"""
Tool 1: Portfolio Summary — Day 3 implementation
"""

from typing import Dict, Any
from src.tools.data_loader import get_client_holdings, get_client_info


def get_portfolio_summary(client_id: str) -> Dict[str, Any]:
    """
    Return a summary of a client's portfolio: total value (at purchase
    price basis), holdings list, and sector allocation percentages.

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with total_value, holdings, sector_allocation
    """
    client_info = get_client_info(client_id)
    holdings_df = get_client_holdings(client_id)

    holdings_df = holdings_df.copy()
    holdings_df["value"] = holdings_df["quantity"] * holdings_df["purchase_price"]

    total_value = round(holdings_df["value"].sum(), 2)

    holdings_list = [
        {
            "symbol": row["symbol"],
            "sector": row["sector"],
            "quantity": int(row["quantity"]),
            "value": round(row["value"], 2),
        }
        for _, row in holdings_df.iterrows()
    ]

    sector_totals = holdings_df.groupby("sector")["value"].sum()
    sector_allocation = {
        sector: round((value / total_value) * 100, 1)
        for sector, value in sector_totals.items()
    }

    return {
        "client_id": client_id,
        "client_name": client_info["name"],
        "risk_profile": client_info["risk_profile"],
        "total_value": total_value,
        "holdings": holdings_list,
        "sector_allocation": sector_allocation,
    }


if __name__ == "__main__":
    # Quick manual test - run: python -m src.tools.portfolio_summary
    import json
    print(json.dumps(get_portfolio_summary("CLIENT_001"), indent=2))
