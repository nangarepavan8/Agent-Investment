"""
Fixed-Income / Non-Stock Asset Valuation

Computes current value for Fixed Deposits, Recurring Deposits,
Corporate Bonds, and government schemes (PPF, NSC, Sovereign Gold
Bond) based on elapsed time since start_date and each instrument's
interest rate.

DELIBERATELY SIMPLIFIED, same philosophy as calc_risk_score and
suggest_rebalancing: these are explainable approximations for a demo,
not actuarially precise banking calculations. Real FD/RD compounding
frequency varies by bank/scheme; here everything compounds annually
except RD, which uses the standard recurring-deposit maturity formula.
"""

from datetime import date
from typing import Dict, Any

TODAY = date(2026, 7, 5)  # matches the fixed reference date used in data generation

# DEMO SIMPLIFICATION: stocks are priced in USD (real US tickers via
# yfinance), while cash/FD/RD/bonds/government schemes are denominated
# in INR (realistic for an Indian wealth-management context). A fixed
# conversion rate is used to combine them into one consistent total —
# not a live FX rate, but transparent and good enough for demo purposes.
USD_TO_INR_RATE = 83.0


def inr_to_usd(inr_amount: float) -> float:
    """Convert an INR amount to its USD equivalent using the fixed demo rate."""
    return inr_amount / USD_TO_INR_RATE


def _years_elapsed(start_date_str: str) -> float:
    start = date.fromisoformat(start_date_str)
    days = (TODAY - start).days
    return max(days / 365.25, 0)


def _compound_interest_value(principal: float, annual_rate: float, years_elapsed: float, tenure_years: float) -> float:
    """Standard annual compound interest, capped at the maturity value
    once the elapsed time passes the instrument's tenure."""
    effective_years = min(years_elapsed, tenure_years)
    return principal * ((1 + annual_rate) ** effective_years)


def _recurring_deposit_value(monthly_installment: float, annual_rate: float, months_elapsed: float, tenure_months: float) -> float:
    """
    Standard RD maturity formula (compounded quarterly, simplified to
    monthly for explainability):
        FV = R * [(1+i)^n - 1] / i * (1+i)
    where R = monthly installment, i = monthly interest rate, n = months elapsed.
    """
    effective_months = min(months_elapsed, tenure_months)
    if effective_months <= 0:
        return 0.0
    i = annual_rate / 12
    n = effective_months
    if i == 0:
        return monthly_installment * n
    return monthly_installment * (((1 + i) ** n - 1) / i) * (1 + i)


def value_instrument(instrument_type: str, principal_amount: float, annual_interest_rate: float,
                      start_date_str: str, tenure_years: float) -> Dict[str, Any]:
    """
    Compute the current value of a single non-stock instrument.

    For Recurring Deposit, principal_amount is treated as the MONTHLY
    installment (consistent with how RDs actually work — small regular
    deposits, not a lump sum).

    Returns:
        dict with current_value, years_elapsed, is_matured
    """
    years_elapsed = _years_elapsed(start_date_str)
    is_matured = years_elapsed >= tenure_years

    if instrument_type == "Recurring Deposit":
        months_elapsed = years_elapsed * 12
        tenure_months = tenure_years * 12
        current_value = _recurring_deposit_value(
            principal_amount, annual_interest_rate, months_elapsed, tenure_months
        )
    else:
        # Fixed Deposit, Corporate Bond, PPF, NSC, Sovereign Gold Bond —
        # all treated as lump-sum compound interest for this demo
        current_value = _compound_interest_value(
            principal_amount, annual_interest_rate, years_elapsed, tenure_years
        )

    return {
        "current_value": round(current_value, 2),
        "years_elapsed": round(years_elapsed, 2),
        "is_matured": is_matured,
    }


if __name__ == "__main__":
    # Quick manual test - run: python -m src.tools.fixed_income
    import json

    # A 4-year FD, ~1 year elapsed
    result = value_instrument("Fixed Deposit", 100000, 0.07, "2025-07-05", 4)
    print("FD example:", json.dumps(result, indent=2))

    # An RD with a monthly deposit of 5000, 2 years elapsed, 3-year tenure
    result = value_instrument("Recurring Deposit", 5000, 0.065, "2024-07-05", 3)
    print("RD example:", json.dumps(result, indent=2))
