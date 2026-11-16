import pandas as pd
from pathlib import Path


def test_five_deals_and_https_sources():
    root = Path(__file__).resolve().parents[1]
    df = pd.read_csv(root / "data" / "source_register.csv")
    assert set(df.deal_id.unique()) == {
        "HDFC", "AIR_INDIA", "ZOMATO", "MICROSOFT", "KRAFT_HEINZ"
    }
    assert df.url.notna().all()
    assert df.url.str.startswith("https://").all()
    assert df.source_id.is_unique
