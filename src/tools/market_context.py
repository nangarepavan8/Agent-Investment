"""
Tool 4: Market Context — upgraded with fundamentals, analyst sentiment,
and automatic Indian-ticker fallback (.NS / .BO), to support open-ended
questions like "shall I invest in TCS?" or "what's the outlook on AAPL?"
— not just simple price lookups.

Uses yfinance (free, no API key) to pull real, live public market data.
This is the one tool that touches real-world data rather than the
synthetic dataset — fine per hackathon rules since stock prices/news/
fundamentals are public market data, not private client information.

IMPORTANT: this tool deliberately does NOT predict future prices or
tell the user to buy/sell. It returns factual data (price, fundamentals,
analyst consensus, news) so the agent can give a balanced, informative
answer — the actual investment decision is always the advisor's/user's,
consistent with how real financial tools and advisors operate.
"""

from typing import Dict, Any, Optional
import yfinance as yf


def _try_fetch(symbol: str) -> Optional[dict]:
    """Attempt to fetch info for one exact symbol. Returns None if no
    usable price data comes back (doesn't raise)."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price:
            return {"ticker_obj": ticker, "info": info, "resolved_symbol": symbol}
    except Exception:
        pass
    return None


def get_market_context(symbol: str) -> Dict[str, Any]:
    """
    Fetch current public market data, fundamentals, analyst sentiment,
    and recent news headlines for a stock symbol.

    Automatically tries common Indian exchange suffixes (.NS for NSE,
    .BO for BSE) if the plain symbol doesn't resolve — so "TCS" or
    "INFY" work without the user needing to know the exact suffix.

    Args:
        symbol: e.g. "AAPL", "MSFT", "TCS", "TCS.NS", "INFY.NS"

    Returns:
        dict with symbol, resolved_symbol, current_price, day_change_pct,
        fifty_two_week_range, pe_ratio, market_cap, analyst_recommendation,
        analyst_target_price, recent_headlines
    """
    try:
        # Try the symbol as given, then common Indian exchange suffixes
        candidates = [symbol, f"{symbol}.NS", f"{symbol}.BO"]
        result = None
        for candidate in candidates:
            result = _try_fetch(candidate)
            if result:
                break

        if not result:
            raise ValueError(
                f"No price data found for '{symbol}' (also tried .NS/.BO for Indian "
                f"exchanges) — check the symbol is valid."
            )

        ticker = result["ticker_obj"]
        info = result["info"]
        resolved_symbol = result["resolved_symbol"]

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose")
        day_change_pct = (
            round(((current_price - previous_close) / previous_close) * 100, 2)
            if current_price and previous_close else None
        )

        # Recent news headlines (best-effort, non-critical)
        recent_headlines = []
        try:
            news_items = ticker.news or []
            for item in news_items[:3]:
                content = item.get("content", item)
                title = content.get("title")
                if title:
                    recent_headlines.append(title)
        except Exception:
            pass

        return {
            "symbol": symbol,
            "resolved_symbol": resolved_symbol,
            "company_name": info.get("shortName", symbol),
            "current_price": current_price,
            "day_change_pct": day_change_pct,
            "fifty_two_week_range": (info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")),
            "pe_ratio": info.get("trailingPE"),
            "market_cap": info.get("marketCap"),
            "analyst_recommendation": info.get("recommendationKey"),  # e.g. "buy", "hold", "sell"
            "analyst_target_price": info.get("targetMeanPrice"),
            "recent_headlines": recent_headlines,
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "error": f"Could not fetch market data: {str(e)}",
        }


if __name__ == "__main__":
    import json
    print("--- US stock ---")
    print(json.dumps(get_market_context("AAPL"), indent=2))
    print("\n--- Indian stock (no suffix given) ---")
    print(json.dumps(get_market_context("TCS"), indent=2))
