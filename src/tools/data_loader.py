"""
Shared data-loading helper used by all 4 tools.
Keeps CSV-reading logic in one place instead of repeating it in every tool.

Also merges in USER-ADDED clients/holdings/investments (created via the
chat, e.g. by a broker adding a real client) from separate "user_*.csv"
files — kept deliberately separate from the synthetic demo data
(clients.csv/holdings.csv/other_investments.csv) so that regenerating
the demo dataset (generate_data.py) never wipes out real clients a
broker has added.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")

USER_CLIENTS_PATH = os.path.join(DATA_DIR, "user_clients.csv")
USER_HOLDINGS_PATH = os.path.join(DATA_DIR, "user_holdings.csv")
USER_OTHER_INVESTMENTS_PATH = os.path.join(DATA_DIR, "user_other_investments.csv")

CLIENTS_COLUMNS = ["client_id", "name", "risk_profile", "age", "investment_goal",
                   "time_horizon", "income_bracket", "cash_balance"]
HOLDINGS_COLUMNS = ["client_id", "symbol", "sector", "quantity", "purchase_price", "purchase_date"]
OTHER_INVESTMENTS_COLUMNS = ["client_id", "instrument_type", "principal_amount",
                             "annual_interest_rate", "start_date", "tenure_years"]


def _load_user_csv(path: str, columns: list) -> pd.DataFrame:
    """Load a user-added CSV if it exists, else return an empty DataFrame
    with the correct columns (so pd.concat works cleanly either way)."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=columns)


def load_clients() -> pd.DataFrame:
    synthetic = pd.read_csv(os.path.join(DATA_DIR, "clients.csv"))
    user_added = _load_user_csv(USER_CLIENTS_PATH, CLIENTS_COLUMNS)
    return pd.concat([synthetic, user_added], ignore_index=True)


def load_holdings() -> pd.DataFrame:
    synthetic = pd.read_csv(os.path.join(DATA_DIR, "holdings.csv"))
    user_added = _load_user_csv(USER_HOLDINGS_PATH, HOLDINGS_COLUMNS)
    return pd.concat([synthetic, user_added], ignore_index=True)


def load_other_investments() -> pd.DataFrame:
    synthetic = pd.read_csv(os.path.join(DATA_DIR, "other_investments.csv"))
    user_added = _load_user_csv(USER_OTHER_INVESTMENTS_PATH, OTHER_INVESTMENTS_COLUMNS)
    return pd.concat([synthetic, user_added], ignore_index=True)


def get_client_other_investments(client_id: str) -> pd.DataFrame:
    """Return a client's FD/RD/Bond/government-scheme holdings (may be empty)."""
    other = load_other_investments()
    return other[other["client_id"] == client_id]


def get_client_holdings(client_id: str) -> pd.DataFrame:
    """
    Return only the holdings rows belonging to one client. Returns an
    EMPTY DataFrame (not an error) if the client exists but simply has
    no stock holdings yet (e.g. a newly-added client who only has
    cash/FD so far) — existence itself is validated by get_client_info()
    elsewhere, so this function's job is just to return what's there.
    """
    holdings = load_holdings()
    return holdings[holdings["client_id"] == client_id]


def get_client_info(client_id: str) -> dict:
    """Return a client's name + risk profile."""
    clients = load_clients()
    row = clients[clients["client_id"] == client_id]
    if row.empty:
        raise ValueError(f"No client found with id '{client_id}'.")
    return row.iloc[0].to_dict()
