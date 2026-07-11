"""
Historical Performance Lookback (1/2/3-year) + Flexible Price History

Answers "how has this stock actually performed over the past 1/2/3
years?" using REAL historical price data via yfinance — not a
prediction, a look backward. Green if positive return, red if
negative, over each lookback window.

Now includes REAL calendar years (not generic "Year 1/2/3" labels) and
a flexible-granularity price series (daily/weekly/monthly) for line
charts covering exactly what actually happened, at whatever zoom level
the user picks.

Approximates each year as 252 trading days (standard convention).
"""

from datetime import date
from typing import Dict, Any
import yfinance as yf
from src.tools.yf_session import get_yf_session
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def _resolve_symbol(symbol: str) -> str:
    """
    Try the symbol as given, then common Indian exchange suffixes
    (.NS for NSE, .BO for BSE) — so a user can type "TCS" or "WIPRO"
    without knowing the exact suffix. Returns the first symbol that
    actually resolves to real price data; raises if none do.
    """
    symbol = symbol.strip().upper()
    candidates = [symbol] if "." in symbol else [symbol, f"{symbol}.NS", f"{symbol}.BO"]

    for candidate in candidates:
        try:
            ticker = yf.Ticker(candidate, session=get_yf_session())
            info = ticker.info
            if info.get("currentPrice") or info.get("regularMarketPrice"):
                return candidate
        except Exception:
            continue

    raise ValueError(f"Could not find market data for '{symbol}' (also tried .NS/.BO for Indian exchanges).")


def get_historical_returns(symbol: str) -> Dict[str, Any]:
    """
    Fetch real historical returns for a stock over 1, 2, and 3-year
    lookback windows, labeled with REAL calendar years (e.g. "2025",
    not "1_year").

    Args:
        symbol: e.g. "TCS.NS", "RELIANCE.NS", or just "TCS"/"RELIANCE"
                (Indian exchange suffix auto-resolved if omitted)

    Returns:
        dict with symbol, current_price, and returns keyed by the
        actual calendar year each lookback window started from
    """
    try:
        resolved_symbol = _resolve_symbol(symbol)
        ticker = yf.Ticker(resolved_symbol, session=get_yf_session())
        hist = ticker.history(period="3y")

        if hist.empty or len(hist) < 30:
            raise ValueError(f"Not enough historical data available for '{symbol}'.")

        current_price = float(hist["Close"].iloc[-1])
        total_days = len(hist)
        today = date.today()

        returns = {}
        for years_back in [1, 2, 3]:
            lookback_days = years_back * TRADING_DAYS_PER_YEAR
            idx = max(0, total_days - lookback_days - 1)
            past_price = float(hist["Close"].iloc[idx])
            past_actual_date = hist.index[idx].date()

            return_pct = round(((current_price - past_price) / past_price) * 100, 2)

            # Real calendar year label, e.g. "2025" for a 1-year lookback from 2026
            year_label = str(today.year - years_back)

            returns[year_label] = {
                "years_back": years_back,
                "from_date": past_actual_date.isoformat(),
                "return_pct": return_pct,
                "is_positive": return_pct >= 0,
            }

        return {
            "symbol": symbol,
            "resolved_symbol": resolved_symbol,
            "current_price": round(current_price, 2),
            "as_of_date": today.isoformat(),
            "returns": returns,
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"Could not fetch historical data: {str(e)}"}


def get_price_history_series(symbol: str, granularity: str = "Monthly") -> Dict[str, Any]:
    """
    Fetch a real historical price series at a chosen granularity, for
    line-chart display — the user can zoom between daily, weekly, and
    monthly views of the SAME real underlying data.

    Args:
        symbol: e.g. "TCS.NS"
        granularity: "Daily" | "Weekly" | "Monthly"

    Returns:
        dict with symbol, granularity, dates (list of ISO date strings),
        prices (list of closing prices, same order as dates)
    """
    granularity_map = {
        "Daily": {"period": "3mo", "interval": "1d"},
        "Weekly": {"period": "1y", "interval": "1wk"},
        "Monthly": {"period": "3y", "interval": "1mo"},
    }
    settings = granularity_map.get(granularity, granularity_map["Monthly"])

    try:
        resolved_symbol = _resolve_symbol(symbol)
        ticker = yf.Ticker(resolved_symbol, session=get_yf_session())
        hist = ticker.history(period=settings["period"], interval=settings["interval"])

        if hist.empty:
            raise ValueError(f"No price history available for '{symbol}' at {granularity} granularity.")

        dates = [d.date().isoformat() for d in hist.index]
        prices = [round(float(p), 2) for p in hist["Close"]]

        return {
            "symbol": symbol,
            "resolved_symbol": resolved_symbol,
            "granularity": granularity,
            "dates": dates,
            "prices": prices,
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"Could not fetch price history: {str(e)}"}


if __name__ == "__main__":
    import json
    print("--- Historical returns (real calendar years) ---")
    print(json.dumps(get_historical_returns("TCS.NS"), indent=2))

    print("\n--- Price history series (Monthly) ---")
    result = get_price_history_series("TCS.NS", "Monthly")
    print(json.dumps({k: v for k, v in result.items() if k != "prices" and k != "dates"}, indent=2))
    if "dates" in result:
        print(f"Got {len(result['dates'])} data points from {result['dates'][0]} to {result['dates'][-1]}")
