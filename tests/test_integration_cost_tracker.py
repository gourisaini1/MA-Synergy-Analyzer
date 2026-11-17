import pandas as pd


def test_integration_cost_tracker_preserves_undisclosed_costs():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    costs = pd.read_csv(root / "research" / "integration_cost_tracker.csv")
    sources = pd.read_csv(root / "data" / "source_register.csv")

    assert set(costs.deal_id) == {"HDFC", "AIR_INDIA", "ZOMATO", "KRAFT_HEINZ"}
    assert set(costs.source_id).issubset(set(sources.source_id))
    for deal in ("HDFC", "AIR_INDIA", "ZOMATO"):
        rows = costs[costs.deal_id.eq(deal)]
        assert rows.reported_cost_value.isna().all()
        assert rows.status.eq("not_disclosed").all()

    khc = costs[costs.deal_id.eq("KRAFT_HEINZ")]
    assert khc.reported_cost_value.sum() == 2055
    assert set(khc.reported_cost_value) == {339, 829, 887}
