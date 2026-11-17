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


def test_event_study_does_not_shift_missing_event_date_to_next_session():
    dates = pd.bdate_range("2021-09-01", "2022-07-31")
    tickers = ["HDFCBANK.NS", "HDFC.NS", "^NSEI", "ZOMATO.NS"]
    rng = np.random.default_rng(23)
    frame = pd.DataFrame(index=dates)
    for ticker in tickers:
        frame[ticker] = 100 * (1 + pd.Series(
            rng.normal(0.0002, 0.01, len(dates)), index=dates
        )).cumprod()
    frame = frame.drop(pd.Timestamp("2022-04-04"))
    rows = event_rows(frame)
    hdfc_rows = [r for r in rows if r["deal"] == "HDFC"]
    assert hdfc_rows
    assert all(r["status"] == "exact event-session return unavailable" for r in hdfc_rows)


def test_event_study_rejects_incomplete_event_windows():
    dates = pd.bdate_range("2021-09-01", "2022-07-31")
    rng = np.random.default_rng(29)
    frame = pd.DataFrame(index=dates)
    for ticker in ["HDFCBANK.NS", "HDFC.NS", "^NSEI", "ZOMATO.NS"]:
        frame[ticker] = 100 * (1 + pd.Series(
            rng.normal(0.0002, 0.01, len(dates)), index=dates
        )).cumprod()
    frame = frame.drop(pd.Timestamp("2022-04-05"))
    rows = event_rows(frame)
    hdfc_bank = [r for r in rows if r["deal"] == "HDFC" and r["security"] == "HDFC Bank (acquirer)"]
    short = [r for r in hdfc_bank if r.get("status") == "incomplete event window"]
    assert short
    assert all(r["observations_available"] < r["observations_required"] for r in short)
