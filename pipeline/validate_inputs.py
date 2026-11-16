"""Validate source, estimate, target and evidence provenance."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DEALS = {"HDFC", "AIR_INDIA", "ZOMATO", "MICROSOFT", "KRAFT_HEINZ"}


def main():
    sources = pd.read_csv(ROOT / "data" / "source_register.csv")
    assert set(sources.deal_id) == EXPECTED_DEALS
    assert sources.source_id.is_unique
    assert sources.url.notna().all()
    assert sources.url.astype(str).str.startswith("https://").all()

    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    assumptions = pd.read_csv(ROOT / "model" / "assumptions_register.csv")
    assert set(inputs.deal_id) == EXPECTED_DEALS
    assert inputs.source_or_assumption_id.notna().all()
    assert set(inputs.source_or_assumption_id).issubset(set(assumptions.assumption_id))
    assert set(assumptions.deal_id) == EXPECTED_DEALS
    assert inputs.assumption_type.eq("analyst_assumption").all()

    ledger = pd.read_csv(ROOT / "research" / "evidence_ledger.csv")
    assert set(ledger.source_id).issubset(set(sources.source_id))
    assert ledger.analyst_note.notna().all()
    print(
        f"Validated {len(sources)} sources, {len(assumptions)} assumptions, "
        f"{len(inputs)} model levers and {len(ledger)} evidence claims."
    )


if __name__ == "__main__":
    main()
