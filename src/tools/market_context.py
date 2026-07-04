"""
Tool 4: Market Context

Called when the user asks about current market conditions for a
specific stock/symbol relevant to the client's holdings — the one
tool that pulls REAL (free, public) data via yfinance rather than
the synthetic dataset.

IMPLEMENTATION NOTE (Day 3):
yfinance requires no API key. Keep this simple: current price,
day change %, and 52-week range are plenty for demo purposes.
"""

from typing import Dict, Any


def get_market_context(symbol: str) -> Dict[str, Any]:
    """
    Fetch current public market data for a stock symbol using yfinance.

    Args:
        symbol: Stock ticker symbol (e.g. "AAPL", "MSFT").

    Returns:
        A dictionary containing:
            - symbol (str)
            - current_price (float)
            - day_change_pct (float)
            - fifty_two_week_range (tuple: low, high)
    """
    # TODO (Day 3): implement using yfinance.Ticker(symbol)
    raise NotImplementedError("Implement on Day 3 using yfinance")
