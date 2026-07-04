"""
Tool 2: Risk Score Calculator

Called when the user asks "how risky is this portfolio", or
anything about volatility/exposure/concentration risk.

IMPLEMENTATION NOTE (Day 3):
Simple, explainable risk logic is fine for a demo — e.g. weighted by
sector concentration, single-stock concentration, and asset volatility
tier. Don't over-engineer; judges care about the agentic flow, not a
real quant risk model.
"""

from typing import Dict, Any


def calc_risk_score(client_id: str) -> Dict[str, Any]:
    """
    Calculate a risk score (0-100) for a client's portfolio based on
    sector concentration, single-position concentration, and asset
    volatility.

    Args:
        client_id: Unique identifier for the synthetic client
                    (e.g. "CLIENT_001").

    Returns:
        A dictionary containing:
            - risk_score (int, 0-100, higher = riskier)
            - risk_level (str: "Low" | "Medium" | "High")
            - contributing_factors (list of str explanations)
    """
    # TODO (Day 3): implement scoring logic against synthetic dataset
    raise NotImplementedError("Implement on Day 3 using synthetic dataset")
