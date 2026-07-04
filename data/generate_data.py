"""
DAY 2: Synthetic Portfolio Dataset Generator

Generates fully synthetic (fictional client names, but real public
stock tickers) portfolio data for the hackathon demo. Compliant with
the "public/synthetic data only" rule since no real client or
financial account data is used anywhere.

Usage:
    python data/generate_data.py

Outputs:
    data/clients.csv     — one row per client (profile info)
    data/holdings.csv    — one row per holding (client_id links the two)
"""

import csv
import random
import os

random.seed(42)  # reproducible output every time you run this

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Fictional client names — NOT real people
FIRST_NAMES = ["Aditi", "Rohan", "Meera", "Karan", "Priya", "Arjun", "Sneha", "Vikram", "Neha", "Farhan"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Reddy", "Kapoor", "Nair", "Gupta", "Rao", "Singh", "Menon"]

RISK_PROFILES = ["Conservative", "Moderate", "Aggressive"]

# Real public tickers grouped by sector — used only for realistic demo
# data (yfinance pulls live prices for these in Tool 4, Day 3)
SECTOR_TICKERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
    "Healthcare": ["JNJ", "PFE", "UNH", "ABBV"],
    "Financials": ["JPM", "BAC", "V", "MA"],
    "Consumer": ["AMZN", "TSLA", "MCD", "NKE"],
    "Energy": ["XOM", "CVX"],
    "Industrials": ["CAT", "BA", "HON"],
}

ALL_SECTORS = list(SECTOR_TICKERS.keys())


def generate_clients(n=10):
    clients = []
    for i in range(1, n + 1):
        client_id = f"CLIENT_{i:03d}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        risk_profile = random.choice(RISK_PROFILES)
        clients.append({
            "client_id": client_id,
            "name": name,
            "risk_profile": risk_profile,
        })
    return clients


def generate_holdings(clients):
    holdings = []
    for client in clients:
        client_id = client["client_id"]

        # Aggressive clients get more sectors/holdings + more concentration risk;
        # conservative clients get fewer, more spread out
        if client["risk_profile"] == "Aggressive":
            num_sectors = random.randint(2, 3)  # concentrated on purpose
        elif client["risk_profile"] == "Moderate":
            num_sectors = random.randint(3, 4)
        else:
            num_sectors = random.randint(4, 5)  # spread across more sectors

        chosen_sectors = random.sample(ALL_SECTORS, num_sectors)

        for sector in chosen_sectors:
            ticker = random.choice(SECTOR_TICKERS[sector])
            quantity = random.randint(5, 100)
            purchase_price = round(random.uniform(50, 500), 2)

            holdings.append({
                "client_id": client_id,
                "symbol": ticker,
                "sector": sector,
                "quantity": quantity,
                "purchase_price": purchase_price,
            })

    return holdings


def write_csv(filepath, rows, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {filepath}")


if __name__ == "__main__":
    clients = generate_clients(n=10)
    holdings = generate_holdings(clients)

    write_csv(
        os.path.join(OUTPUT_DIR, "clients.csv"),
        clients,
        fieldnames=["client_id", "name", "risk_profile"],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "holdings.csv"),
        holdings,
        fieldnames=["client_id", "symbol", "sector", "quantity", "purchase_price"],
    )

    print("\n✅ Day 2 dataset generated successfully.")
    print("Check data/clients.csv and data/holdings.csv")
