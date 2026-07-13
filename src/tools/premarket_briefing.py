"""
NEW: Pre-Market Briefing — Real Overnight Global Cues

Answers "what should I check before market opens?" HONESTLY: real,
factual, backward-looking data about what already happened overnight
in global markets while India was closed — the same things real
financial pre-market briefings cover. This is NOT a prediction of
what Indian markets or any specific stock will do today — it's a
factual recap of overnight events that advisors/investors
conventionally check before market open.

Covers: US market overnight performance (Dow, Nasdaq, S&P 500), crude
oil overnight move, USD/INR overnight move, and the Nifty 50's own
last real close — all real data via yfinance, each independently
degrading gracefully if unavailable so one failed fetch doesn't break
the whole briefing.
"""

from typing import Dict, Any, Optional
import yfinance as yf
from src.tools.yf_session import get_yf_session

# Real, standard yfinance tickers for overnight global cues
PREMARKET_TICKERS = {
    "Dow Jones (US)": "^DJI",
    "Nasdaq (US)": "^IXIC",
    "S&P 500 (US)": "^GSPC",
    "Crude Oil (WTI)": "CL=F",
    "USD/INR": "USDINR=X",
    "Nifty 50 (last close)": "^NSEI",
}


def _get_real_change(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch real current price + day change % for one ticker. Returns
    None on any failure so one bad ticker doesn't break the briefing."""
    try:
        ticker = yf.Ticker(ticker_symbol, session=get_yf_session())
        info = ticker.info
        current = info.get("regularMarketPrice") or info.get("currentPrice")
        previous = info.get("previousClose")
        if current is None or previous is None:
            return None
        change_pct = round(((current - previous) / previous) * 100, 2)
        return {
            "level": round(float(current), 2),
            "change_pct": change_pct,
            "is_positive": change_pct >= 0,
        }
    except Exception:
        return None


def get_premarket_briefing() -> Dict[str, Any]:
    """
    Fetch a real, factual pre-market briefing: overnight US market
    performance, crude oil, USD/INR, and Nifty 50's last real close —
    everything needed for the SAME check real financial briefings do
    before market open. NOT a prediction of what today's session or any
    specific stock will do.

    Returns:
        dict with "items" (real data per real-world indicator, may be
        partial if some fetches fail), disclaimer
    """
    items = {}
    for label, symbol in PREMARKET_TICKERS.items():
        result = _get_real_change(symbol)
        if result:
            items[label] = result

    return {
        "items": items,
        "data_fetched": len(items),
        "data_attempted": len(PREMARKET_TICKERS),
        "disclaimer": (
            "This is REAL, factual data about what already happened overnight in global "
            "markets (backward-looking) — the same overnight cues real financial briefings "
            "cover. This does NOT predict what Indian markets, any sector, or any specific "
            "stock will do today. No one can reliably predict that."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_premarket_briefing(), indent=2))
