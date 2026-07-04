"""
DAY 6: Vector Memory (ChromaDB)

Gives the agent persistent, per-client memory across conversations.
Each query + answer is stored as a "memory" tagged with the client_id,
so future queries can retrieve relevant past context — this is what
turns the agent from a one-off Q&A tool into something that gives
ongoing, personalized guidance.

Storage is local (a folder on disk), no cloud account or API key needed.
"""

import os
import uuid
import time
import chromadb

# NOTE: On first run, Chroma's default embedding function downloads a small
# model (~80MB) from huggingface.co. If your network blocks that domain
# (common on some corporate networks), this will fail. Test this EARLY,
# not on demo day - see README "Day 6" section for how to pre-warm it.

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")

_client = chromadb.PersistentClient(path=DB_PATH)
_collection = _client.get_or_create_collection(name="client_conversations")


def store_memory(client_id: str, user_query: str, agent_answer: str) -> None:
    """
    Save one exchange (query + answer) to memory, tagged with the client_id
    so it can be retrieved later for that specific client.
    """
    memory_text = f"Q: {user_query}\nA: {agent_answer}"
    memory_id = str(uuid.uuid4())

    _collection.add(
        ids=[memory_id],
        documents=[memory_text],
        metadatas=[{
            "client_id": client_id,
            "timestamp": time.time(),
        }],
    )


def retrieve_relevant_memory(client_id: str, current_query: str, n_results: int = 3) -> list:
    """
    Retrieve the most relevant past exchanges for this client, based on
    similarity to the current query. Returns a list of memory text strings
    (empty list if nothing found yet for this client).
    """
    # Chroma requires at least 1 item in the collection to query
    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[current_query],
        n_results=n_results,
        where={"client_id": client_id},
    )

    documents = results.get("documents", [[]])[0]
    return documents


def clear_all_memory() -> None:
    """Wipe all stored memory - useful for demo resets between rehearsals."""
    global _collection
    _client.delete_collection(name="client_conversations")
    _collection = _client.get_or_create_collection(name="client_conversations")


if __name__ == "__main__":
    # Quick manual test - run: python -m src.memory
    print("Storing a test memory for CLIENT_001...")
    store_memory(
        "CLIENT_001",
        "How risky is my portfolio?",
        "Your portfolio has a High risk score of 80, driven mainly by 74% concentration in Healthcare.",
    )

    print("Retrieving relevant memory for a follow-up question...")
    results = retrieve_relevant_memory("CLIENT_001", "What did we say about my risk before?")
    for r in results:
        print(f"- {r}")

    print("\n✅ Memory store/retrieve working.")
