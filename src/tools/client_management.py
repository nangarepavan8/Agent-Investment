"""
NEW: Client Management — Add Real Clients & Their Investments via Chat

Lets an advisor/broker add REAL new clients and their real investment
details (stocks, FD/RD/Bonds) through the chat, persisting them to
dedicated "user_*.csv" files — kept deliberately separate from the
synthetic demo data (clients.csv/holdings.csv/other_investments.csv)
so regenerating the demo dataset never wipes out real, added clients.

Once added, a new client immediately works with EVERY existing tool
(portfolio_summary, risk_score, rebalancing, goal_gap_analysis, etc.)
exactly like the original 10 synthetic clients — data_loader.py merges
synthetic + user-added data transparently, so no other code needed
any changes to support this.
"""

import os
import csv
from datetime import date
from typing import Dict, Any, Optional
from src.tools.data_loader import (
    DATA_DIR, USER_CLIENTS_PATH, USER_HOLDINGS_PATH, USER_OTHER_INVESTMENTS_PATH,
    CLIENTS_COLUMNS, HOLDINGS_COLUMNS, OTHER_INVESTMENTS_COLUMNS,
    load_clients,
)
from src.tools.stock_screener import SYMBOL_TO_SECTOR

VALID_RISK_PROFILES = ["Conservative", "Moderate", "Aggressive"]
VALID_INSTRUMENT_TYPES = ["Fixed Deposit", "Recurring Deposit", "Corporate Bond", "PPF", "NSC", "Sovereign Gold Bond"]


def _append_row(path: str, columns: list, row: dict):
    """Append one row to a user-added CSV, creating it with a header
    first if it doesn't exist yet."""
    file_exists = os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _generate_next_client_id() -> str:
    """Generate the next available user-added client ID (CLIENT_U001,
    CLIENT_U002, ...) — separate ID space from the synthetic
    CLIENT_001-010 so there's never a collision."""
    existing = load_clients()
    user_ids = [cid for cid in existing["client_id"] if str(cid).startswith("CLIENT_U")]
    if not user_ids:
        return "CLIENT_U001"
    max_num = max(int(cid.replace("CLIENT_U", "")) for cid in user_ids)
    return f"CLIENT_U{max_num + 1:03d}"


def add_client(name: str, age: int, investment_goal: str, time_horizon: str,
               risk_profile: str = "Moderate", income_bracket: str = "Not specified",
               cash_balance: float = 0.0) -> Dict[str, Any]:
    """
    Add a new real client, persisted to user_clients.csv. Immediately
    usable by every existing tool once added.

    Args:
        name: client's full name
        age: client's age
        investment_goal: e.g. "Retirement", "Wealth Growth", "Child Education"
        time_horizon: e.g. "Short-term (<3 yrs)", "Long-term (>7 yrs)"
        risk_profile: "Conservative" | "Moderate" | "Aggressive"
        income_bracket: e.g. "₹10-25 LPA" (optional, free text)
        cash_balance: uninvested cash balance in INR (optional, default 0)

    Returns:
        dict with the new client_id and confirmation, or an "error"
    """
    if risk_profile not in VALID_RISK_PROFILES:
        return {"error": f"risk_profile must be one of {VALID_RISK_PROFILES}, got '{risk_profile}'."}
    if age <= 0 or age > 120:
        return {"error": f"age must be a realistic value, got {age}."}

    new_client_id = _generate_next_client_id()
    row = {
        "client_id": new_client_id,
        "name": name,
        "risk_profile": risk_profile,
        "age": age,
        "investment_goal": investment_goal,
        "time_horizon": time_horizon,
        "income_bracket": income_bracket,
        "cash_balance": round(cash_balance, 2),
    }
    _append_row(USER_CLIENTS_PATH, CLIENTS_COLUMNS, row)

    return {
        "client_id": new_client_id,
        "name": name,
        "status": "created",
        "message": (
            f"Added new client {name} as {new_client_id}. They can now be selected in the "
            f"sidebar and used with every tool. Add their stock/FD/RD/Bond holdings next "
            f"using add_holding or add_other_investment."
        ),
    }


