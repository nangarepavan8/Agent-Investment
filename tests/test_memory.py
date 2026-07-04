"""
DAY 6 CHECK: Test ChromaDB memory in isolation (no OpenAI API calls needed).

Usage:
    python tests/test_memory.py

IMPORTANT FIRST-RUN NOTE:
The first time this runs, ChromaDB downloads a small embedding model
(~80MB) from huggingface.co. If this fails with a download/hash error,
your network may be blocking that domain. Test this NOW, not on demo
day - if it fails on your work network, try from home wifi or a
personal hotspot once to let it download and cache locally (it only
downloads once, then it's cached for all future runs).
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.memory import store_memory, retrieve_relevant_memory, clear_all_memory


def run():
    print("Clearing any old test memory...")
    clear_all_memory()

    print("\nStoring a memory for CLIENT_001...")
    store_memory(
        "CLIENT_001",
        "How risky is my portfolio?",
        "Risk score is 80 (High), driven by 74% concentration in Healthcare.",
    )

    print("Storing a memory for CLIENT_002 (different client, should stay separate)...")
    store_memory(
        "CLIENT_002",
        "What's my portfolio worth?",
        "Total portfolio value is $12,450 across 4 holdings.",
    )

    print("\nRetrieving memory for CLIENT_001 with a related follow-up question...")
    results = retrieve_relevant_memory("CLIENT_001", "What did we discuss about risk?")
    for r in results:
        print(f"  - {r}")

    if not results:
        print("  ⚠️  No results returned - something's wrong.")
    else:
        print(f"\n✅ Retrieved {len(results)} memory item(s) for CLIENT_001.")

    print("\nConfirming CLIENT_002's memory doesn't leak into CLIENT_001's results...")
    client_ids_in_results = [r for r in results if "12,450" in r]
    if client_ids_in_results:
        print("  ❌ FAIL: CLIENT_002 data leaked into CLIENT_001 query results!")
    else:
        print("  ✅ PASS: Memory is correctly isolated per client_id.")


if __name__ == "__main__":
    run()
