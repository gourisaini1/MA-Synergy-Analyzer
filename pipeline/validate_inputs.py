"""Validate source, estimate, target and evidence provenance."""
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DEALS = {"HDFC", "AIR_INDIA", "ZOMATO", "MICROSOFT", "KRAFT_HEINZ"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    sources = pd.read_csv(ROOT / "data" / "source_register.csv")
    require(set(sources.deal_id) == EXPECTED_DEALS, "Source register deal coverage is incomplete.")
    require(sources.source_id.notna().all() and sources.source_id.is_unique,
            "Source IDs must be present and unique.")
    require(sources.url.notna().all(), "Every source must have a URL.")
    invalid_urls = [
        value for value in sources.url.astype(str)
        if urlparse(value).scheme != "https" or not urlparse(value).netloc
    ]
    require(not invalid_urls, f"Source URLs must be absolute HTTPS URLs: {invalid_urls[:3]}")

    inputs = pd.read_csv(ROOT / "model" / "synergy_inputs.csv")
    assumptions = pd.read_csv(ROOT / "model" / "assumptions_register.csv")
    require(set(inputs.deal_id) == EXPECTED_DEALS, "Model deal coverage is incomplete.")
    require(inputs.source_or_assumption_id.notna().all(),
            "Every model lever must cite a source or assumption ID.")
    require(set(inputs.source_or_assumption_id).issubset(set(assumptions.assumption_id)),
            "Model inputs reference an unknown assumption ID.")
    require(set(assumptions.deal_id) == EXPECTED_DEALS, "Assumption register deal coverage is incomplete.")
    require(assumptions.assumption_id.notna().all() and assumptions.assumption_id.is_unique,
            "Assumption IDs must be present and unique.")
    require(inputs.assumption_type.eq("analyst_assumption").all(),
            "Model estimates must be labelled as analyst assumptions.")

    ledger = pd.read_csv(ROOT / "research" / "evidence_ledger.csv")
    require(set(ledger.source_id).issubset(set(sources.source_id)),
            "Evidence ledger references a source missing from the source register.")
    require(ledger.analyst_note.notna().all(), "Every evidence item must include an attribution caveat.")

    targets = pd.read_csv(ROOT / "research" / "announced_synergy_targets.csv")
    require(targets.deal_id.is_unique, "Announced synergy target deal IDs must be unique.")
    require(targets[["deal_id", "source_id", "target_type", "target_value", "caveat"]].notna().all().all(),
            "Announced targets require source, type, value and caveat fields.")
    require(set(targets.source_id).issubset(set(sources.source_id)),
            "Announced targets reference unknown sources.")
    require(targets.target_value.ge(0).all(),
            "Announced synergy target values must be non-negative.")

    print(
        f"Validated {len(sources)} sources, {len(assumptions)} assumptions, "
        f"{len(inputs)} model levers, {len(ledger)} evidence claims and "
        f"{len(targets)} announced targets."
    )


if __name__ == "__main__":
    main()
