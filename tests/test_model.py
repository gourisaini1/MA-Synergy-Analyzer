import pandas as pd
from pathlib import Path

from pipeline.run_model import calculate

ROOT = Path(__file__).resolve().parents[1]


def test_populated_estimates_are_explicit_analyst_assumptions():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    populated = inputs[inputs["baseline_amount"].notna()]
    assert not populated.empty
    assert populated["assumption_type"].eq("analyst_assumption").all()
    assert populated["confidence"].isin(["low", "medium", "high"]).all()
    assert populated["source_or_assumption_id"].notna().all()
    assumption_ids = set(pd.read_csv(ROOT / "model" / "assumptions_register.csv").assumption_id)
    for ids in populated.assumption_ids:
        assert set(ids.split(";")).issubset(assumption_ids)
    assert populated[["overlap_low", "overlap_base", "overlap_high"]].notna().all().all()


def test_estimates_are_separate_from_management_targets():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    assumptions = pd.read_csv(ROOT / "model" / "assumptions_register.csv")
    assert "management_target" in inputs.columns
    assert "assumption_type" in assumptions.columns
    khc = inputs[inputs.deal_id.eq("KRAFT_HEINZ")].iloc[0]
    assert khc.management_target == 1500
    assert khc.benchmark_status == "pre_2015_benchmark"


def test_four_way_classification_is_preserved():
    targets = pd.read_csv(ROOT / "research" / "announced_synergy_targets.csv")
    assert set(targets.deal_id) == {"KRAFT_HEINZ"}
    assert targets.target_value.iloc[0] == 1500
    assert targets.realised_value.iloc[0] == 1700


def test_five_deals_are_represented():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    assert set(inputs.deal_id) == {"HDFC", "AIR_INDIA", "ZOMATO", "MICROSOFT", "KRAFT_HEINZ"}


def test_hdfc_funding_benefit_and_regulatory_drag_are_separate():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    hdfc = inputs[inputs.deal_id.eq("HDFC")]
    assert "Market borrowing to bank deposit funding substitution" in set(hdfc.lever)
    assert "CRR-SLR reserve opportunity-cost drag" in set(hdfc.lever)
    assert "Priority-sector lending compliance cost" in set(hdfc.lever)
    psl = hdfc[hdfc.lever.eq("Priority-sector lending compliance cost")].iloc[0]
    assert psl.baseline_amount == 136810
    assert psl.overlap_base == 0.40
    assert psl.addressable_low == psl.addressable_base == psl.addressable_high == 1
    assert psl.contribution_margin_low == psl.contribution_margin_base == psl.contribution_margin_high == 0.00589
    assert psl.stress_scenario == "high"


def test_negative_synergy_is_signed_and_programme_cost_is_spread():
    row = {
        "deal_id": "HDFC",
        "lever": "reserve drag",
        "baseline_amount": 1000,
        "overlap_low": 0.2,
        "addressable_low": 0.22,
        "achievable_low": 1.0,
        "ramp_low": 0.5,
        "one_off_cost_low": 0,
        "contribution_margin_low": 0.01,
        "direction": "negative",
        "integration_program_years": 1,
        "discount_rate": 0.1,
    }
    gross, first_year, npv, status = calculate(row, "low")
    assert abs(gross + 0.44) < 1e-9
    assert first_year < 0
    assert npv < 0
    assert status == "estimated"


def test_kraft_year_one_deducts_only_one_third_of_programme_cost():
    row = {
        "deal_id": "KRAFT_HEINZ",
        "lever": "test",
        "baseline_amount": 10000,
        "overlap_low": 0.1,
        "addressable_low": 1.0,
        "achievable_low": 1.0,
        "ramp_low": 0.5,
        "one_off_cost_low": 900,
        "contribution_margin_low": 1.0,
        "direction": "positive",
        "integration_program_years": 3,
        "discount_rate": 0.1,
    }
    gross, first_year, npv, status = calculate(row, "low")
    assert gross == 1000
    assert abs(first_year - 200) < 1e-9
    assert npv > first_year
    assert status == "estimated"


