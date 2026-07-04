"""
Tool 3: Rebalancing Suggestion — Day 3 implementation

Rule-based, deterministic logic (not a black-box model): compares each
client's current sector allocation against a simple equal-weight
target across the sectors they hold, and flags overweight sectors.
"""

from typing import Dict, Any
from src.tools.data_loader import get_client_holdings, get_client_info


def suggest_rebalancing(client_id: str) -> Dict[str, Any]:
    """
    Suggest rebalancing actions to reduce sector concentration risk.

    Args:
        client_id: e.g. "CLIENT_001"

    Returns:
        dict with current_allocation, target_allocation, suggested_actions
    """
    client_info = get_client_info(client_id)
    holdings_df = get_client_holdings(client_id).copy()
    holdings_df["value"] = holdings_df["quantity"] * holdings_df["purchase_price"]

    total_value = holdings_df["value"].sum()
    sector_totals = holdings_df.groupby("sector")["value"].sum()
    current_allocation = {
        sector: round((value / total_value) * 100, 1)
        for sector, value in sector_totals.items()
    }

    num_sectors = len(current_allocation)
    equal_weight = round(100 / num_sectors, 1)
    target_allocation = {sector: equal_weight for sector in current_allocation}

    # Flag sectors overweight vs. equal-weight target by more than 10 points
    suggested_actions = []
    for sector, current_pct in current_allocation.items():
        diff = current_pct - equal_weight
        if diff > 10:
            suggested_actions.append(
                f"Reduce {sector} by approximately {diff:.0f} percentage points "
                f"(currently {current_pct:.0f}%, target ~{equal_weight:.0f}%)"
            )
        elif diff < -10:
            suggested_actions.append(
                f"Consider increasing {sector} by approximately {abs(diff):.0f} percentage points "
                f"(currently {current_pct:.0f}%, target ~{equal_weight:.0f}%)"
            )

    if not suggested_actions:
        suggested_actions.append("Portfolio is reasonably balanced across current sectors — no urgent action needed.")

    return {
        "client_id": client_id,
        "client_name": client_info["name"],
        "current_allocation": current_allocation,
        "target_allocation": target_allocation,
        "suggested_actions": suggested_actions,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(suggest_rebalancing("CLIENT_001"), indent=2))
