"""
NEW: NSE Live "Most Active by Volume" — ALL NSE, not a fixed list

Fetches REAL, live data directly from NSE India's own public website
data feed — the same data anyone can see on nseindia.com's "Most
Active Securities" page — covering the ENTIRE exchange, not a
predefined list of ~29 well-known stocks. This directly answers "give
me high-volume stocks from all NSE, including ones I've never heard of."

WHY THIS NEEDS SPECIAL HANDLING: NSE's website blocks plain script
requests (no browser-like session/cookies = blocked). The standard,
well-known workaround (used by most open-source NSE data tools) is to
first visit NSE's homepage to receive session cookies, then use that
same session to call their data endpoint — imitating a real browser,
same principle as yf_session.py's curl_cffi approach for Yahoo Finance.

HONESTY NOTE: this depends on NSE's public website structure staying
consistent. It has NOT been tested against a live network connection
in this development environment (sandboxed, no access to nseindia.com)
— it follows the standard, well-documented pattern, but should be
verified on first real use, same as any integration with an
unofficial/undocumented endpoint.
"""

from typing import Dict, Any, List

try:
    from curl_cffi import requests as curl_requests
    _HAS_CURL_CFFI = True
except ImportError:
    import requests as curl_requests
    _HAS_CURL_CFFI = False

NSE_HOMEPAGE = "https://www.nseindia.com"
NSE_MOST_ACTIVE_VOLUME_URL = "https://www.nseindia.com/api/live-analysis-volume-gainers"

# Headers that mimic a real browser — NSE blocks requests that look
# like plain scripts (missing these headers reliably returns 401/403)
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


def _get_nse_session():
    """
    Bootstrap a session with valid NSE cookies by visiting the
    homepage first — NSE's API endpoints reject requests that don't
    carry cookies from a prior page visit, a common anti-scraping
    measure. Uses curl_cffi (browser TLS fingerprint impersonation) if
    available — plain `requests` was found to be blocked with a 403
    even with correct headers/cookies, the same class of anti-bot
    protection curl_cffi was already needed for with Yahoo Finance
    (see yf_session.py).
    """
    if _HAS_CURL_CFFI:
        session = curl_requests.Session(impersonate="chrome", headers=NSE_HEADERS)
    else:
        session = curl_requests.Session()
        session.headers.update(NSE_HEADERS)
    # Visiting the homepage first sets the cookies the API endpoint expects
    session.get(NSE_HOMEPAGE, timeout=10)
    return session


def get_nse_most_active_by_volume(count: int = 30) -> Dict[str, Any]:
    """
    Fetch REAL, live "Most Active Securities by Volume" directly from
    NSE — covers the ENTIRE exchange, not a fixed list.

    Args:
        count: how many top-volume stocks to return

    Returns:
        dict with "stocks" (list of real symbol/volume/price data) or
        an "error" key if NSE's endpoint couldn't be reached — this can
        happen if NSE changes their site structure or blocks the
        request pattern, same risk as any unofficial data integration
    """
    try:
        session = _get_nse_session()
        response = session.get(NSE_MOST_ACTIVE_VOLUME_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        # NSE's response structure nests results under a "data" key
        raw_list = data.get("data", [])[:count]

        stocks = []
        for item in raw_list:
            symbol = item.get("symbol")
            if not symbol:
                continue
            stocks.append({
                "symbol": f"{symbol}.NS",  # add NSE suffix so yfinance can resolve it too
                "nse_symbol": symbol,
                "ltp": item.get("ltp"),
                "traded_volume": item.get("tradedQuantity") or item.get("volume"),
                "pct_change": item.get("perChange") or item.get("netPrice"),
            })

        return {
            "stocks": stocks,
            "source": "NSE India — live 'Most Active by Volume' feed (all-exchange, real-time)",
            "disclaimer": (
                "This is REAL, live volume data sourced directly from NSE, covering the "
                "ENTIRE exchange — NOT a Buy/Sell signal or prediction. High volume today "
                "does not predict what the stock will do next."
            ),
        }
    except Exception as e:
        return {
            "error": (
                f"Could not fetch live NSE data: {str(e)}. This may mean NSE's website "
                f"structure changed, or the request was blocked — this integration depends "
                f"on NSE's public (unofficial) data feed staying consistent."
            )
        }


if __name__ == "__main__":
    import json
    print(json.dumps(get_nse_most_active_by_volume(10), indent=2))
