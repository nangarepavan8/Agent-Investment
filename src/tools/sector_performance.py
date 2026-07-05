"""
NEW TOOL: Real Sector Index Performance (Nifty Sector Indices)

Answers "how is the IT sector doing today?" or "which sector is
performing best?" using REAL, LIVE Nifty sector index data via
yfinance — not the synthetic client portfolio data.

Coverage depends on Yahoo Finance's current data availability for
NSE sector indices — if a specific index isn't available, that
sector is gracefully omitted rather than crashing the whole tool.
"""

from typing import Dict, Any
import yfinance as yf

# Real Nifty sector index tickers (Yahoo Finance symbols)
NIFTY_SECTOR_INDICES = {
    "IT": "^CNXIT",
    "Banking": "^NSEBANK",
    "Automobile": "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "Energy": "^CNXENERGY",
    "Metal": "^CNXMETAL",
    "Realty": "^CNXREALTY",
}


def _get_index_change(ticker_symbol: str):
    """Fetch today's % change for one index. Returns None on any failure."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        current = info.get("regularMarketPrice") or info.get("currentPrice")
        previous = info.get("previousClose")
        if current and previous:
            return round(((current - previous) / previous) * 100, 2)
    except Exception:
        pass
    return None


def get_sector_performance(sector_name: str = None) -> Dict[str, Any]:
    """
    Get today's real performance for one Nifty sector index, or ALL
    sectors if none is specified.

    Args:
        sector_name: e.g. "IT", "Banking", "Automobile", "Pharma",
                     "FMCG", "Energy", "Metal", "Realty". If None or
                     not recognized, returns all available sectors.

    Returns:
        dict with sector -> day_change_pct for each resolved sector,
        plus best/worst performing sector if more than one resolved
    """
    sectors_to_check = (
        {sector_name: NIFTY_SECTOR_INDICES[sector_name]}
        if sector_name and sector_name in NIFTY_SECTOR_INDICES
        else NIFTY_SECTOR_INDICES
    )

    results = {}
    for sector, ticker_symbol in sectors_to_check.items():
        change_pct = _get_index_change(ticker_symbol)
        if change_pct is not None:
            results[sector] = change_pct

    if not results:
        return {"error": "Could not fetch sector index data right now — try again shortly."}

    response = {"sector_performance_pct": results}

    if len(results) > 1:
        best_sector = max(results, key=results.get)
        worst_sector = min(results, key=results.get)
        response["best_performing_sector"] = {"sector": best_sector, "change_pct": results[best_sector]}
        response["worst_performing_sector"] = {"sector": worst_sector, "change_pct": results[worst_sector]}

    return response


if __name__ == "__main__":
    import json
    print(json.dumps(get_sector_performance(), indent=2))
