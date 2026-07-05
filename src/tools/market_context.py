"""
Tool 4: Market Context — Day 3 implementation, enhanced with news headlines

Uses yfinance (free, no API key) to pull real, live public market data
AND recent news headlines for a stock symbol. This is the one tool
that touches real-world data rather than the synthetic dataset — fine
per hackathon rules since stock prices/news are public market data,
not private client information.

STRETCH FEATURE: Recent headlines are included so the agent's final
answer can characterize sentiment (positive/neutral/negative) in
context — no separate sentiment-classifier call needed, since the
main agent LLM already reads this tool's output and can describe tone
naturally as part of synthesizing its answer.
"""

from typing import Dict, Any
import yfinance as yf


def get_market_context(symbol: str) -> Dict[str, Any]:
    """
    Fetch current public market data AND recent news headlines for a
    stock symbol.

    Args:
        symbol: e.g. "AAPL", "MSFT"

    Returns:
        dict with symbol, current_price, day_change_pct,
        fifty_two_week_range, recent_headlines (list of str, up to 3)
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

        # Fetch recent news headlines (free via yfinance, no separate API/key).
        # Wrapped in its own try/except since news data is less reliable than
        # price data and shouldn't break the whole tool if it's unavailable.
        recent_headlines = []
        try:
            news_items = ticker.news or []
            for item in news_items[:3]:
                # yfinance news items nest the actual article under "content"
                # in newer versions; fall back gracefully across formats.
                content = item.get("content", item)
                title = content.get("title")
                if title:
                    recent_headlines.append(title)
        except Exception:
            pass  # news is a bonus, not critical — fail silently

        return {
            "symbol": symbol,
            "company_name": info.get("shortName", symbol),
            "current_price": current_price,
            "day_change_pct": day_change_pct,
            "fifty_two_week_range": (fifty_two_week_low, fifty_two_week_high),
            "recent_headlines": recent_headlines,
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
