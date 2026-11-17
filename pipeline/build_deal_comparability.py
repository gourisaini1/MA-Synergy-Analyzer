"""Build a four-deal comparable synergy evidence scorecard.

The scorecard deliberately preserves missing values. A missing target or reported
realisation is not zero, and a partial scenario is never presented as a complete
deal estimate.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "deal_universe.json"
MODEL = ROOT / "dashboard" / "tableau_synergy_data.csv"
TARGETS = ROOT / "research" / "announced_synergy_targets.csv"
OUT = ROOT / "dashboard" / "deal_comparability.csv"

REQUIRED_FIELDS = [
    "deal_id", "deal_name", "case_role", "sector", "completion_date",
    "estimate_status", "estimate_low", "estimate_base", "estimate_high",
    "currency", "announced_target", "target_basis", "reported_realisation",
    "realisation_basis", "key_synergy_lever", "evidence_quality",
    "unquantified_items", "interpretation",
]


def main():
    deals = json.loads(CONFIG.read_text(encoding="utf-8"))["deals"]
    core = [deal for deal in deals if deal.get("core_case", False)]
    if len(core) != 4:
        raise ValueError(f"Expected exactly four core deals, found {len(core)}")

    model = pd.read_csv(MODEL)
    targets = pd.read_csv(TARGETS)
    records = []
    for deal in core:
        deal_id = deal["deal_id"]
        rows = model[model.deal_id.eq(deal_id)]
        estimated = rows[rows.evidence_status.eq("estimated")]
        unverified = rows[rows.evidence_status.ne("estimated")]
        currency_values = rows.currency.dropna().unique().tolist()
        currency = currency_values[0] if len(currency_values) == 1 else deal.get("currency", "")
        values = {}
        for scenario in ("low", "base", "high"):
            scenario_rows = estimated[estimated.scenario.eq(scenario)]
            values[scenario] = (
                round(float(scenario_rows.gross_run_rate.sum()), 2)
                if not scenario_rows.empty else None
            )

        if estimated.empty:
            estimate_status = "not_quantified"
        elif not unverified.empty:
            estimate_status = "partial_estimate"
        else:
            estimate_status = "modelled"

        target_rows = targets[targets.deal_id.eq(deal_id)]
        if target_rows.empty:
            announced_target = None
            target_basis = "No quantified synergy target identified in reviewed public sources"
            reported_realisation = None
            realisation_basis = "No quantified attributable synergy realisation identified"
        else:
            target = target_rows.iloc[0]
            announced_target = f"{target.currency} {target.target_value:g}"
            target_basis = f"{target.target_type}; {target.target_timing}; management target"
            reported_realisation = (
                f"{target.currency} {target.realised_value:g} cumulative"
                if pd.notna(target.realised_value) else None
            )
            realisation_basis = str(target.caveat)

        records.append({
            "deal_id": deal_id,
            "deal_name": deal["name"],
            "case_role": "core",
            "sector": deal["sector"],
            "completion_date": deal.get("completion_date", ""),
            "estimate_status": estimate_status,
            "estimate_low": values["low"],
            "estimate_base": values["base"],
            "estimate_high": values["high"],
            "currency": currency,
            "announced_target": announced_target,
            "target_basis": target_basis,
            "reported_realisation": reported_realisation,
            "realisation_basis": realisation_basis,
            "key_synergy_lever": deal.get("key_synergy_lever", ""),
            "evidence_quality": deal.get("evidence_quality", ""),
            "unquantified_items": deal.get("unquantified_items", ""),
            "interpretation": deal.get("interpretation", ""),
        })

    frame = pd.DataFrame(records, columns=REQUIRED_FIELDS)
    if frame.deal_id.duplicated().any():
        raise ValueError("Core deal scorecard contains duplicate deal IDs")
    if frame[["deal_id", "deal_name", "case_role", "estimate_status"]].isna().any().any():
        raise ValueError("Scorecard is missing required deal identifiers or status")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    print(f"Wrote comparable evidence scorecard for {len(frame)} core deals.")


if __name__ == "__main__":
    main()
