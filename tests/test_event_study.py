import numpy as np
import pandas as pd

from pipeline.event_study import event_rows, _parse_nse_bhavcopy


def test_event_study_computes_acquirer_and_public_target_t_statistics():
    dates = pd.bdate_range("2021-09-01", "2022-07-31")
    tickers = ["HDFCBANK.NS", "HDFC.NS", "^NSEI", "ZOMATO.NS"]
    rng = np.random.default_rng(17)
    frame = pd.DataFrame(index=dates)
    for index, ticker in enumerate(tickers):
        daily_returns = rng.normal(0.0003 + index * 0.00002, 0.01, len(dates))
        frame[ticker] = 100 * (1 + pd.Series(daily_returns, index=dates)).cumprod()
    rows = event_rows(frame)
    calculated = [row for row in rows if row.get("status") == "calculated"]
    assert calculated
    assert all(row["car_t_stat"] is not None for row in calculated)
    assert any(row["security"] == "HDFC Ltd (target)" for row in calculated)
    assert not any(row.get("security") == "Blinkit (target)" for row in rows)

def test_nse_bhavcopy_parser_extracts_listed_target_and_acquirer_prices():
    payload = (
        "SYMBOL,SERIES,DATE1,CLOSE_PRICE\n"
        "HDFC,EQ,04-Apr-2022,2500.50\n"
        "HDFCBANK,EQ,04-Apr-2022,1600.25\n"
        "ZOMATO,EQ,04-Apr-2022,70.10\n"
        "OTHER,BE,04-Apr-2022,10.00\n"
    ).encode("utf-8")
    rows = _parse_nse_bhavcopy(payload, pd.Timestamp("2022-04-04"))
    assert {row["ticker"] for row in rows} == {"HDFC.NS", "HDFCBANK.NS", "ZOMATO.NS"}
    assert all(row["price_source"].startswith("NSE official") for row in rows)


def test_price_panel_does_not_mix_adjusted_and_unadjusted_sources():
    from pipeline.event_study import _price_panel

    cached = pd.DataFrame([
        {"date": "2022-04-01", "ticker": "HDFCBANK.NS", "price": 100.0,
         "price_source": "Yahoo Finance auto-adjusted close"},
        {"date": "2022-04-01", "ticker": "HDFCBANK.NS", "price": 101.0,
         "price_source": "NSE official bhavcopy close (unadjusted)"},
        {"date": "2022-04-04", "ticker": "HDFCBANK.NS", "price": 102.0,
         "price_source": "Yahoo Finance auto-adjusted close"},
    ])
    prices = _price_panel(cached)
    assert prices.loc[pd.Timestamp("2022-04-01"), "HDFCBANK.NS"] == 100.0
    assert prices.attrs["price_sources"]["HDFCBANK.NS"] == "Yahoo Finance auto-adjusted close"
