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
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.monitoring import scan_all_clients

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
# Main area: title + tabs
# ---------------------------------------------------------------------------
st.title("Agentic Investment Research Assistant")
st.caption(
    "Ask a natural-language question — the agent decides which tool(s) to call, "
    "pulls real portfolio data, and remembers context across the conversation."
)
st.caption(f"Currently viewing: **{selected_label}**")

with st.expander("ℹ️ How this works (architecture)"):
    st.markdown("""
    **Flow:** Your question → GPT-4o reasons about which tool(s) apply →
    tool(s) execute against synthetic portfolio data → ChromaDB supplies
    relevant past conversation context → GPT-4o synthesizes a final answer.

    **Tools available to the agent:**
    - `get_portfolio_summary` — holdings, value, sector allocation
    - `calc_risk_score` — 0-100 score with explainable contributing factors
    - `suggest_rebalancing` — rule-based rebalancing suggestions
    - `get_market_context` — live public stock prices via yfinance

    **Memory:** Every exchange is stored per-client in ChromaDB (local
    vector store), so follow-up questions like *"how should we rebalance
    it?"* correctly resolve context from earlier in the conversation.

    **Data:** All client names and holdings are synthetic/fictional,
    generated locally — no real client or financial account data is used.

    **Future path:** This MVP runs on GPT-4o at hackathon scale. The
    documented enterprise roadmap upgrades to Azure OpenAI, Microsoft
    Fabric, and Azure hosting for production, multi-user deployment.
    """)

tab_chat, tab_dashboard, tab_alerts = st.tabs(["💬 Chat", "📊 Dashboard", "🔔 Portfolio Alerts"])

# ---------------------------------------------------------------------------
# DASHBOARD TAB - calls tools directly (no LLM), so it's instant and free
# ---------------------------------------------------------------------------
with tab_dashboard:
    try:
        summary = get_portfolio_summary(selected_client_id)
        risk = calc_risk_score(selected_client_id)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${summary['total_value']:,.2f}")

        risk_level = risk["risk_level"]
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "")
        col2.metric("Risk Score", f"{risk['risk_score']} / 100", f"{risk_emoji} {risk_level}")

        col3.metric("Number of Holdings", len(summary["holdings"]))

        st.markdown("---")

        chart_col, factors_col = st.columns([2, 1])

        with chart_col:
            st.subheader("Sector Allocation")
            allocation_df = pd.DataFrame(
                list(summary["sector_allocation"].items()),
                columns=["Sector", "Allocation %"],
            ).set_index("Sector")
            st.bar_chart(allocation_df)

        with factors_col:
            st.subheader("Risk Factors")
            for factor in risk["contributing_factors"]:
                st.markdown(f"- {factor}")

        st.markdown("---")
        st.subheader("Holdings Detail")
        holdings_df = pd.DataFrame(summary["holdings"])
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Could not load dashboard: {e}")

# ---------------------------------------------------------------------------
# ALERTS TAB - proactive monitoring across ALL clients (not just the
# one selected in the sidebar). This is what makes the agent "proactive"
# rather than purely reactive - it surfaces issues unprompted.
# ---------------------------------------------------------------------------
with tab_alerts:
    st.subheader("Portfolio Health Scan")
    st.caption(
        "Unlike the chat, which only answers about the client you ask, this scans "
        "ALL 10 clients at once and proactively flags anything needing attention — "
        "high risk levels, or risk scores that increased since the last scan."
    )

    if st.button("🔍 Run Portfolio Scan"):
        with st.spinner("Scanning all client portfolios..."):
            alerts = scan_all_clients()
        st.session_state.last_alerts = alerts

    if "last_alerts" in st.session_state:
        alerts = st.session_state.last_alerts
        if not alerts:
            st.success("✅ No alerts — all clients are within normal risk range.")
        else:
            st.warning(f"⚠️ {len(alerts)} client(s) need attention:")
            for alert in alerts:
                if alert["alert_type"] == "high_risk":
                    st.error(f"🔴 {alert['message']}")
                else:
                    st.warning(f"🟠 {alert['message']}")
    else:
        st.info("Click 'Run Portfolio Scan' to check all clients for risk issues.")

# ---------------------------------------------------------------------------
# CHAT TAB
# ---------------------------------------------------------------------------
with tab_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Reset chat history display if the client changes (keeps demo clear,
    # though memory in ChromaDB still persists per-client behind the scenes)
    if "last_client" not in st.session_state:
        st.session_state.last_client = selected_client_id
    if st.session_state.last_client != selected_client_id:
        st.session_state.messages = []
        st.session_state.last_client = selected_client_id

    # Render past messages (including any stored reasoning trace / approval state)
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            # Show the reasoning trace for assistant messages that used tools
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                with st.expander("🧠 Agent's reasoning"):
                    for tc in msg["tool_calls"]:
                        st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                    if msg.get("memory_hits"):
                        st.markdown(f"- Used {msg['memory_hits']} relevant memory item(s) from past conversation")

            # Human-in-the-loop: show approve/reject for rebalancing suggestions
            if msg["role"] == "assistant" and msg.get("requires_approval") and not msg.get("approval_decision"):
                st.warning("This includes a rebalancing suggestion — advisor approval required before acting on it.")
                col_a, col_b = st.columns(2)
                if col_a.button("✅ Approve", key=f"approve_{i}"):
                    st.session_state.messages[i]["approval_decision"] = "approved"
                    st.rerun()
                if col_b.button("❌ Reject", key=f"reject_{i}"):
                    st.session_state.messages[i]["approval_decision"] = "rejected"
                    st.rerun()
            elif msg.get("approval_decision") == "approved":
                st.success("✅ Rebalancing suggestion approved by advisor.")
            elif msg.get("approval_decision") == "rejected":
                st.error("❌ Rebalancing suggestion rejected by advisor.")

    user_input = st.chat_input("Ask about this client's portfolio, risk, or a stock...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_agent(user_input, client_id=selected_client_id, verbose=False)
                    answer = result["answer"]
                    tool_calls = result["tool_calls"]
                    memory_hits = result["memory_hits"]
                    requires_approval = result["requires_approval"]
                except Exception as e:
                    answer = f"⚠️ Something went wrong: {e}"
                    tool_calls = []
                    memory_hits = 0
                    requires_approval = False
            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "tool_calls": tool_calls,
            "memory_hits": memory_hits,
            "requires_approval": requires_approval,
        })
        st.rerun()
