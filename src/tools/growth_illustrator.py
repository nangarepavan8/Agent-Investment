"""
NEW: Hypothetical Growth Illustrator

Shows what an investment MIGHT look like over 1-4 years IF a stock's
REAL historical average annual return continued — the same illustrative
technique real mutual funds and brokers use (with the same mandatory
honesty): this is explicitly NOT a prediction. Past average returns
are not a promise of future returns, and are clearly labeled as such
everywhere this is shown.

Uses REAL historical data (via historical_performance.py) to compute
an average annual return, then projects a hypothetical compound growth
curve — mathematically transparent, not a black-box forecast.
"""

from datetime import date
from typing import Dict, Any
from src.tools.historical_performance import get_historical_returns


def get_hypothetical_growth(symbol: str, investment_amount: float, years: int = 4) -> Dict[str, Any]:
    """
    Illustrate hypothetical growth of an investment IF the stock's real
    historical average annual return continued — NOT a prediction.

    Args:
        symbol: e.g. "TCS.NS"
        investment_amount: hypothetical amount invested, in INR
        years: how many years forward to illustrate (max 4)

    Returns:
        dict with symbol, avg_annual_return_pct (from real historical
        data), yearly_projection keyed by REAL future calendar years
        (e.g. "2027", "2028"), disclaimer
    """
    years = min(max(years, 1), 4)

    historical = get_historical_returns(symbol)
    if "error" in historical:
        return {"symbol": symbol, "error": historical["error"]}

    # Average the available historical annualized returns as the
    # illustrative growth rate (simple average across the returned
    # calendar-year lookback windows, each annualized to its own span)
    returns = historical["returns"]
    annualized_rates = []
    for year_label, return_data in returns.items():
        period_years = return_data["years_back"]
        total_return_pct = return_data["return_pct"]
        annualized_pct = ((1 + total_return_pct / 100) ** (1 / period_years) - 1) * 100
        annualized_rates.append(annualized_pct)

    avg_annual_return_pct = round(sum(annualized_rates) / len(annualized_rates), 2)

    current_year = date.today().year
    yearly_projection = {}
    value = investment_amount
    for i in range(1, years + 1):
        value = value * (1 + avg_annual_return_pct / 100)
        future_year_label = str(current_year + i)
        yearly_projection[future_year_label] = round(value, 2)

    return {
        "symbol": symbol,
        "investment_amount": investment_amount,
        "avg_annual_return_pct": avg_annual_return_pct,
        "yearly_projection": yearly_projection,
        "disclaimer": (
            "HYPOTHETICAL ILLUSTRATION ONLY. This assumes the stock's real "
            "historical average annual return continues unchanged — it does "
            "not. Past performance is not indicative of future returns. "
            "Actual results will differ and could be negative. This is not "
            "a prediction, forecast, or guarantee of any kind."
        ),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_hypothetical_growth("TCS.NS", 100000, years=4), indent=2))
