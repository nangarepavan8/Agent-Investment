"""
Daily Valuation Snapshot — Excel Export

Generates a fresh Excel workbook with EVERY client's current portfolio
valuation: stocks at live market prices, FD/RD/Bonds/government
schemes valued as of today's real date, cash balances, risk scores,
and asset allocation — everything get_portfolio_summary() already
computes, exported into a shareable, human-readable spreadsheet.

WHY THIS MATTERS: stock prices are already live every time the app
runs. But an advisor may want a physical snapshot file — to open in
Excel, email to a colleague, or archive for a specific date — without
needing to run the Streamlit app. This script produces exactly that.

Usage:
    python scripts/daily_valuation_snapshot.py

Output:
    data/daily_valuation_snapshot.xlsx  (overwritten each run)

To make this run automatically every day, see the "Scheduling" section
in the README (Windows Task Scheduler or the N8N automation endpoint
already built in api_server.py).
"""

import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.tools.data_loader import load_clients
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "daily_valuation_snapshot.xlsx"
)


def build_snapshot():
    clients_df = load_clients()

    summary_rows = []
    all_holdings_rows = []
    all_other_investments_rows = []

    for _, client_row in clients_df.iterrows():
        client_id = client_row["client_id"]
        print(f"Processing {client_id}...")

        summary = get_portfolio_summary(client_id)
        risk = calc_risk_score(client_id)

        if "error" in summary:
            print(f"  ⚠️ Skipped {client_id}: {summary['error']}")
            continue

        summary_rows.append({
            "Client ID": summary["client_id"],
            "Name": summary["client_name"],
            "Risk Profile": summary["risk_profile"],
            "Risk Score": risk["risk_score"],
            "Risk Level": risk["risk_level"],
            "Total Value (USD)": summary["total_value"],
            "Total Gain/Loss (USD)": summary["total_gain_loss"],
            "Gain/Loss %": summary["total_gain_loss_pct"],
            "Cash Balance (INR)": summary["cash_balance_inr"],
            "# Stock Holdings": len(summary["holdings"]),
            "# Other Investments": len(summary["other_investments"]),
        })

        for h in summary["holdings"]:
            all_holdings_rows.append({"Client ID": client_id, **h})

        for inv in summary["other_investments"]:
            all_other_investments_rows.append({"Client ID": client_id, **inv})

    summary_df = pd.DataFrame(summary_rows)
    holdings_df = pd.DataFrame(all_holdings_rows)
    other_df = pd.DataFrame(all_other_investments_rows)

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Client Summary", index=False)
        holdings_df.to_excel(writer, sheet_name="Stock Holdings", index=False)
        other_df.to_excel(writer, sheet_name="FD-RD-Bonds-Schemes", index=False)

    print(f"\n✅ Snapshot generated: {OUTPUT_PATH}")
    print(f"   Date: {date.today().isoformat()}")
    print(f"   {len(summary_rows)} clients, {len(all_holdings_rows)} stock holdings, "
          f"{len(all_other_investments_rows)} other investments")


if __name__ == "__main__":
    build_snapshot()
