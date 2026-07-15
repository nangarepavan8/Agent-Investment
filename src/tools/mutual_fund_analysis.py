"""
Mutual Fund Historical Returns — Real NAV History via mfapi.in

Adds real historical 1/3/5-year return calculation for a specific
mutual fund scheme, using mfapi.in (a well-known public wrapper around
AMFI's historical NAV data). Reuses search_mutual_funds() from
mutual_fund_data.py rather than duplicating it — this file ONLY adds
the genuinely new capability: computing real backward-looking returns
for one scheme, same honest pattern as historical_performance.py for stocks.

HONESTY NOTE: like AMFI's NAV file, mfapi.in could not be tested
against a live network connection in this sandboxed environment —
should be verified on first real use.
"""

from typing import Dict, Any
from datetime import datetime
import requests

MFAPI_BASE_URL = "https://api.mfapi.in/mf"


def get_mutual_fund_historical_returns(scheme_code: str) -> Dict[str, Any]:
    """
    Fetch real historical NAV data for one scheme (via mfapi.in) and
    compute real 1/3/5-year returns — backward-looking only, NOT a
    prediction. Use search_mutual_funds() (mutual_fund_data.py) first
    to find a scheme_code by name.

    Args:
        scheme_code: AMFI scheme code

    Returns:
        dict with scheme_name, current_nav, historical returns, disclaimer
    """
    try:
        response = requests.get(f"{MFAPI_BASE_URL}/{scheme_code}", timeout=15)
        response.raise_for_status()
        data = response.json()

        nav_history = data.get("data", [])
        if not nav_history:
            raise ValueError("No historical NAV data available for this scheme.")

        scheme_name = data.get("meta", {}).get("scheme_name", "Unknown")
        current_nav = float(nav_history[0]["nav"])
        current_date = datetime.strptime(nav_history[0]["date"], "%d-%m-%Y").date()

        returns = {}
        for years_back, label in [(1, "1_year"), (3, "3_year"), (5, "5_year")]:
            target_date = current_date.replace(year=current_date.year - years_back)
            past_nav = None
            for entry in nav_history:
                entry_date = datetime.strptime(entry["date"], "%d-%m-%Y").date()
                if entry_date <= target_date:
                    past_nav = float(entry["nav"])
                    break
            if past_nav:
                returns[label] = round(((current_nav - past_nav) / past_nav) * 100, 2)

        return {
            "scheme_code": scheme_code,
            "scheme_name": scheme_name,
            "current_nav": current_nav,
            "as_of_date": current_date.isoformat(),
            "historical_returns_pct": returns,
            "disclaimer": (
                "Real historical NAV-based returns, backward-looking only. Past "
                "performance is NOT indicative of future returns — this is not a prediction."
            ),
        }
    except Exception as e:
        return {"error": f"Could not fetch historical mutual fund data: {str(e)}"}


if __name__ == "__main__":
    import json
    print(json.dumps(get_mutual_fund_historical_returns("119551"), indent=2))
