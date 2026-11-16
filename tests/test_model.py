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
    assert khc.benchmark_status == "ex_post_sensitivity_not_benchmark"


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
    assert pd.isna(psl.baseline_amount)


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
