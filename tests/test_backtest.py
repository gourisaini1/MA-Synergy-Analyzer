import pandas as pd
from pathlib import Path


def test_quantitative_backtest_sources_and_deals():
    root = Path(__file__).resolve().parents[1]
    evidence = pd.read_csv(root / "research" / "quantitative_backtest.csv")
    sources = pd.read_csv(root / "data" / "source_register.csv")
    assert set(evidence.deal_id) == {
        "HDFC", "AIR_INDIA", "ZOMATO", "MICROSOFT", "KRAFT_HEINZ"
    }
    assert evidence.source_id.notna().all()
    assert set(evidence.source_id).issubset(set(sources.source_id))
    assert evidence.attribution_caveat.notna().all()
