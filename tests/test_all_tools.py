"""
DAY 3 CHECK: Run this to verify all 4 tools work end-to-end.

Usage:
    python tests/test_all_tools.py
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.tools.rebalancing import suggest_rebalancing
from src.tools.market_context import get_market_context


def run():
    client_id = "CLIENT_001"

    print(f"\n{'='*50}\nTesting Tool 1: get_portfolio_summary({client_id})\n{'='*50}")
    print(json.dumps(get_portfolio_summary(client_id), indent=2))

    print(f"\n{'='*50}\nTesting Tool 2: calc_risk_score({client_id})\n{'='*50}")
    print(json.dumps(calc_risk_score(client_id), indent=2))

    print(f"\n{'='*50}\nTesting Tool 3: suggest_rebalancing({client_id})\n{'='*50}")
    print(json.dumps(suggest_rebalancing(client_id), indent=2))

    print(f"\n{'='*50}\nTesting Tool 4: get_market_context('AAPL')\n{'='*50}")
    print(json.dumps(get_market_context("AAPL"), indent=2))

    print("\n✅ All 4 tools ran without crashing.")
    print("Check the output above - if Tool 4 shows an 'error' key, check your internet connection.")


if __name__ == "__main__":
    run()
