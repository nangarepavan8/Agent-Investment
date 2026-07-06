"""
NEW: Historical Performance Lookback (1/2/3-year)

Answers "how has this stock actually performed over the past 1/2/3
years?" using REAL historical price data via yfinance — not a
prediction, a look backward. Green if positive return, red if
negative, over each lookback window.

Approximates each year as 252 trading days (standard convention).
"""

from typing import Dict, Any
import yfinance as yf

TRADING_DAYS_PER_YEAR = 252


def get_historical_returns(symbol: str) -> Dict[str, Any]:
    """
    Fetch real historical returns for a stock over 1, 2, and 3-year
    lookback windows.

    Args:
        symbol: e.g. "TCS.NS", "RELIANCE.NS"

    Returns:
        dict with symbol, current_price, and returns for each window:
        {"1_year": {"return_pct": ..., "is_positive": ...}, "2_year": ..., "3_year": ...}
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3y")

        if hist.empty or len(hist) < 30:
            raise ValueError(f"Not enough historical data available for '{symbol}'.")

        current_price = float(hist["Close"].iloc[-1])
        total_days = len(hist)

        returns = {}
        for years, label in [(1, "1_year"), (2, "2_year"), (3, "3_year")]:
            lookback_days = years * TRADING_DAYS_PER_YEAR
            idx = max(0, total_days - lookback_days - 1)
            past_price = float(hist["Close"].iloc[idx])

            return_pct = round(((current_price - past_price) / past_price) * 100, 2)
            returns[label] = {
                "return_pct": return_pct,
                "is_positive": return_pct >= 0,
            }

        return {
            "symbol": symbol,
            "current_price": round(current_price, 2),
            "returns": returns,
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"Could not fetch historical data: {str(e)}"}


if __name__ == "__main__":
    import json
    print(json.dumps(get_historical_returns("TCS.NS"), indent=2))
