"""
NEW: Asset Class Education — FD, RD, Emergency Fund, Cash

Well-established, general personal-finance facts about non-equity
asset classes — NOT specific to any real product/bank/rate, just the
standard characteristics every financial literacy resource covers.
Used to give a self-service investor the FULL picture alongside stock
ideas, not just an equity-only view.
"""

from typing import Dict, Any

ASSET_EDUCATION = {
    "Fixed Deposit (FD)": {
        "what_it_is": "A lump sum deposited with a bank for a fixed tenure at a fixed interest rate.",
        "benefits": [
            "Guaranteed, predictable returns — not subject to market ups and downs",
            "Capital protection — the principal amount is safe",
            "Good for short-to-medium-term goals where you can't afford to lose value",
        ],
        "tradeoffs": [
            "Returns are typically lower than long-term equity growth",
            "Interest earned is taxable as per your income slab",
            "Early withdrawal usually involves a penalty",
        ],
    },
    "Recurring Deposit (RD)": {
        "what_it_is": "A fixed amount deposited monthly for a fixed tenure, earning a fixed interest rate.",
        "benefits": [
            "Builds a savings discipline through regular monthly contributions",
            "Guaranteed returns, similar safety profile to FD",
            "Good for building a corpus over time from regular income",
        ],
        "tradeoffs": [
            "Lower returns than equity over the long run",
            "Less flexible than a savings account — committed monthly amount",
            "Interest is taxable",
        ],
    },
    "Emergency Fund": {
        "what_it_is": "Money set aside specifically for unexpected expenses — job loss, medical emergencies, urgent repairs.",
        "benefits": [
            "Financial safety net so you're not forced to sell investments at a bad time",
            "Reduces stress and reliance on high-interest debt during emergencies",
            "Standard guidance: 3-6 months of essential expenses, kept easily accessible",
        ],
        "tradeoffs": [
            "Money here earns little to no growth — that's the intentional tradeoff for safety and liquidity",
            "Should generally be built up BEFORE aggressive investing, not after",
        ],
    },
    "Cash": {
        "what_it_is": "Money kept immediately accessible — savings account or equivalent.",
        "benefits": [
            "Instant liquidity for day-to-day needs and near-term goals",
            "Zero market risk",
        ],
        "tradeoffs": [
            "Loses purchasing power to inflation over time if held in excess",
            "Generally best kept to what's needed for near-term spending and emergencies, not as a long-term growth strategy",
        ],
    },
}


def get_asset_education(asset_name: str = None) -> Dict[str, Any]:
    """
    Return general educational information about a non-equity asset
    class, or all of them if none specified.

    Args:
        asset_name: one of "Fixed Deposit (FD)", "Recurring Deposit (RD)",
                    "Emergency Fund", "Cash" — or None for all

    Returns:
        dict of asset education content
    """
    if asset_name and asset_name in ASSET_EDUCATION:
        return {asset_name: ASSET_EDUCATION[asset_name]}
    return ASSET_EDUCATION


if __name__ == "__main__":
    import json
    print(json.dumps(get_asset_education(), indent=2))