def test_hdfc_stress_cases_use_input_columns_and_preserve_totals():
    from pipeline.run_model import HDFC_MATCHED_LEVERS, HDFC_STRESS_CASES, build_stress_rows

    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    hdfc = inputs[inputs.deal_id.eq("HDFC")]
    funding = hdfc[hdfc.lever.eq("Market borrowing to bank deposit funding substitution")].iloc[0]
    reserve = hdfc[hdfc.lever.eq("CRR-SLR reserve opportunity-cost drag")].iloc[0]
    operating = hdfc[hdfc.lever.eq("Legacy standalone operating cost overlap")].iloc[0]
    assert funding.stress_scenario == "low"
    assert reserve.stress_scenario == "high"
    assert operating.stress_scenario == "high"

    results = {}
    core_results = {}
    for case, case_inputs in HDFC_STRESS_CASES.items():
        assert case_inputs["matched_share"] in (0.20, 0.30)
        assert case_inputs["ramp"] in (0.65, 0.80)
        total = 0.0
        core_total = 0.0
        for row in hdfc.itertuples(index=False):
            record = row._asdict()
            stress_rows = build_stress_rows(record)
            for item in stress_rows:
                if item["scenario"] == case:
                    total += item["npv_5yr"]
                    if item["lever"] != "Priority-sector lending compliance cost":
                        core_total += item["npv_5yr"]
        results[case] = total
        core_results[case] = core_total

    assert HDFC_MATCHED_LEVERS == {
        "Market borrowing to bank deposit funding substitution",
        "CRR-SLR reserve opportunity-cost drag",
    }
    # Preserve the PR #3 stress-refactor regression values before PSL is added.
    assert round(core_results["stress_30_80"]) == -352
    assert round(core_results["stress_20_65"]) == -278
    # The high PSL sensitivity is now included in the complete HDFC stress totals.
    assert round(results["stress_30_80"]) == -1055
    assert round(results["stress_20_65"]) == -981
    psl_stress = next(
        item for row in hdfc.itertuples(index=False)
        for item in build_stress_rows(row._asdict())
        if item["lever"] == "Priority-sector lending compliance cost"
        and item["scenario"] == "stress_20_65"
    )
    assert "A-HDFC-18" in psl_stress["assumption_ids"]


def test_kraft_overlap_benchmark_is_not_haircut_twice():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    khc = inputs.query("deal_id == 'KRAFT_HEINZ'").iloc[0]
    assert khc.addressable_low == khc.addressable_base == khc.addressable_high == 1
    assert khc.achievable_low == khc.achievable_base == khc.achievable_high == 1


def test_kraft_overlap_benchmark_exceeds_precedent_range():
    benchmarks = pd.read_csv(ROOT / "research" / "pre2015_synergy_benchmarks.csv")
    khc = pd.read_csv(ROOT / "model" / "synergy_inputs.csv").query("deal_id == 'KRAFT_HEINZ'").iloc[0]
    assert len(benchmarks) == 3
    assert khc.overlap_low == benchmarks["low_ratio"].min()
    assert khc.overlap_base == benchmarks["base_ratio"].median()
    assert khc.overlap_high == benchmarks["high_ratio"].max()
    target_ratio = khc.management_target / khc.baseline_amount
    assert target_ratio > khc.overlap_high


def test_psl_npv_applies_rbi_three_year_phase_in():
    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    psl = inputs.query("deal_id == 'HDFC' and lever == 'Priority-sector lending compliance cost'").iloc[0].to_dict()
    _, _, npv, status = calculate(psl, "base")
    assert status == "estimated"
    assert round(npv, 2) == -468.86

def test_zomato_is_excluded_from_generated_headline_event_study():
    from pipeline.event_study import EVENTS
    assert {event["deal"] for event in EVENTS} == {"HDFC", "KRAFT_HEINZ"}
