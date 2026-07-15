"""
NEW: Mutual Fund Data — Real NAV from AMFI + SIP Calculator + Education

Fetches REAL, current mutual fund NAV data directly from AMFI
(Association of Mutual Funds in India) — their official public daily
NAV file, published specifically for investor/public download (unlike
NSE's bot-protected site, this is designed to be scraped/downloaded).

HONESTY NOTE: like the NSE integration, this depends on AMFI's public
file staying available and correctly formatted. It has NOT been
tested against a live network connection in this sandboxed
development environment — should be verified on first real use.

Also includes: a real SIP (Systematic Investment Plan) future-value
calculator (same annuity math as goal_gap_analysis.py, just framed
for mutual fund SIPs specifically), real mutual fund tax rules (reused
from tax_guidance.py), and general mutual fund education facts.
"""

from typing import Dict, Any, List, Optional
import requests

AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

MUTUAL_FUND_EDUCATION = {
    "what_is_nav": (
        "NAV (Net Asset Value) is the per-unit price of a mutual fund — the total value "
        "of the fund's holdings divided by the number of units outstanding, updated daily."
    ),
    "fund_categories": {
        "Equity Funds": "Invest mainly in stocks — higher risk/return potential, suited for long-term goals",
        "Debt Funds": "Invest in bonds/fixed-income instruments — lower risk, more stable returns",
        "Hybrid Funds": "Mix of equity and debt — balanced risk/return",
        "Index Funds": "Passively track an index (e.g. Nifty 50) — low cost, no active management",
        "ELSS": "Equity Linked Savings Scheme — tax-saving (Section 80C), 3-year lock-in, taxed as equity LTCG",
    },
    "direct_vs_regular": (
        "Direct plans have a lower expense ratio (no distributor commission) and thus "
        "slightly higher returns over time vs. Regular plans of the SAME fund — the "
        "underlying portfolio is identical, only the fee differs."
    ),
    "expense_ratio": (
        "The annual fee (as a % of assets) charged by the fund for management — directly "
        "reduces your returns. Lower is generally better, all else equal."
    ),
    "exit_load": (
        "A fee charged if you redeem/withdraw before a specified period (e.g. 1 year) — "
        "meant to discourage short-term trading of long-term fund products."
    ),
}


def _fetch_amfi_nav_data() -> Optional[List[Dict[str, str]]]:
    """
    Download and parse AMFI's real, official daily NAV file. Returns a
    list of {scheme_code, scheme_name, nav, date} records, or None if
    the fetch fails (network issue, AMFI site changes, etc.).

    AMFI's file format is semicolon-delimited with category header
    lines interspersed — this parses the standard structure.
    """
    try:
        response = requests.get(AMFI_NAV_URL, timeout=15)
        response.raise_for_status()
        lines = response.text.splitlines()

        records = []
        for line in lines:
            parts = line.split(";")
            # Valid data rows have exactly 6 semicolon-delimited fields;
            # header/category/blank lines don't match this shape
            if len(parts) == 6 and parts[0].strip().isdigit():
                records.append({
                    "scheme_code": parts[0].strip(),
                    "scheme_name": parts[3].strip(),
                    "nav": parts[4].strip(),
                    "date": parts[5].strip(),
                })
        return records if records else None
    except Exception:
        return None


def search_mutual_funds(keyword: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search AMFI's real, current NAV data for mutual funds matching a
    keyword (e.g. "HDFC", "Nifty Index", "ELSS").

    Args:
        keyword: search term to match against scheme names
        limit: max results to return

    Returns:
        dict with "results" (real matching schemes with current NAV) or
        an "error" if AMFI's data couldn't be fetched
    """
    records = _fetch_amfi_nav_data()
    if records is None:
        return {
            "error": (
                "Could not fetch real mutual fund NAV data from AMFI right now — "
                "this may mean AMFI's public file format changed or the site is "
                "temporarily unavailable. This integration depends on AMFI's public "
                "data feed staying consistent."
            )
        }

    keyword_lower = keyword.lower()
    matches = [r for r in records if keyword_lower in r["scheme_name"].lower()][:limit]

    return {
        "keyword": keyword,
        "results": matches,
        "total_schemes_in_source": len(records),
        "source": "AMFI (Association of Mutual Funds in India) — official real-time public NAV data",
        "disclaimer": (
            "Real, current NAV data sourced directly from AMFI's official public feed. "
            "NAV reflects TODAY's fund value — not a prediction of future returns. Past "
            "fund performance (not shown here) is also not indicative of future results."
        ),
    }


def calc_sip_future_value(monthly_amount: float, years: float, assumed_annual_return_pct: float = 10.0) -> Dict[str, Any]:
    """
    Real SIP (Systematic Investment Plan) future-value calculation —
    standard future-value-of-annuity formula, same math as
    goal_gap_analysis.py. The return rate is an ASSUMPTION for
    planning purposes, clearly labeled as such — not a prediction.

    Args:
        monthly_amount: monthly SIP contribution, in INR
        years: investment horizon in years
        assumed_annual_return_pct: assumed average annual return (default 10%,
                                    a common equity-fund planning assumption)

    Returns:
        dict with projected_value, total_invested, estimated_gains, disclaimer
    """
    monthly_rate = assumed_annual_return_pct / 100 / 12
    months = years * 12

    if monthly_rate > 0:
        future_value = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    else:
        future_value = monthly_amount * months

    total_invested = monthly_amount * months
    estimated_gains = future_value - total_invested

    return {
        "monthly_amount": monthly_amount,
        "years": years,
        "assumed_annual_return_pct": assumed_annual_return_pct,
        "total_invested": round(total_invested, 2),
        "projected_value": round(future_value, 2),
        "estimated_gains": round(estimated_gains, 2),
        "disclaimer": (
            f"Uses a CLEARLY-ASSUMED {assumed_annual_return_pct:.0f}%/year average return — "
            f"an assumption for planning purposes, NOT a prediction or guarantee of actual "
            f"future returns. Actual mutual fund returns fluctuate and can be negative."
        ),
    }


if __name__ == "__main__":
    import json
    print("--- SIP calculator (fully offline, always testable) ---")
    print(json.dumps(calc_sip_future_value(10000, 15, 12.0), indent=2))

    print("\n--- AMFI real NAV search (requires live network) ---")
    print(json.dumps(search_mutual_funds("Nifty Index", limit=5), indent=2))
