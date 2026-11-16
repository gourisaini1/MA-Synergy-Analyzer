"""Calculate directional synergy scenarios, first-year net and five-year NPV."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "model" / "synergy_inputs.csv"
OUT = ROOT / "dashboard" / "tableau_synergy_data.csv"
SCENARIOS = ("low", "base", "high")


def calculate(row, scenario):
    names = {
        "baseline": "baseline_amount",
        "overlap": f"overlap_{scenario}",
        "addressable": f"addressable_{scenario}",
        "achievable": f"achievable_{scenario}",
        "ramp": f"ramp_{scenario}",
        "one_off": f"one_off_cost_{scenario}",
        "margin": f"contribution_margin_{scenario}",
    }
    values = {
        key: pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
        for key, column in names.items()
    }
    if any(pd.isna(value) for value in values.values()):
        return None, None, None, "unverified"
    if values["baseline"] < 0 or values["one_off"] < 0:
        raise ValueError(f"{row['deal_id']}/{row['lever']}: baseline and programme cost must be non-negative")
    for key in ("overlap", "addressable", "achievable", "ramp"):
        if not 0 <= values[key] <= 1:
            raise ValueError(f"{row['deal_id']}/{row['lever']}: {key} must be between zero and one")
    if values["margin"] < 0 or values["margin"] > 1:
        raise ValueError(f"{row['deal_id']}/{row['lever']}: unit economics factor must be between zero and one")

    direction = -1 if row.get("direction", "positive") == "negative" else 1
    gross = (
        values["baseline"] * values["overlap"] * values["addressable"]
        * values["achievable"] * values["margin"] * direction
    )
    program_years = max(1, int(row.get("integration_program_years", 1) or 1))
    discount_rate = float(row.get("discount_rate", 0.10) or 0.10)
    annual_program_cost = values["one_off"] / program_years
    first_year_net = gross * values["ramp"] - annual_program_cost

    npv_5yr = 0.0
    for year in range(1, 6):
        year_ramp = min(1.0, values["ramp"] + 0.20 * (year - 1))
        program_cost = annual_program_cost if year <= program_years else 0.0
        net_cash_flow = gross * year_ramp - program_cost
        npv_5yr += net_cash_flow / ((1 + discount_rate) ** year)
    return gross, first_year_net, npv_5yr, "estimated"


def main():
    frame = pd.read_csv(INPUT)
    rows = []
    for row in frame.itertuples(index=False):
        record = row._asdict()
        for scenario in SCENARIOS:
            gross, net, npv, status = calculate(record, scenario)
            rows.append({
                "deal_id": row.deal_id,
                "lever": row.lever,
                "synergy_type": row.synergy_type,
                "scenario": scenario,
                "currency": row.currency,
                "gross_run_rate": gross,
                "net_first_year": net,
                "npv_5yr": npv,
                "direction": getattr(row, "direction", "positive"),
                "source_or_assumption_id": row.source_or_assumption_id,
                "assumption_ids": getattr(row, "assumption_ids", ""),
                "classification": getattr(row, "assumption_type", "analyst_assumption"),
                "confidence": getattr(row, "confidence", "low"),
                "management_target": getattr(row, "management_target", None),
                "benchmark_status": getattr(row, "benchmark_status", "not_benchmarked"),
                "evidence_status": status,
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    estimated = sum(row["evidence_status"] == "estimated" for row in rows)
    print(f"Wrote {len(rows)} scenarios: {estimated} estimated, {len(rows) - estimated} unverified.")


if __name__ == "__main__":
    main()