def add_holding(client_id: str, symbol: str, quantity: float, purchase_price: float,
                 purchase_date: Optional[str] = None, sector: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a real stock holding to an existing client (synthetic or
    user-added), persisted to user_holdings.csv. Live-priced
    automatically by the existing portfolio tools — no special
    handling needed beyond storing the real purchase details.

    Args:
        client_id: e.g. "CLIENT_U001" (from add_client) or an existing CLIENT_001-010
        symbol: real NSE/BSE ticker, e.g. "TCS.NS"
        quantity: number of shares
        purchase_price: real purchase price per share, in INR
        purchase_date: ISO date string (YYYY-MM-DD), defaults to today if not given
        sector: sector name — auto-detected from the known sector map if omitted and recognized

    Returns:
        dict confirming the holding was added, or an "error"
    """
    existing_clients = load_clients()
    if client_id not in existing_clients["client_id"].values:
        return {"error": f"No client found with id '{client_id}'. Add the client first with add_client."}

    if quantity <= 0 or purchase_price <= 0:
        return {"error": "quantity and purchase_price must both be positive numbers."}

    if not sector:
        sector = SYMBOL_TO_SECTOR.get(symbol, "Other")

    if not purchase_date:
        purchase_date = date.today().isoformat()

    row = {
        "client_id": client_id,
        "symbol": symbol,
        "sector": sector,
        "quantity": quantity,
        "purchase_price": round(purchase_price, 2),
        "purchase_date": purchase_date,
    }
    _append_row(USER_HOLDINGS_PATH, HOLDINGS_COLUMNS, row)

    return {
        "client_id": client_id,
        "symbol": symbol,
        "status": "added",
        "message": f"Added {quantity} shares of {symbol} at ₹{purchase_price:,.2f} to {client_id} (sector: {sector}).",
    }


def add_other_investment(client_id: str, instrument_type: str, principal_amount: float,
                          annual_interest_rate: float, start_date: Optional[str] = None,
                          tenure_years: float = 5) -> Dict[str, Any]:
    """
    Add a real non-stock investment (FD, RD, Corporate Bond, PPF, NSC,
    Sovereign Gold Bond) to an existing client, persisted to
    user_other_investments.csv.

    Args:
        client_id: e.g. "CLIENT_U001" or an existing CLIENT_001-010
        instrument_type: one of "Fixed Deposit", "Recurring Deposit",
                        "Corporate Bond", "PPF", "NSC", "Sovereign Gold Bond"
        principal_amount: amount invested, in INR
        annual_interest_rate: as a decimal, e.g. 0.07 for 7%
        start_date: ISO date string (YYYY-MM-DD), defaults to today if not given
        tenure_years: investment tenure in years (default 5)

    Returns:
        dict confirming the investment was added, or an "error"
    """
    existing_clients = load_clients()
    if client_id not in existing_clients["client_id"].values:
        return {"error": f"No client found with id '{client_id}'. Add the client first with add_client."}

    if instrument_type not in VALID_INSTRUMENT_TYPES:
        return {"error": f"instrument_type must be one of {VALID_INSTRUMENT_TYPES}, got '{instrument_type}'."}
    if principal_amount <= 0:
        return {"error": "principal_amount must be a positive number."}

    if not start_date:
        start_date = date.today().isoformat()

    row = {
        "client_id": client_id,
        "instrument_type": instrument_type,
        "principal_amount": round(principal_amount, 2),
        "annual_interest_rate": annual_interest_rate,
        "start_date": start_date,
        "tenure_years": tenure_years,
    }
    _append_row(USER_OTHER_INVESTMENTS_PATH, OTHER_INVESTMENTS_COLUMNS, row)

    return {
        "client_id": client_id,
        "instrument_type": instrument_type,
        "status": "added",
        "message": f"Added {instrument_type} of ₹{principal_amount:,.2f} to {client_id}.",
    }


def list_user_added_clients() -> Dict[str, Any]:
    """
    List every REAL client added via add_client_tool (not the 10
    synthetic demo clients), with a quick summary of each — a
    "client roster" view so a broker can see everyone they've added
    so far, and their client_id for use in other tools.

    Returns:
        dict with "clients" (list of real added clients with basic
        profile info), "count"
    """
    from src.tools.portfolio_summary import get_portfolio_summary

    all_clients = load_clients()
    user_added = all_clients[all_clients["client_id"].astype(str).str.startswith("CLIENT_U")]

    if user_added.empty:
        return {
            "clients": [],
            "count": 0,
            "message": "No clients have been added yet via add_client_tool. Add one to see it listed here.",
        }

    roster = []
    for _, row in user_added.iterrows():
        client_id = row["client_id"]
        try:
            summary = get_portfolio_summary(client_id)
            total_value = summary["total_value"]
            num_holdings = len(summary["holdings"])
            num_other_investments = len(summary["other_investments"])
        except Exception:
            total_value = None
            num_holdings = None
            num_other_investments = None

        roster.append({
            "client_id": client_id,
            "name": row["name"],
            "age": int(row["age"]),
            "risk_profile": row["risk_profile"],
            "investment_goal": row["investment_goal"],
            "time_horizon": row["time_horizon"],
            "total_portfolio_value": total_value,
            "num_stock_holdings": num_holdings,
            "num_other_investments": num_other_investments,
        })

    return {"clients": roster, "count": len(roster)}


if __name__ == "__main__":
    import json
    # Quick manual test - run: python -m src.tools.client_management
    result = add_client(
        name="Test Client", age=30, investment_goal="Wealth Growth",
        time_horizon="Long-term (>7 yrs)", risk_profile="Moderate", cash_balance=50000,
    )
    print(json.dumps(result, indent=2))

    if "client_id" in result:
        cid = result["client_id"]
        print(json.dumps(add_holding(cid, "TCS.NS", 10, 3500.00), indent=2))
        print(json.dumps(add_other_investment(cid, "Fixed Deposit", 100000, 0.07, tenure_years=3), indent=2))
