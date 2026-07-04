"""
Tool 1: Portfolio Summary

Called when the user asks about a client's holdings, allocation,
or general "what does this portfolio look like" questions.

IMPLEMENTATION NOTE (Day 3):
Will read from the synthetic dataset (data/portfolios.csv or .db)
and return a structured summary — no LLM call inside this function,
pure Python/pandas logic.
"""

from typing import Dict, Any


def get_portfolio_summary(client_id: str) -> Dict[str, Any]:
    """
    Return a summary of a client's portfolio: total value, holdings,
    sector allocation, and asset mix.

    Args:
        client_id: Unique identifier for the synthetic client
                    (e.g. "CLIENT_001").

    Returns:
        A dictionary containing:
            - total_value (float)
            - holdings (list of dicts: symbol, quantity, value)
            - sector_allocation (dict: sector -> percentage)
    """
    # TODO (Day 3): load from data/portfolios.csv, compute real values
    raise NotImplementedError("Implement on Day 3 using synthetic dataset")
