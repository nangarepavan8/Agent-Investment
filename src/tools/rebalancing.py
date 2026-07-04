"""
Tool 3: Rebalancing Suggestion

Called when the user asks how to adjust/rebalance/diversify a
portfolio, usually as a follow-up after risk_score or
portfolio_summary have been discussed.

IMPLEMENTATION NOTE (Day 3):
Keep this rule-based (e.g. "if any sector > 40% of portfolio,
suggest trimming toward target allocation") — deterministic and
explainable beats a black-box suggestion for a hackathon demo.
"""

from typing import Dict, Any


def suggest_rebalancing(client_id: str) -> Dict[str, Any]:
    """
    Suggest portfolio rebalancing actions to reduce concentration risk
    and move toward a more diversified target allocation.

    Args:
        client_id: Unique identifier for the synthetic client
                    (e.g. "CLIENT_001").

    Returns:
        A dictionary containing:
            - current_allocation (dict: sector -> percentage)
            - target_allocation (dict: sector -> percentage)
            - suggested_actions (list of str, e.g. "Reduce Tech by 10%")
    """
    # TODO (Day 3): implement rule-based rebalancing logic
    raise NotImplementedError("Implement on Day 3 using synthetic dataset")
