"""Build traceable evidence, financial diligence and synergy target back-test outputs."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "research" / "quantitative_backtest.csv"
OUT = ROOT / "dashboard" / "deal_evidence_backtest.csv"
SUMMARY = ROOT / "output" / "executive_deck" / "evidence_backtest_summary.md"


def main():
    evidence = pd.read_csv(INPUT)
    required = {
        "deal_id", "metric", "period", "value", "unit", "source_id",
        "classification", "synergy_relevance", "attribution_caveat",
    }
    missing = required - set(evidence.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if evidence[list(required)].isna().any().any():
        raise ValueError("Back-test rows require complete source and caveat fields")
    register = pd.read_csv(ROOT / "data" / "source_register.csv")
    unknown = set(evidence.source_id) - set(register.source_id)
    if unknown:
        raise ValueError(f"Evidence references unknown source IDs: {sorted(unknown)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    evidence.to_csv(OUT, index=False)

    targets = pd.read_csv(ROOT / "research" / "announced_synergy_targets.csv")
    lines = [
        "# Evidence back-test",
        "",
        "The project maintains four distinct buckets: management-announced, independently estimated, management-reported realised, and unverified.",
        "",
        "## Announced target vs estimate vs reported realisation",
        "",
        "| Deal | Announced annual run-rate | Independent scenario range | Reported realisation | Basis caveat |",
        "|---|---:|---:|---:|---|",
    ]
    for target in targets.itertuples(index=False):
        model_rows = pd.read_csv(ROOT / "dashboard" / "tableau_synergy_data.csv")
        estimates = model_rows[
            (model_rows.deal_id == target.deal_id)
            & (model_rows.evidence_status == "estimated")
        ]
        low = estimates.loc[estimates.scenario.eq("low"), "gross_run_rate"].sum()
        high = estimates.loc[estimates.scenario.eq("high"), "gross_run_rate"].sum()
        lines.append(
            f"| {target.deal_id} | {target.currency} {target.target_value:,.0f}m | "
            f"{target.currency} {low:,.0f}m–{high:,.0f}m | "
            f"{target.currency} {target.realised_value:,.0f}m cumulative | {target.caveat} |"
        )
    lines += ["", "## Evidence by deal", ""]
    for deal, group in evidence.groupby("deal_id", sort=False):
        lines += [f"### {deal}", ""]
        for item in group.itertuples(index=False):
            lines.append(
                f"- **{item.metric} ({item.period}):** {item.value} {item.unit} "
                f"({item.classification}). {item.attribution_caveat}"
            )
        lines.append("")
    lines += [
        "## Interpretation",
        "",
        "- Kraft Heinz is the public target/realisation back-test: announced annual run-rate and reported cumulative savings are deliberately not treated as identical measures.",
        "- HDFC's scenario is an outside-in cost-overlap estimate, not a management synergy target; the reported cost-to-income ratio is an outcome metric, not causal attribution.",
        "- Air India–Vistara remains qualitative because public contract counts and system migrations do not supply spend baselines or counterfactuals.",
        "- Blinkit and LinkedIn segment financials are acquired-business performance; they are not labelled merger synergies.",
        "- Every estimate is tagged with assumption type and confidence; unverified levers remain null.",
    ]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(evidence)} evidence observations and the synergy back-test.")


if __name__ == "__main__":
    main()
