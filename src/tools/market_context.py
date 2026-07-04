"""
Tool 4: Market Context — Day 3 implementation

Uses yfinance (free, no API key) to pull real, live public market data
for a stock symbol. This is the one tool that touches real-world data
rather than the synthetic dataset — fine per hackathon rules since
stock prices are public market data, not private client information.
"""

from typing import Dict, Any
import yfinance as yf


def get_market_context(symbol: str) -> Dict[str, Any]:
    """
    Fetch current public market data for a stock symbol.

    Args:
        symbol: e.g. "AAPL", "MSFT"

    Returns:
        dict with symbol, current_price, day_change_pct, fifty_two_week_range
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose")

        if not current_price:
            raise ValueError(f"No price data returned for '{symbol}' — check the symbol is valid.")

        if current_price and previous_close:
            day_change_pct = round(((current_price - previous_close) / previous_close) * 100, 2)
        else:
            day_change_pct = None

        fifty_two_week_low = info.get("fiftyTwoWeekLow")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")

        return {
            "symbol": symbol,
            "company_name": info.get("shortName", symbol),
            "current_price": current_price,
            "day_change_pct": day_change_pct,
            "fifty_two_week_range": (fifty_two_week_low, fifty_two_week_high),
        }
    except Exception as e:
        # Demo safety net: if yfinance hiccups (rate limit, bad symbol, network),
        # return a clear error dict instead of crashing the whole agent response.
        return {
            "symbol": symbol,
            "error": f"Could not fetch market data: {str(e)}",
        }


if __name__ == "__main__":
    import json
    print(json.dumps(get_market_context("AAPL"), indent=2))
