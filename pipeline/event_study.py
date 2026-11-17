"""Multi-deal market-model event study with cached Yahoo/NSE price sources.

Listed targets are included where exchange price history is available. Heinz was
private at announcement; Kraft Foods Group was the listed target but its delisted
KRFT history is unavailable from Yahoo's current feed.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import os
from pathlib import Path
import zipfile

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "market_prices.csv"
OUT = ROOT / "dashboard" / "event_study_results.csv"

EVENTS = [
    {
        "deal": "KRAFT_HEINZ",
        "announcement_date": "2015-03-25",
        "event_date": "2015-03-25",
        "event": "Kraft-Heinz merger announcement",
        "securities": {"Kraft Foods Group (listed target)": ["KRFT"]},
        "benchmark": "^GSPC",
        "target_status": "Heinz was privately held acquirer; Kraft Foods Group was the listed target",
    },
    {
        "deal": "HDFC",
        "announcement_date": "2022-04-04",
        "event_date": "2022-04-04",
        "event": "HDFC Ltd-HDFC Bank merger announcement",
        "securities": {
            "HDFC Bank (acquirer)": ["HDFCBANK.NS", "HDFCBANK.BO"],
            "HDFC Ltd (target)": ["HDFC.NS", "HDFC.BO"],
        },
        "benchmark": "^NSEI",
        "target_status": "Both acquirer and target publicly traded",
    },
    {
        "deal": "ZOMATO",
        "announcement_date": "2022-06-24",
        "event_date": "2022-06-27",
        "event": "Zomato board approval of Blinkit acquisition (next session)",
        "securities": {"Zomato (acquirer)": ["ETERNAL.NS", "ZOMATO.NS", "ETERNAL.BO", "ZOMATO.BO"]},
        "benchmark": "^NSEI",
        "target_status": "Blinkit was privately held target; no listed target return",
    },
]

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Accept": "text/csv,application/zip,application/octet-stream,*/*",
    "Referer": "https://www.nseindia.com/",
}
NSE_SYMBOLS = {
    "HDFC.NS": "HDFC",
    "HDFCBANK.NS": "HDFCBANK",
    "ZOMATO.NS": "ZOMATO",
}


def _extract_close(downloaded):
    if downloaded.empty:
        return None
    if isinstance(downloaded.columns, pd.MultiIndex):
        for level in range(downloaded.columns.nlevels):
            if "Close" in downloaded.columns.get_level_values(level):
                series = downloaded.xs("Close", axis=1, level=level)
                if isinstance(series, pd.DataFrame):
                    series = series.iloc[:, 0]
                return series
        return None
    if "Close" in downloaded:
        return downloaded["Close"]
    return None


def _parse_nse_bhavcopy(content, trading_date):
    payload = BytesIO(content)
    if zipfile.is_zipfile(payload):
        payload.seek(0)
        with zipfile.ZipFile(payload) as archive:
            csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
            frame = pd.read_csv(archive.open(csv_name))
    else:
        payload.seek(0)
        frame = pd.read_csv(payload)
    frame.columns = [str(column).strip().upper() for column in frame.columns]
    symbol_col = "SYMBOL" if "SYMBOL" in frame else None
    series_col = "SERIES" if "SERIES" in frame else None
    close_col = "CLOSE_PRICE" if "CLOSE_PRICE" in frame else "CLOSE"
    if symbol_col is None or close_col not in frame:
        return []
    if series_col:
        frame = frame[frame[series_col].astype(str).str.upper().eq("EQ")]
    frame[symbol_col] = frame[symbol_col].astype(str).str.upper().str.strip()
    frame[close_col] = pd.to_numeric(frame[close_col], errors="coerce")
    wanted = set(NSE_SYMBOLS.values())
    frame = frame[frame[symbol_col].isin(wanted)].dropna(subset=[close_col])
    rows = []
    for record in frame.itertuples(index=False, name=None):
        values = dict(zip(frame.columns, record))
        symbol = values[symbol_col]
        ticker = next(key for key, value in NSE_SYMBOLS.items() if value == symbol)
        rows.append({
            "date": pd.Timestamp(trading_date),
            "ticker": ticker,
            "price": float(values[close_col]),
            "price_source": "NSE official bhavcopy close (unadjusted)",
        })
    return rows


def _fetch_nse_day(day):
    date_code = day.strftime("%d%m%Y")
    url = f"https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_{date_code}.csv"
    try:
        response = requests.get(url, headers=NSE_HEADERS, timeout=15)
        if response.status_code == 200 and b"SYMBOL" in response.content[:1000].upper():
            return _parse_nse_bhavcopy(response.content, day)
    except requests.RequestException:
        pass

    # Older daily PR zip archive is a fallback for the same session.
    url = (
        "https://nsearchives.nseindia.com/content/historical/EQUITIES/"
        f"{day.year}/{day.strftime('%b').upper()}/PR{day.strftime('%d%m%y')}.zip"
    )
    try:
        response = requests.get(url, headers=NSE_HEADERS, timeout=15)
        if response.status_code == 200:
            return _parse_nse_bhavcopy(response.content, day)
    except requests.RequestException:
        pass
    return []


def load_prices():
    if CACHE.exists() and os.getenv("REFRESH_MARKET_DATA") != "1":
        cached = pd.read_csv(CACHE, parse_dates=["date"])
        if "adjusted_close" in cached and "price" not in cached:
            cached = cached.rename(columns={"adjusted_close": "price"})
        required = {"date", "ticker", "price"}
        if not required.issubset(cached.columns):
            raise ValueError(f"Market price cache must contain {sorted(required)}")
        return cached.pivot(index="date", columns="ticker", values="price").sort_index()

    tickers = sorted({
        ticker
        for event in EVENTS
        for ticker in [
            event["benchmark"],
            *(option for options in event["securities"].values() for option in options),
        ]
    })
    start = pd.Timestamp("2014-07-01")
    end = pd.Timestamp("2022-08-01")
    fresh_rows = []

    for ticker in tickers:
        try:
            downloaded = yf.download(
                ticker,
                start=start.date(),
                end=end.date(),
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            close = _extract_close(downloaded)
            if close is not None and not close.dropna().empty:
                fresh_rows.extend([
                    {
                        "date": pd.Timestamp(date).tz_localize(None),
                        "ticker": ticker,
                        "price": float(value),
                        "price_source": "Yahoo Finance auto-adjusted close",
                    }
                    for date, value in close.dropna().items()
                ])
        except Exception as error:
            print(f"Yahoo price download failed for {ticker}: {error}")

    # Yahoo no longer serves several delisted/renamed Indian tickers. Fill those
    # series from the official NSE daily bhavcopy archive.
    cached_tickers = {row["ticker"] for row in fresh_rows}
    if CACHE.exists():
        try:
            existing_cache = pd.read_csv(CACHE, usecols=["ticker"])
            cached_tickers.update(existing_cache["ticker"].dropna().astype(str).unique())
        except (ValueError, OSError):
            pass
    nse_missing = {
        ticker for ticker in NSE_SYMBOLS
        if ticker not in cached_tickers
    }
    if nse_missing:
        trading_days = pd.bdate_range("2021-09-01", "2022-07-31")
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_fetch_nse_day, day): day for day in trading_days}
            for future in as_completed(futures):
                try:
                    day_rows = future.result()
                    fresh_rows.extend(
                        row for row in day_rows if row["ticker"] in nse_missing
                    )
                except Exception as error:
                    print(f"NSE bhavcopy retrieval failed for {futures[future].date()}: {error}")

    if fresh_rows:
        fresh = pd.DataFrame(fresh_rows)
        if CACHE.exists():
            prior = pd.read_csv(CACHE, parse_dates=["date"])
            if "adjusted_close" in prior and "price" not in prior:
                prior = prior.rename(columns={"adjusted_close": "price"})
            if "price_source" not in prior:
                prior["price_source"] = "Legacy cached price; provider not tagged"
            fresh = pd.concat([prior, fresh], ignore_index=True)
        fresh = fresh.drop_duplicates(["date", "ticker"], keep="last")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        fresh.sort_values(["ticker", "date"]).to_csv(CACHE, index=False)

    if not CACHE.exists():
        raise FileNotFoundError(
            "No downloadable prices and no committed data/market_prices.csv cache."
        )
    cached = pd.read_csv(CACHE, parse_dates=["date"])
    if "adjusted_close" in cached and "price" not in cached:
        cached = cached.rename(columns={"adjusted_close": "price"})
    required = {"date", "ticker", "price"}
    if not required.issubset(cached.columns):
        raise ValueError(f"Market price cache must contain {sorted(required)}")
    if "price_source" not in cached.columns:
        cached["price_source"] = "Legacy cached price; provider not tagged"

    # Select exactly one provider/adjustment convention per ticker. This avoids
    # calculating returns across Yahoo dividend-adjusted closes and NSE raw closes.
    source_priority = {
        "Yahoo Finance auto-adjusted close": 0,
        "NSE official bhavcopy close (unadjusted)": 1,
        "Legacy cached price; provider not tagged": 2,
    }
    selected_sources = {}
    for ticker, group in cached.groupby("ticker"):
        sources = group["price_source"].dropna().astype(str).unique().tolist()
        selected_sources[ticker] = min(
            sources, key=lambda source: source_priority.get(source, 99)
        )
    cached = cached[
        cached.apply(
            lambda row: row["price_source"] == selected_sources.get(row["ticker"]),
            axis=1,
        )
    ].copy()
    prices = cached.pivot(index="date", columns="ticker", values="price").sort_index()
    prices.attrs["price_sources"] = selected_sources
    return prices


def event_rows(prices):
    rows = []
    for event in EVENTS:
        event_date = pd.Timestamp(event["event_date"])
        for security_label, ticker_options in event["securities"].items():
            benchmark = event["benchmark"]
            ticker = next(
                (option for option in ticker_options if option in prices.columns),
                ticker_options[0],
            )
            if ticker not in prices or benchmark not in prices:
                reference = ""
                if event["deal"] == "HDFC" and "HDFC Ltd" in security_label:
                    reference = "SEBI reports +9.29% close-to-close on announcement day; raw return, not CAR."
                elif event["deal"] == "KRAFT_HEINZ":
                    reference = "SEC S-4 reports USD 61.33 on 24 Mar and USD 89.40 on 9 Apr (+45.8% cumulative); not event-window CAR."
                rows.append({
                    "deal": event["deal"],
                    "event": event["event"],
                    "security": security_label,
                    "ticker": ticker,
                    "status": "daily price series unavailable from current feed",
                    "price_source": prices.attrs.get("price_sources", {}).get(ticker, "unavailable"),
                    "reference_reaction": reference,
                    "target_status": event["target_status"],
                })
                continue

            close = prices[[ticker, benchmark]].dropna()
            returns = close.pct_change().dropna()
            returns.index = pd.to_datetime(returns.index).tz_localize(None)
            event_positions = [i for i, date in enumerate(returns.index) if date >= event_date]
            if not event_positions:
                rows.append({
                    "deal": event["deal"],
                    "event": event["event"],
                    "security": security_label,
                    "ticker": ticker,
                    "status": "event date outside cached price range",
                    "price_source": prices.attrs.get("price_sources", {}).get(ticker, "unavailable"),
                    "target_status": event["target_status"],
                })
                continue
            event_pos = event_positions[0]
            estimation = returns.iloc[max(0, event_pos - 120):max(0, event_pos - 20)]
            if len(estimation) < 60:
                rows.append({
                    "deal": event["deal"],
                    "event": event["event"],
                    "security": security_label,
                    "ticker": ticker,
                    "status": "insufficient estimation-window observations",
                    "price_source": prices.attrs.get("price_sources", {}).get(ticker, "unavailable"),
                    "target_status": event["target_status"],
                })
                continue

            market = estimation[benchmark]
            variance = market.var(ddof=1)
            if not variance or pd.isna(variance):
                continue
            beta = estimation[ticker].cov(market) / variance
            alpha = estimation[ticker].mean() - beta * market.mean()
            residual = estimation[ticker] - (alpha + beta * market)
            sigma2 = float((residual ** 2).sum() / (len(estimation) - 2))
            returns = returns.copy()
            returns["abnormal"] = returns[ticker] - (alpha + beta * returns[benchmark])
            returns["event_day"] = range(len(returns))
            returns["event_day"] = returns["event_day"] - event_pos

            for window, low, high in [("[-1,+1]", -1, 1), ("[-2,+2]", -2, 2), ("[-5,+5]", -5, 5)]:
                sample = returns[returns.event_day.between(low, high)]
                n = len(sample)
                if n == 0:
                    continue
                car = float(sample.abnormal.sum())
                market_sum_deviation = float(
                    (sample[benchmark] - market.mean()).sum()
                )
                sxx = float(((market - market.mean()) ** 2).sum())
                prediction_variance = sigma2 * (
                    n + (n ** 2 / len(estimation))
                    + (market_sum_deviation ** 2 / max(sxx, 1e-12))
                )
                standard_error = prediction_variance ** 0.5
                rows.append({
                    "deal": event["deal"],
                    "announcement_date": event["announcement_date"],
                    "event_date_used": returns.index[event_pos].date().isoformat(),
                    "event": event["event"],
                    "security": security_label,
                    "ticker": ticker,
                    "benchmark": benchmark,
                    "window": window,
                    "security_cumulative_return_pct": ((1 + sample[ticker]).prod() - 1) * 100,
                    "benchmark_cumulative_return_pct": ((1 + sample[benchmark]).prod() - 1) * 100,
                    "car_pct": car * 100,
                    "car_t_stat": car / standard_error if standard_error else None,
                    "estimation_observations": len(estimation),
                    "residual_sigma_daily_pct": sigma2 ** 0.5 * 100,
                    "status": "calculated",
                    "price_source": prices.attrs.get("price_sources", {}).get(ticker, "unavailable"),
                    "target_status": event["target_status"],
                    "caveat": "Single-event market-model estimate; not causal proof; concurrent news and leakage may affect returns.",
                })
    return rows


def update_readme_event_table(results):
    readme = ROOT / "README.md"
    if not readme.exists():
        return
    lines = readme.read_text(encoding="utf-8").splitlines()
    start_marker = "<!-- EVENT_STUDY_TABLE_START -->"
    end_marker = "<!-- EVENT_STUDY_TABLE_END -->"
    try:
        start = lines.index(start_marker)
        end = lines.index(end_marker, start + 1)
    except ValueError:
        return

    table = [
        "| Deal | Security | [-1,+1] CAR (t) | [-2,+2] CAR (t) | [-5,+5] CAR (t) |",
        "|---|---|---:|---:|---:|",
    ]
    groups = {}
    for row in results:
        groups.setdefault((row.get("deal", ""), row.get("security", "")), []).append(row)
    for (deal, security), rows in sorted(groups.items()):
        values = {}
        status = ""
        reference = ""
        for row in rows:
            if row.get("status") == "calculated":
                values[row.get("window")] = (
                    f"{row.get('car_pct', 0):+.2f}% (t={row.get('car_t_stat', 0):+.2f})"
                )
            else:
                status = row.get("status", "not calculated")
                reference = row.get("reference_reaction", "")
        fallback = f"n/a; {reference}" if reference else status or "n/a"
        table.append(
            f"| {deal} | {security} | {values.get('[-1,+1]', fallback)} | "
            f"{values.get('[-2,+2]', 'n/a')} | {values.get('[-5,+5]', 'n/a')} |"
        )
    lines[start + 1:end] = table
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    try:
        prices = load_prices()
    except (FileNotFoundError, ValueError) as error:
        print(f"Event study skipped safely: {error}")
        return
    results = event_rows(prices)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).round(6).to_csv(OUT, index=False)
    update_readme_event_table(results)
    print(f"Wrote {len(results)} event-study rows to {OUT}")


if __name__ == "__main__":
    main()
