"""
Shared data-loading helper used by all 4 tools.
Keeps CSV-reading logic in one place instead of repeating it in every tool.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def load_clients() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, "clients.csv"))


def load_holdings() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, "holdings.csv"))


def get_client_holdings(client_id: str) -> pd.DataFrame:
    """Return only the holdings rows belonging to one client."""
    holdings = load_holdings()
    client_rows = holdings[holdings["client_id"] == client_id]
    if client_rows.empty:
        raise ValueError(f"No holdings found for client_id '{client_id}'. "
                          f"Valid IDs are CLIENT_001 through CLIENT_010.")
    return client_rows


def get_client_info(client_id: str) -> dict:
    """Return a client's name + risk profile."""
    clients = load_clients()
    row = clients[clients["client_id"] == client_id]
    if row.empty:
        raise ValueError(f"No client found with id '{client_id}'.")
    return row.iloc[0].to_dict()
