"""
DAY 7: Streamlit Chat UI

The demo-facing front end. Lets an advisor pick a client, chat with
the agent in natural language, and see the conversation history.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from src.agent import run_agent
from src.tools.data_loader import load_clients

st.set_page_config(
    page_title="Agentic Investment Research Assistant",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar: client selector
# ---------------------------------------------------------------------------
st.sidebar.title("📊 Client Selector")

clients_df = load_clients()
client_options = {
    f"{row['client_id']} — {row['name']} ({row['risk_profile']})": row["client_id"]
    for _, row in clients_df.iterrows()
}

selected_label = st.sidebar.selectbox("Choose a client", list(client_options.keys()))
selected_client_id = client_options[selected_label]

st.sidebar.markdown("---")
st.sidebar.markdown("**Try asking:**")
st.sidebar.markdown("""
- What does this client's portfolio look like?
- How risky is this portfolio?
- How should we rebalance it?
- What's the current price of AAPL?
""")

if st.sidebar.button("🗑️ Clear conversation"):
    st.session_state.messages = []
    st.rerun()

# ---------------------------------------------------------------------------
# Main area: title + chat history
# ---------------------------------------------------------------------------
st.title("Agentic Investment Research Assistant")
st.caption(f"Currently viewing: **{selected_label}**")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset chat history display if the client changes (keeps demo clear,
# though memory in ChromaDB still persists per-client behind the scenes)
if "last_client" not in st.session_state:
    st.session_state.last_client = selected_client_id
if st.session_state.last_client != selected_client_id:
    st.session_state.messages = []
    st.session_state.last_client = selected_client_id

# Render past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask about this client's portfolio, risk, or a stock...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = run_agent(user_input, client_id=selected_client_id, verbose=False)
            except Exception as e:
                answer = f"⚠️ Something went wrong: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
