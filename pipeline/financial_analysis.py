"""Build deal financial diligence output and parse Microsoft's SEC companyfacts."""
from pathlib import Path
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "financial_due_diligence.csv"
OUT = ROOT / "dashboard" / "financial_due_diligence.csv"
FACTS = ROOT / "data" / "raw" / "microsoft" / "companyfacts.json"
FACTS_OUT = ROOT / "dashboard" / "microsoft_sec_companyfacts.csv"


def extract_companyfacts():
    if not FACTS.exists():
        print("Microsoft SEC companyfacts not downloaded; skipping XBRL supplement.")
        return
    facts = json.loads(FACTS.read_text(encoding="utf-8"))["facts"]["us-gaap"]
    tags = {
        "Revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"],
        "OperatingIncome": ["OperatingIncomeLoss"],
        "SGA": ["SellingGeneralAndAdministrativeExpense"],
        "ResearchAndDevelopment": ["ResearchAndDevelopmentExpense"],
    }
    rows = {}
    for label, alternatives in tags.items():
        tag = next((candidate for candidate in alternatives if candidate in facts), None)
        if tag is None:
            continue
        entries = facts[tag].get("units", {}).get("USD", [])
        for item in entries:
            if item.get("form") != "10-K" or item.get("fp") != "FY":
                continue
            year = int(item.get("fy", 0))
            if not 2015 <= year <= 2026:
                continue
            row = rows.setdefault(year, {"fiscal_year": year})
            if item.get("end", "") >= row.get(f"{label}_end", ""):
                row[label] = item["val"] / 1_000_000
                row[f"{label}_end"] = item.get("end", "")
    frame = pd.DataFrame(rows.values()).sort_values("fiscal_year")
    if "Revenue" in frame and "OperatingIncome" in frame:
        frame["operating_margin_pct"] = frame["OperatingIncome"] / frame["Revenue"] * 100
    if "Revenue" in frame and "SGA" in frame:
        frame["sga_pct_revenue"] = frame["SGA"] / frame["Revenue"] * 100
    if "Revenue" in frame and "ResearchAndDevelopment" in frame:
        frame["rd_pct_revenue"] = frame["ResearchAndDevelopment"] / frame["Revenue"] * 100
    frame.to_csv(FACTS_OUT, index=False)
    print(f"Parsed Microsoft SEC XBRL financial facts to {FACTS_OUT}")


def main():
    data = pd.read_csv(SOURCE)
    data["source_verified"] = data.source_id.notna() & data.source_url.str.startswith("https://")
    data["period_order"] = data.period.str.extract(r"(\d{4})", expand=False).astype(float)
    data["numeric_value"] = pd.to_numeric(data.value, errors="coerce")
    data = data.sort_values(["deal_id", "metric", "period_order"])
    data["prior_period_value"] = data.groupby(["deal_id", "metric"]).numeric_value.shift(1)
    data["change"] = data.numeric_value - data.prior_period_value
    data.to_csv(OUT, index=False)
    extract_companyfacts()
    print(f"Wrote {len(data)} financial diligence observations to {OUT}")


if __name__ == "__main__":
    main()
