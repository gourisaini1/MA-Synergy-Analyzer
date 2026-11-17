import json

import pandas as pd

from pipeline import build_deal_comparability as scorecard


def test_scorecard_preserves_unverified_deals_and_target_basis(tmp_path, monkeypatch):
    config = {
        "deals": [
            {"deal_id": "HDFC", "name": "HDFC Ltd–HDFC Bank", "sector": "Financial services",
             "completion_date": "2023-07-01", "core_case": True, "currency": "INR crore",
             "key_synergy_lever": "Funding", "evidence_quality": "Medium",
             "unquantified_items": "PSL", "interpretation": "Partial only"},
            {"deal_id": "AIR_INDIA", "name": "Air India–Vistara", "sector": "Airlines",
             "completion_date": "2024-11-12", "core_case": True, "currency": "INR crore",
             "key_synergy_lever": "Procurement", "evidence_quality": "Low",
             "unquantified_items": "Vendor spend", "interpretation": "Milestones are not savings"},
            {"deal_id": "ZOMATO", "name": "Zomato–Blinkit", "sector": "Consumer internet",
             "completion_date": "2022-08", "core_case": True, "currency": "INR crore",
             "key_synergy_lever": "Delivery", "evidence_quality": "Low",
             "unquantified_items": "Cohorts", "interpretation": "Segment growth is not synergy"},
            {"deal_id": "KRAFT_HEINZ", "name": "Kraft Foods–H.J. Heinz", "sector": "CPG",
             "completion_date": "2015-07", "core_case": True, "currency": "USD million",
             "key_synergy_lever": "Procurement", "evidence_quality": "High",
             "unquantified_items": "Recurring bridge", "interpretation": "Ex-post sensitivity"},
            {"deal_id": "MICROSOFT", "name": "Microsoft–LinkedIn", "sector": "Technology",
             "completion_date": "2016-12-08", "core_case": False},
        ]
    }
    model_rows = [
        {"deal_id": "HDFC", "scenario": s, "gross_run_rate": v,
         "evidence_status": "estimated", "currency": "INR crore"}
        for s, v in [("low", 8), ("base", 86), ("high", 302)]
    ]
    model_rows += [
        {"deal_id": "HDFC", "scenario": s, "gross_run_rate": None,
         "evidence_status": "unverified", "currency": "INR crore"}
        for s in ("low", "base", "high")
    ]
    model_rows += [
        {"deal_id": "KRAFT_HEINZ", "scenario": s, "gross_run_rate": v,
         "evidence_status": "estimated", "currency": "USD million"}
        for s, v in [("low", 710), ("base", 1400), ("high", 2040)]
    ]
    pd.DataFrame(model_rows).to_csv(tmp_path / "model.csv", index=False)
    pd.DataFrame([{
        "deal_id": "KRAFT_HEINZ", "currency": "USD million",
        "target_value": 1500, "target_type": "annual_run_rate",
        "target_timing": "2017", "realised_value": 1700,
        "caveat": "Cumulative savings; not directly comparable",
    }]).to_csv(tmp_path / "targets.csv", index=False)
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    monkeypatch.setattr(scorecard, "CONFIG", tmp_path / "config.json")
    monkeypatch.setattr(scorecard, "MODEL", tmp_path / "model.csv")
    monkeypatch.setattr(scorecard, "TARGETS", tmp_path / "targets.csv")
    monkeypatch.setattr(scorecard, "OUT", tmp_path / "scorecard.csv")

    scorecard.main()
    result = pd.read_csv(tmp_path / "scorecard.csv")

    assert set(result.deal_id) == {"HDFC", "AIR_INDIA", "ZOMATO", "KRAFT_HEINZ"}
    assert "MICROSOFT" not in set(result.deal_id)
    assert result.loc[result.deal_id.eq("HDFC"), "estimate_status"].item() == "partial_estimate"
    assert result.loc[result.deal_id.eq("HDFC"), "estimate_base"].item() == 86
    assert pd.isna(result.loc[result.deal_id.eq("AIR_INDIA"), "estimate_base"].item())
    assert pd.isna(result.loc[result.deal_id.eq("ZOMATO"), "announced_target"].item())
    khc = result[result.deal_id.eq("KRAFT_HEINZ")].iloc[0]
    assert khc.announced_target == "USD million 1500"
    assert "cumulative" in khc.reported_realisation
    assert "not directly comparable" in khc.realisation_basis
