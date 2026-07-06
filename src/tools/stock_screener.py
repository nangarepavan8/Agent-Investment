"""
NEW: Stock Screener — Real Current Data, Personalized by Risk Category

Surfaces real, CURRENT market data (proximity to 52-week high, P/E
valuation, recent earnings growth) across a fixed universe of real
Indian stocks, then sorts/tags results based on which risk category
(Conservative/Moderate/Aggressive) they're most relevant to.

DELIBERATELY NOT A PREDICTION TOOL: every field here is a real,
verifiable, as-of-today data point (yfinance). Nothing here forecasts
future price movement or "breakouts" — it's a snapshot, clearly
labeled as such wherever it's shown to the user. Personalizing which
REAL data gets surfaced first (e.g. lower-P/E stocks first for a
Conservative investor) is honest; predicting what will happen next
is not, and this tool does not do the latter.
"""

from typing import Dict, Any, List, Optional
import yfinance as yf

# Fixed screening universe — same real NSE tickers used elsewhere in
# this project, flattened across all sectors.
SCREENER_UNIVERSE = [
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS",
    "HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "TITAN.NS",
    "TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS",
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS",
    "LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS",
]

# Ticker -> sector mapping, so every stock result can show its sector too
SYMBOL_TO_SECTOR = {
    "TCS.NS": "IT", "INFY.NS": "IT", "WIPRO.NS": "IT", "HCLTECH.NS": "IT", "TECHM.NS": "IT",
    "HDFCBANK.NS": "Banking", "ICICIBANK.NS": "Banking", "SBIN.NS": "Banking",
    "KOTAKBANK.NS": "Banking", "AXISBANK.NS": "Banking",
    "RELIANCE.NS": "Energy", "ONGC.NS": "Energy", "NTPC.NS": "Energy", "POWERGRID.NS": "Energy",
    "HINDUNILVR.NS": "FMCG", "ITC.NS": "FMCG", "NESTLEIND.NS": "FMCG", "TITAN.NS": "FMCG",
    "TATAMOTORS.NS": "Automobile", "MARUTI.NS": "Automobile",
    "BAJAJ-AUTO.NS": "Automobile", "EICHERMOT.NS": "Automobile",
    "SUNPHARMA.NS": "Pharma", "DRREDDY.NS": "Pharma", "CIPLA.NS": "Pharma", "DIVISLAB.NS": "Pharma",
    "LT.NS": "Industrials", "ADANIPORTS.NS": "Industrials", "ULTRACEMCO.NS": "Industrials",
}

PE_LOW_THRESHOLD = 20.0
EARNINGS_GROWTH_STRONG_THRESHOLD = 0.15  # 15%
NEAR_52WK_HIGH_THRESHOLD_PCT = -5.0  # within 5% of 52-week high


def _screen_one_stock(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch and tag real current data for one stock. Returns None on failure."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        pe_ratio = info.get("trailingPE")
        earnings_growth = info.get("earningsGrowth")  # fraction, e.g. 0.18 = 18%

        if not current_price or not fifty_two_week_high:
            return None

        pct_from_52wk_high = round(((current_price - fifty_two_week_high) / fifty_two_week_high) * 100, 2)

        tags = []
        reasons = []
        if pct_from_52wk_high >= NEAR_52WK_HIGH_THRESHOLD_PCT:
            tags.append("Near 52-Week High")
            reasons.append(f"Currently trading only {abs(pct_from_52wk_high):.1f}% below its 52-week high (as of today)")
        if pe_ratio is not None and pe_ratio < PE_LOW_THRESHOLD:
            tags.append("Low P/E")
            reasons.append(f"P/E ratio of {pe_ratio:.1f} is below the {PE_LOW_THRESHOLD:.0f} threshold used here — trading cheaper relative to earnings than average")
        if earnings_growth is not None and earnings_growth >= EARNINGS_GROWTH_STRONG_THRESHOLD:
            tags.append("Strong Earnings Growth")
            reasons.append(f"Reported {earnings_growth * 100:.1f}% earnings growth in the most recent period")

        if not reasons:
            reasons.append("Included in screening universe; no specific current-data highlight crossed the thresholds used here")

        return {
            "symbol": symbol,
            "sector": SYMBOL_TO_SECTOR.get(symbol, "Other"),
            "company_name": info.get("shortName", symbol),
            "current_price": current_price,
            "pct_from_52wk_high": pct_from_52wk_high,
            "pe_ratio": round(pe_ratio, 2) if pe_ratio is not None else None,
            "earnings_growth_pct": round(earnings_growth * 100, 2) if earnings_growth is not None else None,
            "tags": tags,
            "reason": " | ".join(reasons),
        }
    except Exception:
        return None


def get_stock_screener(risk_category: str = "Moderate", limit: int = 10,
                        preferred_sectors: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Screen the real stock universe and sort/tag results based on which
    risk category they're most relevant to. All fields are real,
    current, as-of-today data — NOT a prediction of future performance.

    Args:
        risk_category: "Conservative" | "Moderate" | "Aggressive"
        limit: max number of results to return
        preferred_sectors: optional list of sectors to filter to (e.g.
            ["IT", "Banking"]) — if None or empty, screens ALL sectors

    Returns:
        dict with risk_category, results (list of screened stocks,
        sorted by relevance to that risk category), disclaimer
    """
    universe = SCREENER_UNIVERSE
    if preferred_sectors:
        universe = [s for s in SCREENER_UNIVERSE if SYMBOL_TO_SECTOR.get(s) in preferred_sectors]
        if not universe:
            universe = SCREENER_UNIVERSE  # fall back to full universe if the filter matched nothing

    results = []
    for symbol in universe:
        screened = _screen_one_stock(symbol)
        if screened:
            results.append(screened)

    if not results:
        return {"error": "Could not fetch screener data right now — try again shortly."}

    # Sort by relevance to the risk category using REAL data fields only
    if risk_category == "Conservative":
        # Prioritize lower P/E (value) and steadier, less momentum-chasing picks
        results.sort(key=lambda r: (r["pe_ratio"] if r["pe_ratio"] is not None else 999))
    elif risk_category == "Aggressive":
        # Prioritize proximity to 52-week high (momentum) and earnings growth
        results.sort(key=lambda r: (
            -(r["earnings_growth_pct"] or 0),
            -(r["pct_from_52wk_high"] if r["pct_from_52wk_high"] is not None else -999),
        ))
    else:  # Moderate — balanced mix
        results.sort(key=lambda r: -len(r["tags"]))

    return {
        "risk_category": risk_category,
        "results": results[:limit],
        "disclaimer": (
            "Real, current market data as of today — NOT a prediction of future "
            "performance. Tags reflect present-day price/valuation/earnings data "
            "only, sorted by relevance to the selected risk category."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_stock_screener("Aggressive", limit=5), indent=2))
