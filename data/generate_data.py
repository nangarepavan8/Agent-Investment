"""
Synthetic Portfolio Dataset Generator — EXPANDED

Generates fully synthetic (fictional client names, but real public
stock tickers) portfolio data for the hackathon demo. Compliant with
the "public/synthetic data only" rule since no real client or
financial account data is used anywhere.

EXPANDED to include:
    - Richer client profiles: age, investment goal, time horizon,
      income bracket, cash balance
    - More holdings per client, with purchase dates
    - Non-stock asset classes: Fixed Deposits, Recurring Deposits,
      Corporate Bonds, and government schemes (PPF, NSC, Sovereign
      Gold Bond) — realistic for an Indian wealth-management context

Usage:
    python data/generate_data.py

Outputs:
    data/clients.csv            — one row per client (profile info)
    data/holdings.csv           — one row per stock holding
    data/other_investments.csv  — one row per FD/RD/Bond/govt scheme
"""

import csv
import random
import os
from datetime import date, timedelta

random.seed(42)  # reproducible output every time you run this

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY = date(2026, 7, 5)  # fixed reference date so output is reproducible

# Fictional client names — NOT real people
FIRST_NAMES = ["Aditi", "Rohan", "Meera", "Karan", "Priya", "Arjun", "Sneha", "Vikram", "Neha", "Farhan"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Reddy", "Kapoor", "Nair", "Gupta", "Rao", "Singh", "Menon"]

RISK_PROFILES = ["Conservative", "Moderate", "Aggressive"]
INVESTMENT_GOALS = ["Retirement", "Wealth Growth", "Child Education", "Home Purchase", "Regular Income"]
TIME_HORIZONS = ["Short-term (<3 yrs)", "Medium-term (3-7 yrs)", "Long-term (>7 yrs)"]
INCOME_BRACKETS = ["₹5-10 LPA", "₹10-25 LPA", "₹25-50 LPA", "₹50+ LPA"]

# Real public tickers grouped by sector — used only for realistic demo
# data (yfinance pulls live prices for these in the market/portfolio tools)
SECTOR_TICKERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
    "Healthcare": ["JNJ", "PFE", "UNH", "ABBV"],
    "Financials": ["JPM", "BAC", "V", "MA"],
    "Consumer": ["AMZN", "TSLA", "MCD", "NKE"],
    "Energy": ["XOM", "CVX"],
    "Industrials": ["CAT", "BA", "HON"],
}
ALL_SECTORS = list(SECTOR_TICKERS.keys())

# Non-stock instrument types with realistic Indian interest rates (annual).
# Sovereign Gold Bond's real return also depends on gold price appreciation;
# simplified here to its fixed interest component only, for explainability.
INSTRUMENT_RATES = {
    "Fixed Deposit": 0.070,
    "Recurring Deposit": 0.065,
    "Corporate Bond": 0.078,
    "PPF": 0.071,
    "NSC": 0.077,
    "Sovereign Gold Bond": 0.025,
}
INSTRUMENT_TYPICAL_TENURE_YEARS = {
    "Fixed Deposit": (1, 5),
    "Recurring Deposit": (1, 3),
    "Corporate Bond": (3, 10),
    "PPF": (15, 15),
    "NSC": (5, 5),
    "Sovereign Gold Bond": (8, 8),
}


def random_past_date(min_days_ago, max_days_ago):
    days_ago = random.randint(min_days_ago, max_days_ago)
    return TODAY - timedelta(days=days_ago)


def generate_clients(n=10):
    clients = []
    for i in range(1, n + 1):
        client_id = f"CLIENT_{i:03d}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        risk_profile = random.choice(RISK_PROFILES)
        age = random.randint(28, 65)
        investment_goal = random.choice(INVESTMENT_GOALS)
        time_horizon = random.choice(TIME_HORIZONS)
        income_bracket = random.choice(INCOME_BRACKETS)
        cash_balance = round(random.uniform(50000, 800000), 2)  # INR, uninvested cash

        clients.append({
            "client_id": client_id,
            "name": name,
            "risk_profile": risk_profile,
            "age": age,
            "investment_goal": investment_goal,
            "time_horizon": time_horizon,
            "income_bracket": income_bracket,
            "cash_balance": cash_balance,
        })
    return clients


