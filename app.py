"""
DAY 7: Streamlit Chat UI

The demo-facing front end. Lets an advisor pick a client, chat with
the agent in natural language, and see the conversation history.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.agent import run_agent
from src.tools.data_loader import load_clients
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.monitoring import scan_all_clients
from src.audit_log import log_event, load_audit_log

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

EXAMPLE_QUESTIONS = {
    "Your Portfolio": [
        "What's this portfolio worth right now?",
        "Is this client up or down overall?",
        "How risky is this portfolio?",
        "How should we rebalance it?",
        "Which stocks should I book profit on?",
    ],
    "Stock Research": [
        "Should I invest in TCS?",
        "What's the outlook on AAPL?",
        "What will Infosys's future be?",
        "What's the sentiment on MSFT right now?",
        "Is Reliance a good buy?",
    ],
    "General Finance": [
        "What is diversification?",
        "How does compound interest work?",
        "What's the difference between a mutual fund and an ETF?",
        "What is a P/E ratio?",
        "What's the difference between stocks and bonds?",
    ],
}

if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

for category, questions in EXAMPLE_QUESTIONS.items():
    with st.sidebar.expander(f"💡 Try asking — {category}", expanded=False):
        for q in questions:
            if st.button(q, key=f"suggest_{q}", use_container_width=True):
                st.session_state.pending_query = q
                st.rerun()

st.sidebar.caption("Click a question above to send it directly — switch to the 💬 Chat tab to see the answer.")

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
    - `get_portfolio_summary` — real-time market value, gain/loss, sector allocation
    - `calc_risk_score` — 0-100 score with explainable contributing factors
    - `suggest_rebalancing` — rule-based rebalancing suggestions
    - `get_market_context` — live prices, fundamentals, analyst sentiment, news (any US or Indian ticker)
    - `profit_booking_tool` — flags holdings with significant gains/losses for profit-booking or tax-loss harvesting

    **Responsible by design:** For open-ended questions like "should I
    invest in X," the agent presents factual data (price, fundamentals,
    analyst view, sentiment) rather than a confident buy/sell call, and
    never predicts future prices — consistent with how real financial
    tools and advisors operate.

    **General finance questions** (e.g. "what is diversification?",
    "how does compound interest work?") are answered directly from the
    model's own knowledge — not every question needs a tool call, only
    ones involving a specific client or live stock data.

    **Memory:** Every exchange is stored per-client in ChromaDB (local
    vector store), so follow-up questions like *"how should we rebalance
    it?"* correctly resolve context from earlier in the conversation.

    **Data:** All client names and holdings are synthetic/fictional,
    generated locally — no real client or financial account data is used.

    **Future path:** This MVP runs on GPT-4o at hackathon scale. The
    documented enterprise roadmap upgrades to Azure OpenAI, Microsoft
    Fabric, and Azure hosting for production, multi-user deployment.
    """)

tab_chat, tab_dashboard, tab_alerts, tab_audit = st.tabs(
    ["💬 Chat", "📊 Dashboard", "🔔 Portfolio Alerts", "📋 Audit Log"]
)

