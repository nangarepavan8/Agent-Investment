"""
DAY 9: Full Run-Through & Bug Fixing

Runs a broader set of queries than Day 4/5's test_agent.py, specifically
including edge cases that could trip up a live demo: invalid client IDs,
invalid stock symbols, ambiguous/off-topic questions, and multi-tool
queries. The goal is to surface bugs NOW, not in front of judges.

Usage:
    python tests/test_day9_full_runthrough.py

This makes real (billed) OpenAI API calls - expect a few cents total.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import run_agent

# Organized by category so you can see exactly what kind of bug you're hunting
TEST_CASES = {
    "Happy path — single tool": [
        ("CLIENT_001", "What does this portfolio contain?"),
        ("CLIENT_003", "How risky is this portfolio?"),
        ("CLIENT_005", "How should we rebalance this portfolio?"),
        (None, "What's the current price of MSFT?"),
    ],
    "Happy path — multi-tool in one query": [
        ("CLIENT_002", "Give me a full risk assessment and rebalancing plan"),
        ("CLIENT_004", "What's the portfolio summary and risk score?"),
    ],
    "Memory / follow-up questions": [
        ("CLIENT_001", "How risky is this portfolio?"),
        ("CLIENT_001", "Based on that, how should we rebalance it?"),
    ],
    "Edge cases — should NOT crash": [
        ("CLIENT_999", "How risky is this portfolio?"),          # invalid client
        (None, "What's the current price of ZZZZINVALID?"),      # invalid symbol
        (None, "What's the weather like today?"),                # off-topic
        ("CLIENT_001", ""),                                       # empty query
    ],
}


def run():
    total = 0
    for category, cases in TEST_CASES.items():
        print(f"\n{'='*70}\n{category}\n{'='*70}")
        for client_id, query in cases:
            total += 1
            print(f"\n--- Query: '{query}' (client={client_id}) ---")
            try:
                answer = run_agent(query, client_id=client_id, verbose=True)
                print(f"Answer: {answer}")
            except Exception as e:
                print(f"❌ CRASHED: {e}")

    print(f"\n{'='*70}")
    print(f"Ran {total} test queries. Review above for:")
    print("1. Did edge cases return a graceful message instead of crashing?")
    print("2. Did multi-tool queries call BOTH expected tools?")
    print("3. Did the memory follow-up correctly understand 'it'?")
    print("4. Are all answers clear prose, not raw JSON?")
    print("=" * 70)


if __name__ == "__main__":
    run()