def generate_holdings(clients):
    holdings = []
    for client in clients:
        client_id = client["client_id"]

        # Aggressive clients get more sectors/holdings + more concentration risk;
        # conservative clients get fewer, more spread out
        if client["risk_profile"] == "Aggressive":
            num_sectors = random.randint(3, 4)
        elif client["risk_profile"] == "Moderate":
            num_sectors = random.randint(4, 5)
        else:
            num_sectors = random.randint(5, 6)

        num_sectors = min(num_sectors, len(ALL_SECTORS))
        chosen_sectors = random.sample(ALL_SECTORS, num_sectors)

        for sector in chosen_sectors:
            # Allow occasional second holding in the same sector for more
            # varied, realistic-looking portfolios
            num_holdings_in_sector = random.choice([1, 1, 2])
            tickers_in_sector = random.sample(
                SECTOR_TICKERS[sector], min(num_holdings_in_sector, len(SECTOR_TICKERS[sector]))
            )
            for ticker in tickers_in_sector:
                quantity = random.randint(5, 100)
                purchase_price = round(random.uniform(50, 500), 2)
                purchase_date = random_past_date(30, 900)  # 1 month to ~2.5 years ago

                holdings.append({
                    "client_id": client_id,
                    "symbol": ticker,
                    "sector": sector,
                    "quantity": quantity,
                    "purchase_price": purchase_price,
                    "purchase_date": purchase_date.isoformat(),
                })

    return holdings


def generate_other_investments(clients):
    """FD, RD, Corporate Bonds, and government schemes per client."""
    other_investments = []
    for client in clients:
        client_id = client["client_id"]

        # Conservative clients hold MORE non-stock instruments (safer mix);
        # aggressive clients hold fewer
        if client["risk_profile"] == "Conservative":
            num_instruments = random.randint(2, 4)
        elif client["risk_profile"] == "Moderate":
            num_instruments = random.randint(1, 3)
        else:
            num_instruments = random.randint(0, 2)

        instrument_types = random.sample(
            list(INSTRUMENT_RATES.keys()), min(num_instruments, len(INSTRUMENT_RATES))
        )

        for instrument_type in instrument_types:
            rate = INSTRUMENT_RATES[instrument_type]
            min_tenure, max_tenure = INSTRUMENT_TYPICAL_TENURE_YEARS[instrument_type]
            tenure_years = random.randint(min_tenure, max_tenure) if min_tenure != max_tenure else min_tenure

            if instrument_type == "Recurring Deposit":
                # RD principal_amount represents the MONTHLY installment,
                # not a lump sum - realistic RD deposits are much smaller
                principal = round(random.uniform(2000, 20000), 2)
            else:
                principal = round(random.uniform(50000, 500000), 2)  # lump-sum instruments (INR)

            start_date = random_past_date(180, min(tenure_years * 365, 1800))

            other_investments.append({
                "client_id": client_id,
                "instrument_type": instrument_type,
                "principal_amount": principal,
                "annual_interest_rate": rate,
                "start_date": start_date.isoformat(),
                "tenure_years": tenure_years,
            })

    return other_investments


def write_csv(filepath, rows, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    clients = generate_clients(n=10)
    holdings = generate_holdings(clients)
    other_investments = generate_other_investments(clients)

    write_csv(
        os.path.join(OUTPUT_DIR, "clients.csv"),
        clients,
        fieldnames=["client_id", "name", "risk_profile", "age", "investment_goal",
                    "time_horizon", "income_bracket", "cash_balance"],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "holdings.csv"),
        holdings,
        fieldnames=["client_id", "symbol", "sector", "quantity", "purchase_price", "purchase_date"],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "other_investments.csv"),
        other_investments,
        fieldnames=["client_id", "instrument_type", "principal_amount",
                    "annual_interest_rate", "start_date", "tenure_years"],
    )

    print(f"\n✅ Expanded dataset generated successfully.")
    print("Check data/clients.csv, data/holdings.csv, and data/other_investments.csv")