# ---------------------------------------------------------------------------
# DASHBOARD TAB - calls tools directly (no LLM), so it's instant and free
# ---------------------------------------------------------------------------
with tab_dashboard:
    try:
        summary = get_portfolio_summary(selected_client_id)
        risk = calc_risk_score(selected_client_id)

        st.caption(
            f"👤 Age {summary.get('age', '—')} · Goal: {summary.get('investment_goal', '—')} · "
            f"Horizon: {summary.get('time_horizon', '—')}"
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Portfolio Value", f"${summary['total_value']:,.2f}")

        gain_loss = summary["total_gain_loss"]
        gain_loss_pct = summary["total_gain_loss_pct"]
        col2.metric(
            "Unrealized Gain/Loss",
            f"${gain_loss:,.2f}",
            f"{gain_loss_pct:+.2f}%",
            delta_color="normal",
        )

        risk_level = risk["risk_level"]
        risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(risk_level, "")
        col3.metric("Risk Score", f"{risk['risk_score']} / 100", f"{risk_emoji} {risk_level}")

        col4.metric("Cash Balance", f"₹{summary['cash_balance_inr']:,.0f}")

        if summary.get("note"):
            st.caption(f"⚠️ {summary['note']}")
        st.caption(f"ℹ️ {summary.get('total_value_currency_note', '')}")

        st.markdown("---")

        chart_col, factors_col = st.columns([2, 1])

        DONUT_COLORS = ["#5B2EDB", "#E8348B", "#F5A623", "#2ECC71", "#3498DB", "#E74C3C", "#95A5A6"]

        def render_donut(data_dict, title):
            if not data_dict:
                st.caption(f"No data available for {title.lower()}.")
                return
            labels = list(data_dict.keys())
            values = list(data_dict.values())
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=DONUT_COLORS, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                textposition="outside",
            )])
            fig.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True, key=f"donut_{title}")

        with chart_col:
            st.subheader("Asset Allocation (All Asset Classes)")
            render_donut(summary["asset_allocation"], "Asset Allocation")

            st.subheader("Sector Allocation (Within Stocks)")
            render_donut(summary["sector_allocation"], "Sector Allocation")

        with factors_col:
            st.subheader("Risk Factors")
            for factor in risk["contributing_factors"]:
                st.markdown(f"- {factor}")

        st.markdown("---")
        st.subheader("Stock Holdings")
        holdings_df = pd.DataFrame(summary["holdings"])
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)

        if summary["other_investments"]:
            st.subheader("Fixed Deposits, Bonds & Government Schemes")
            other_df = pd.DataFrame(summary["other_investments"])
            st.dataframe(other_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No FD/RD/Bond/government scheme holdings for this client.")

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
                st.warning("This includes a rebalancing or trading suggestion — advisor approval required before acting on it.")
                col_a, col_b = st.columns(2)
                if col_a.button("✅ Approve", key=f"approve_{i}"):
                    st.session_state.messages[i]["approval_decision"] = "approved"
                    log_event("approval_decision", selected_client_id, {"decision": "approved", "action": "rebalancing"})
                    st.rerun()
                if col_b.button("❌ Reject", key=f"reject_{i}"):
                    st.session_state.messages[i]["approval_decision"] = "rejected"
                    log_event("approval_decision", selected_client_id, {"decision": "rejected", "action": "rebalancing"})
                    st.rerun()
            elif msg.get("approval_decision") == "approved":
                st.success("✅ Rebalancing suggestion approved by advisor.")
            elif msg.get("approval_decision") == "rejected":
                st.error("❌ Rebalancing suggestion rejected by advisor.")

    chat_box_input = st.chat_input("Ask about this client's portfolio, risk, or a stock...")

    # A sidebar suggestion button click sets pending_query; treat it exactly
    # like typed input, then clear it so it doesn't resend on every rerun
    user_input = chat_box_input or st.session_state.pending_query
    st.session_state.pending_query = None

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

# ---------------------------------------------------------------------------
# AUDIT LOG TAB - persistent, exportable record of every autonomous action
# the agent took and every advisor approve/reject decision. Addresses the
# "Governance and Security" judging category from the hackathon poster.
# ---------------------------------------------------------------------------
with tab_audit:
    st.subheader("Audit Trail")
    st.caption(
        "Every tool call the agent makes, every portfolio scan, and every "
        "advisor approve/reject decision is logged here with a timestamp — "
        "a persistent compliance record, not just a live UI trace."
    )

    audit_df = load_audit_log()

    if audit_df.empty:
        st.info("No audit events yet — interact with the Chat or run a Portfolio Scan to generate log entries.")
    else:
        # Most recent first
        audit_df_display = audit_df.iloc[::-1].reset_index(drop=True)
        st.dataframe(audit_df_display, use_container_width=True, hide_index=True)
        st.caption(f"{len(audit_df)} total logged events.")

        csv_data = audit_df.to_csv(index=False)
        st.download_button(
            "⬇️ Export audit log as CSV",
            data=csv_data,
            file_name="audit_log_export.csv",
            mime="text/csv",
        )
