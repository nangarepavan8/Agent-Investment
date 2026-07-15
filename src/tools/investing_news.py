"""
NEW: Investing News Aggregator — Real Headlines Across Stocks/Gold/Market

Aggregates REAL news headlines from a representative set of real
tickers (Nifty 50 index, Gold futures, and large-cap stocks across
major sectors) via yfinance's news data — the SAME tested mechanism
already used in market_context.py and swing_screener.py. This is real
data collection; the AI summarization/categorization happens
separately in agent.py's generate_news_digest(), following the exact
same "AI synthesizes real data, never invents it" pattern as
generate_sector_wise_suggestions().
"""

from typing import Dict, Any, List
import yfinance as yf
from src.tools.yf_session import get_yf_session

# Representative tickers across categories for a broad "investing news" feed
NEWS_SOURCE_TICKERS = {
    "Broad Market": "^NSEI",       # Nifty 50
    "Gold": "GC=F",
    "IT": "TCS.NS",
    "Banking": "HDFCBANK.NS",
    "Energy": "RELIANCE.NS",
    "Pharma": "SUNPHARMA.NS",
    "Automobile": "MARUTI.NS",
}


def _fetch_real_headlines(ticker_symbol: str, max_headlines: int = 3) -> List[str]:
    """Fetch real news headlines for one ticker. Returns empty list on failure."""
    try:
        ticker = yf.Ticker(ticker_symbol, session=get_yf_session())
        news_items = ticker.news or []
        headlines = []
        for item in news_items[:max_headlines]:
            content = item.get("content", item)
            title = content.get("title")
            if title:
                headlines.append(title)
        return headlines
    except Exception:
        return []


def get_aggregated_investing_news() -> Dict[str, Any]:
    """
    Aggregate REAL news headlines across a representative set of real
    tickers — broad market, gold, and stocks across major sectors.
    This is raw real data collection; categorization/summarization
    into a readable digest happens separately via AI synthesis
    (agent.py's generate_news_digest()).

    Returns:
        dict with "headlines_by_category" (real headlines grouped by
        category), disclaimer
    """
    headlines_by_category = {}
    for category, ticker_symbol in NEWS_SOURCE_TICKERS.items():
        headlines = _fetch_real_headlines(ticker_symbol)
        if headlines:
            headlines_by_category[category] = headlines

    return {
        "headlines_by_category": headlines_by_category,
        "total_categories_fetched": len(headlines_by_category),
        "disclaimer": (
            "Real news headlines fetched from real market data sources. This is a snapshot "
            "of currently available headlines, not a comprehensive or exhaustive news feed."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_aggregated_investing_news(), indent=2))
