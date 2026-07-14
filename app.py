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

from src.agent import run_agent, generate_sector_wise_suggestions, generate_client_executive_summary
from src.tools.data_loader import load_clients
from src.tools.portfolio_summary import get_portfolio_summary
from src.tools.risk_score import calc_risk_score
from src.monitoring import scan_all_clients
from src.audit_log import log_event, load_audit_log
from src.tools.investor_guidance import get_investment_guidance, VALID_GOALS, VALID_HORIZONS
from src.tools.historical_performance import get_historical_returns, get_price_history_series
from src.tools.sector_performance import get_sector_performance, NIFTY_SECTOR_INDICES
from src.tools.stock_screener import get_stock_screener, get_stock_screener_by_sector, SYMBOL_TO_SECTOR
from src.tools.growth_illustrator import get_hypothetical_growth
from src.tools.asset_education import get_asset_education
from src.tools.goal_gap_analysis import calc_goal_gap
from src.tools.tax_guidance import get_capital_gains_rules, get_tax_saving_instruments, CAPITAL_GAINS_RULES
from src.tools.swing_screener import get_swing_analysis, get_swing_screener_by_sector
from src.tools.nse_live_data import get_nse_most_active_by_volume
from src.tools.premarket_briefing import get_premarket_briefing
from src.tools.gold_analysis import get_gold_analysis

st.set_page_config(
    page_title="Agentic Investment Research Assistant",
    page_icon="📊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session-wide query cap — protects a live demo from a runaway OpenAI bill
# or rate-limit if someone (e.g. a judge exploring on their own) spams the
# chat. Applies across ALL chat surfaces (advisor chat, investor chat,
# screener chat) combined, since they all hit the same OpenAI account.
# ---------------------------------------------------------------------------
MAX_QUERIES_PER_SESSION = 40


def check_query_budget() -> bool:
    """
    Returns True if there's still budget left this session, and
    increments the counter. Returns False (and shows a warning) if the
    cap has been hit — the caller should skip running the agent.
    """
    if "session_query_count" not in st.session_state:
        st.session_state.session_query_count = 0

    if st.session_state.session_query_count >= MAX_QUERIES_PER_SESSION:
        st.error(
            f"⚠️ This session has reached its query limit ({MAX_QUERIES_PER_SESSION}) "
            f"to protect against runaway API costs. Restart the app to reset."
        )
        return False

    st.session_state.session_query_count += 1
    return True

# ---------------------------------------------------------------------------
# Custom styling — TVS Next brand colors (navy + orange), gradient hero
# header, polished cards, smoother tabs
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Import a cleaner font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Gradient hero banner — TVS Next navy-to-orange, replacing the plain title */
    .hero-banner {
        background: linear-gradient(120deg, #0B1F4D 0%, #16305C 55%, #F5821F 130%);
        padding: 2rem 2.2rem;
        border-radius: 18px;
        margin-bottom: 1.2rem;
        box-shadow: 0 8px 24px rgba(11, 31, 77, 0.30);
    }
    .hero-banner h1 {
        color: white;
        font-weight: 800;
        font-size: 2.1rem;
        margin: 0 0 0.4rem 0;
    }
    .hero-banner p {
        color: rgba(255,255,255,0.92);
        font-size: 1.02rem;
        margin: 0;
    }

    /* Metric cards get a subtle lift and shadow */
    div[data-testid="stMetric"] {
        background: linear-gradient(160deg, #ffffff 0%, #f4f7fb 100%);
        border: 1px solid #dde6f0;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        box-shadow: 0 2px 8px rgba(11, 31, 77, 0.08);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(11, 31, 77, 0.16);
    }

    /* Tabs — more breathing room, bolder active tab */
    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0B1F4D !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #F5821F !important;
        height: 3px !important;
    }

    /* Buttons — gradient primary action buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        border: none;
        transition: transform 0.12s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(120deg, #0B1F4D, #F5821F);
        color: white;
    }

    /* Expanders — softer, card-like */
    div[data-testid="stExpander"] {
        border-radius: 12px;
        border: 1px solid #dde6f0;
    }

    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafbfd 0%, #f0f4f9 100%);
    }
</style>
""", unsafe_allow_html=True)

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
        "How is the IT sector doing today?",
        "Which sector is performing best right now?",
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
# Main area: company banner + title + tabs
# ---------------------------------------------------------------------------
st.image("assets/tvsnext_banner.jpg", use_container_width=True)

st.markdown(f"""
<div class="hero-banner">
    <h1>📊 Agentic Investment Research Assistant</h1>
    <p>Ask a natural-language question — the agent decides which tool(s) to call, pulls real
    portfolio data, and remembers context across the conversation.</p>
</div>
""", unsafe_allow_html=True)
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

tab_chat, tab_dashboard, tab_alerts, tab_audit, tab_investor, tab_screener, tab_tax, tab_swing, tab_gold = st.tabs(
    ["💬 Chat", "📊 Dashboard", "🔔 Portfolio Alerts", "📋 Audit Log", "🧑‍💼 For Investors",
     "🔎 Stock Screener", "💰 Taxation", "🔄 Swing", "🪙 Gold"]
)

# ---------------------------------------------------------------------------
# DASHBOARD TAB - calls tools directly (no LLM), so it's instant and free
# ---------------------------------------------------------------------------
with tab_dashboard:
    try:
        summary = get_portfolio_summary(selected_client_id)
        risk = calc_risk_score(selected_client_id)

        # --- AI Executive Summary: synthesis of real data, not new calculations ---
        st.markdown("### 🤖 AI Executive Summary")
        st.caption(
            "GPT-4o synthesizes real portfolio, risk, rebalancing, and profit-booking data "
            "into a readable brief — it does NOT calculate any of the underlying numbers itself."
        )

        if st.button("Generate Executive Summary", use_container_width=True):
            if check_query_budget():
                with st.spinner("Gathering real client data and generating summary..."):
                    exec_summary = generate_client_executive_summary(selected_client_id)
                st.session_state[f"exec_summary_{selected_client_id}"] = exec_summary
                log_event("executive_summary_generated", selected_client_id, {})

        exec_summary_key = f"exec_summary_{selected_client_id}"
        if exec_summary_key in st.session_state:
            exec_summary = st.session_state[exec_summary_key]
            st.info(exec_summary["summary_text"])
            with st.expander("📊 View the real underlying data used above"):
                st.json(exec_summary["raw_data"])

        st.markdown("---")

        st.caption(
            f"👤 Age {summary.get('age', '—')} · Goal: {summary.get('investment_goal', '—')} · "
            f"Horizon: {summary.get('time_horizon', '—')}"
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Portfolio Value", f"₹{summary['total_value']:,.2f}")

        gain_loss = summary["total_gain_loss"]
        gain_loss_pct = summary["total_gain_loss_pct"]
        col2.metric(
            "Unrealized Gain/Loss",
            f"₹{gain_loss:,.2f}",
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

        DONUT_COLORS = ["#0B1F4D", "#F5821F", "#2E6DB4", "#2ECC71", "#7FA8D9", "#E74C3C", "#95A5A6"]

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
            st.subheader("Fixed Deposits, Bonds & Government Schemes (incl. Gold via Sovereign Gold Bond)")
            other_df = pd.DataFrame(summary["other_investments"])
            st.dataframe(other_df, use_container_width=True, hide_index=True)
        else:
            st.caption("No FD/RD/Bond/government scheme holdings for this client.")

        # --- Historical Stress Test: "what if the market crashes?" (honest, backward-looking) ---
        st.markdown("---")
        st.subheader("📉 Historical Stress Test")
        st.caption(
            "Replays a REAL past market drawdown against this client's ACTUAL current "
            "holdings, using real historical prices — a backward-looking illustration, "
            "NOT a prediction that a similar event will happen again."
        )

        scenario_choice = st.selectbox("Historical scenario", list(STRESS_SCENARIOS.keys()), key="stress_scenario")

        if st.button("Run Stress Test", use_container_width=True):
            with st.spinner("Fetching real historical prices for this scenario..."):
                stress_result = run_stress_test(selected_client_id, scenario_choice)
            st.session_state.stress_result = stress_result
            log_event("stress_test_run", selected_client_id, {"scenario": scenario_choice})

        if "stress_result" in st.session_state:
            sr = st.session_state.stress_result
            if "error" in sr:
                st.warning(f"⚠️ {sr['error']}")
            else:
                s1, s2, s3 = st.columns(3)
                s1.metric("Current Value", f"₹{sr['current_total_value']:,.0f}")
                s2.metric("Stressed Value", f"₹{sr['stressed_total_value']:,.0f}")
                s3.metric(
                    "Drawdown", f"₹{sr['total_drawdown']:,.0f}",
                    f"{sr['total_drawdown_pct']:+.2f}%", delta_color="inverse"
                )
                st.caption(
                    f"Scenario period: {sr['scenario_period']} · Safe assets (FD/RD/Bonds/cash) of "
                    f"₹{sr['safe_assets_unaffected']:,.0f} assumed unaffected."
                )

                holdings_stress_df = pd.DataFrame(sr["holding_results"])
                st.dataframe(holdings_stress_df, use_container_width=True, hide_index=True)

                if sr.get("any_missing_data"):
                    st.caption("⚠️ Some holdings had no historical data available for this period and were assumed unchanged.")

                st.error(f"⚠️ {sr['disclaimer']}")

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
                st.caption(f"💡 Suggested action: {alert['suggested_action']}")
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

            # Show the reasoning trace for assistant messages
            if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                with st.expander("🧠 Agent's reasoning"):
                    for tc in msg.get("tool_calls", []):
                        st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                    if msg.get("memory_hits"):
                        st.markdown(f"- Used {msg['memory_hits']} relevant memory item(s) from past conversation")
                    if msg.get("latency_seconds") is not None:
                        st.caption(
                            f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                            f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                        )

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

        if not check_query_budget():
            st.stop()

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_agent(user_input, client_id=selected_client_id, verbose=False)
                    answer = result["answer"]
                    tool_calls = result["tool_calls"]
                    memory_hits = result["memory_hits"]
                    requires_approval = result["requires_approval"]
                    latency_seconds = result.get("latency_seconds")
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    approx_cost_usd = result.get("approx_cost_usd", 0)
                except Exception as e:
                    answer = f"⚠️ Something went wrong: {e}"
                    tool_calls = []
                    memory_hits = 0
                    requires_approval = False
                    latency_seconds = None
                    input_tokens = 0
                    output_tokens = 0
                    approx_cost_usd = 0
            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "tool_calls": tool_calls,
            "memory_hits": memory_hits,
            "requires_approval": requires_approval,
            "latency_seconds": latency_seconds,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "approx_cost_usd": approx_cost_usd,
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

# ---------------------------------------------------------------------------
# FOR INVESTORS TAB - self-service end-user experience, separate from the
# advisor-facing client tools above. No client_id needed - takes a generic
# investor's own age/amount/goal directly.
# ---------------------------------------------------------------------------
with tab_investor:
    st.subheader("Get Your Personalized Investment Guidance")
    st.caption(
        "This is educational, rule-based guidance — not personalized financial "
        "advice. It does not predict future returns and is not a substitute "
        "for a licensed financial advisor."
    )

    with st.form("investor_intake_form"):
        col_a, col_b = st.columns(2)
        investor_age = col_a.number_input("Your age", min_value=18, max_value=100, value=30, step=1)
        investment_amount = col_b.number_input(
            "Amount you want to invest (₹)", min_value=1000, value=100000, step=1000
        )

        col_c, col_d = st.columns(2)
        investor_goal = col_c.selectbox("Investment goal", VALID_GOALS)
        investor_horizon = col_d.selectbox("Time horizon (optional)", ["Let the guidance infer this"] + VALID_HORIZONS)

        submitted = st.form_submit_button("Get My Guidance", use_container_width=True)

    if submitted or "investor_guidance_result" in st.session_state:
        if submitted:
            horizon_arg = None if investor_horizon == "Let the guidance infer this" else investor_horizon
            guidance = get_investment_guidance(
                age=int(investor_age),
                investment_amount=float(investment_amount),
                goal=investor_goal,
                time_horizon=horizon_arg,
            )
            st.session_state.investor_guidance_result = guidance
            log_event("investor_guidance_generated", None, {
                "age": investor_age, "amount": investment_amount, "goal": investor_goal
            })

        guidance = st.session_state.investor_guidance_result

        st.markdown("---")
        risk_colors = {"Conservative": "🟢", "Moderate": "🟡", "Aggressive": "🔴"}
        st.markdown(
            f"### Your Risk Category: {risk_colors.get(guidance['risk_category'], '')} {guidance['risk_category']}"
        )
        st.caption(f"Based on age {guidance['age']}, goal: {guidance['goal']}, horizon: {guidance['time_horizon']}")

        alloc_col, factors_col = st.columns([2, 1])

        with alloc_col:
            st.markdown("**Suggested Asset Allocation**")
            fig = go.Figure(data=[go.Pie(
                labels=list(guidance["allocation_pct"].keys()),
                values=list(guidance["allocation_pct"].values()),
                hole=0.55,
                marker=dict(colors=DONUT_COLORS, line=dict(color="#FFFFFF", width=2)),
                textinfo="label+percent",
                textposition="outside",
            )])
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=320)
            st.plotly_chart(fig, use_container_width=True, key="investor_allocation_donut")

            alloc_table = pd.DataFrame([
                {"Asset Class": k, "Allocation %": v, "Amount (₹)": guidance["allocation_amount"][k]}
                for k, v in guidance["allocation_pct"].items()
            ])
            st.dataframe(alloc_table, use_container_width=True, hide_index=True)

        with factors_col:
            st.markdown("**Why this allocation?**")
            for factor in guidance["contributing_factors"]:
                st.markdown(f"- {factor}")

        st.info(f"ℹ️ {guidance['disclaimer']}")

        # --- AI Stock Suggestions by Sector (real data, AI-narrated) ---
        st.markdown("---")
        st.markdown("### 🤖 AI Stock Suggestions by Sector")
        st.warning(
            "⚠️ This is an AI-written summary of REAL, CURRENT market data (52-week "
            "high proximity, P/E, earnings growth) — organized by sector for your "
            "risk category. It is NOT a prediction of future performance."
        )

        if st.button("Get AI Sector-Wise Suggestions", use_container_width=True):
            if check_query_budget():
                with st.spinner("Screening real market data across all sectors..."):
                    sector_data = get_stock_screener_by_sector(guidance["risk_category"])
                with st.spinner("Generating AI summary from real data..."):
                    narrative = generate_sector_wise_suggestions(sector_data)
                st.session_state.sector_suggestions_narrative = narrative
                st.session_state.sector_suggestions_raw = sector_data
                log_event("sector_suggestions_generated", None, {"risk_category": guidance["risk_category"]})

        if "sector_suggestions_narrative" in st.session_state:
            st.markdown(st.session_state.sector_suggestions_narrative)
            with st.expander("📊 View the real underlying data used above"):
                raw = st.session_state.sector_suggestions_raw
                for sector, stocks in raw.get("sectors", {}).items():
                    st.markdown(f"**{sector}**")
                    sector_stocks_df = pd.DataFrame(stocks)
                    if not sector_stocks_df.empty:
                        sector_stocks_df["tags"] = sector_stocks_df["tags"].apply(
                            lambda t: ", ".join(t) if t else "—"
                        )
                        st.dataframe(sector_stocks_df, use_container_width=True, hide_index=True)
            st.caption(f"ℹ️ {raw.get('disclaimer', '')}")

        # --- Goal Gap Analysis: "am I on track?" ---
        st.markdown("---")
        st.markdown("### 🎯 Goal Gap Analysis — Am I On Track?")
        st.caption(
            "Projects your current corpus + planned monthly savings forward using a "
            "clearly-assumed average return for your risk category — NOT a prediction. "
            "Shows whether you're on track, and if not, how much more to save monthly."
        )

        goal_col1, goal_col2, goal_col3 = st.columns(3)
        goal_current_corpus = goal_col1.number_input(
            "Amount already saved toward this goal (₹)", min_value=0, value=int(guidance["investment_amount"]), step=10000
        )
        goal_monthly_contribution = goal_col2.number_input(
            "Planned monthly contribution (₹)", min_value=0, value=10000, step=1000
        )
        goal_target_amount = goal_col3.number_input(
            "Target amount needed (₹)", min_value=1, value=5000000, step=100000
        )
        goal_years = st.slider("Years until goal", min_value=1, max_value=40, value=15)

        if st.button("Check My Goal Gap", use_container_width=True):
            gap_result = calc_goal_gap(
                current_corpus=goal_current_corpus,
                monthly_contribution=goal_monthly_contribution,
                target_amount=goal_target_amount,
                years=goal_years,
                risk_category=guidance["risk_category"],
            )
            st.session_state.goal_gap_result = gap_result
            log_event("goal_gap_checked", None, {"risk_category": guidance["risk_category"], "years": goal_years})

        if "goal_gap_result" in st.session_state:
            gap = st.session_state.goal_gap_result
            g1, g2, g3 = st.columns(3)
            g1.metric("Projected Corpus", f"₹{gap['projected_corpus']:,.0f}")
            g2.metric("Target Amount", f"₹{gap['target_amount']:,.0f}")

            if gap["is_shortfall"]:
                g3.metric("Shortfall", f"₹{gap['gap']:,.0f}", delta="Behind", delta_color="inverse")
                st.error(
                    f"📉 Based on the assumption below, you're projected to fall short by "
                    f"₹{gap['gap']:,.0f}. To close this gap, consider increasing your monthly "
                    f"contribution by approximately **₹{gap['required_additional_monthly_sip']:,.0f}/month**."
                )
            else:
                g3.metric("Surplus", f"₹{gap['gap']:,.0f}", delta="On track", delta_color="normal")
                st.success(
                    f"📈 Based on the assumption below, you're projected to exceed your target "
                    f"by ₹{gap['gap']:,.0f} — currently on track."
                )

            st.warning(f"⚠️ {gap['disclaimer']}")

        # --- Historical performance lookback (real data, not a prediction) ---
        st.markdown("---")
        st.markdown("### Historical Performance Lookback (Real Data)")
        st.caption(
            "Past performance by real calendar year — shown as-is, NOT a forecast of future returns."
        )

        if "hist_search_symbol" not in st.session_state:
            st.session_state.hist_search_symbol = "TCS.NS"

        hist_col1, hist_col2 = st.columns([2, 1])
        selected_ticker = hist_col1.text_input(
            "Search any stock (e.g. TCS, INFY, RELIANCE, WIPRO — Indian exchange suffix auto-detected)",
            value=st.session_state.hist_search_symbol,
            key="hist_search_input",
        ).strip()
        hist_chart_type = hist_col2.radio("Chart type", ["Bar", "Line"], horizontal=True, key="hist_chart_type")

        st.caption("Quick picks:")
        quick_pick_cols = st.columns(6)
        quick_picks = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS", "HEROMOTOCO.NS", "SUNPHARMA.NS"]
        for i, qp in enumerate(quick_picks):
            if quick_pick_cols[i].button(qp, key=f"quickpick_{qp}", use_container_width=True):
                st.session_state.hist_search_symbol = qp
                st.rerun()

        if st.button("Show Historical Performance"):
            with st.spinner(f"Fetching real historical data for '{selected_ticker}'..."):
                hist_result = get_historical_returns(selected_ticker)

            if "error" in hist_result:
                st.warning(f"⚠️ {hist_result['error']}")
            else:
                resolved_note = (
                    f" (resolved to {hist_result['resolved_symbol']})"
                    if hist_result.get("resolved_symbol") and hist_result["resolved_symbol"] != selected_ticker
                    else ""
                )
                st.caption(
                    f"Current price: ₹{hist_result['current_price']:,.2f}{resolved_note} "
                    f"(as of {hist_result['as_of_date']})"
                )
                # Sort so years appear oldest-to-newest, left-to-right
                sorted_years = sorted(hist_result["returns"].keys())
                bar_labels = sorted_years
                bar_values = [hist_result["returns"][y]["return_pct"] for y in sorted_years]
                bar_colors = ["#2ECC71" if hist_result["returns"][y]["is_positive"] else "#E74C3C" for y in sorted_years]

                if hist_chart_type == "Bar":
                    hist_fig = go.Figure(data=[go.Bar(
                        x=bar_labels, y=bar_values,
                        marker=dict(color=bar_colors),
                        text=[f"{v:+.1f}%" for v in bar_values],
                        textposition="outside",
                    )])
                else:
                    hist_fig = go.Figure(data=[go.Scatter(
                        x=bar_labels, y=bar_values, mode="lines+markers+text",
                        line=dict(color="#0B1F4D", width=3),
                        marker=dict(size=10, color=bar_colors),
                        text=[f"{v:+.1f}%" for v in bar_values],
                        textposition="top center",
                    )])
                hist_fig.update_layout(
                    xaxis_title="Year", yaxis_title="Return %",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                )
                st.plotly_chart(hist_fig, use_container_width=True, key="historical_return_chart")

        # --- Flexible granularity price history (daily/weekly/monthly line chart) ---
        st.markdown("**Price History — Choose Your Own Zoom Level**")
        granularity = st.radio(
            "Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, key="price_history_granularity"
        )
        if st.button("Show Price History"):
            with st.spinner(f"Fetching real {granularity.lower()} price history..."):
                series_result = get_price_history_series(selected_ticker, granularity)

            if "error" in series_result:
                st.warning(f"⚠️ {series_result['error']}")
            else:
                price_fig = go.Figure(data=[go.Scatter(
                    x=series_result["dates"], y=series_result["prices"],
                    mode="lines", line=dict(color="#3498DB", width=2), fill="tozeroy",
                    fillcolor="rgba(52, 152, 219, 0.1)",
                )])
                price_fig.update_layout(
                    xaxis_title="Date", yaxis_title="Price (₹)",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                )
                st.plotly_chart(price_fig, use_container_width=True, key="price_history_line")
                st.caption(f"{granularity} closing price, {series_result['dates'][0]} to {series_result['dates'][-1]} — real historical data.")

        # --- Sector comparison (real data, today's performance) ---
        st.markdown("---")
        st.markdown("### Sector Comparison (Today's Real Performance)")
        st.caption("Compare how different sectors are performing today — helps spot where the current momentum is.")

        sector_chart_type = st.radio(
            "Chart type", ["Bar", "Pie (by magnitude of movement)"], horizontal=True, key="sector_chart_type"
        )

        if st.button("Compare Sectors"):
            with st.spinner("Fetching real sector index data..."):
                sector_result = get_sector_performance()

            if "error" in sector_result:
                st.warning(f"⚠️ {sector_result['error']}")
            else:
                perf = sector_result["sector_performance_pct"]
                sector_colors = ["#2ECC71" if v >= 0 else "#E74C3C" for v in perf.values()]

                if sector_chart_type == "Bar":
                    sector_fig = go.Figure(data=[go.Bar(
                        x=list(perf.keys()), y=list(perf.values()),
                        marker=dict(color=sector_colors),
                        text=[f"{v:+.2f}%" for v in perf.values()],
                        textposition="outside",
                    )])
                    sector_fig.update_layout(
                        yaxis_title="Today's Change %",
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=320,
                    )
                else:
                    # Pie sizes by magnitude of movement (abs value); color still
                    # reflects direction (green=up, red=down) via marker colors
                    sector_fig = go.Figure(data=[go.Pie(
                        labels=[f"{k} ({v:+.2f}%)" for k, v in perf.items()],
                        values=[abs(v) for v in perf.values()],
                        hole=0.5,
                        marker=dict(colors=sector_colors, line=dict(color="#FFFFFF", width=2)),
                        textinfo="label",
                    )])
                    sector_fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=380)
                    st.caption("Slice size = magnitude of today's move; green = up, red = down.")

                st.plotly_chart(sector_fig, use_container_width=True, key="sector_comparison_chart")

                if "best_performing_sector" in sector_result:
                    best = sector_result["best_performing_sector"]
                    worst = sector_result["worst_performing_sector"]
                    st.caption(
                        f"🟢 Best today: {best['sector']} ({best['change_pct']:+.2f}%)  |  "
                        f"🔴 Worst today: {worst['sector']} ({worst['change_pct']:+.2f}%)"
                    )

        # --- Individual report generation ---
        st.markdown("---")
        st.markdown("### Download Your Personalized Report")

        report_lines = [
            "PERSONALIZED INVESTMENT GUIDANCE REPORT",
            "=" * 50,
            "",
            f"Age: {guidance['age']}",
            f"Investment Amount: ₹{guidance['investment_amount']:,.2f}",
            f"Goal: {guidance['goal']}",
            f"Time Horizon: {guidance['time_horizon']}",
            f"Risk Category: {guidance['risk_category']}",
            "",
            "SUGGESTED ASSET ALLOCATION",
            "-" * 50,
        ]
        for k, v in guidance["allocation_pct"].items():
            report_lines.append(f"  {k}: {v}%  (₹{guidance['allocation_amount'][k]:,.2f})")
        report_lines += [
            "",
            "WHY THIS ALLOCATION",
            "-" * 50,
        ]
        for factor in guidance["contributing_factors"]:
            report_lines.append(f"  - {factor}")
        report_lines += [
            "",
            "IMPORTANT DISCLAIMER",
            "-" * 50,
            f"  {guidance['disclaimer']}",
        ]
        report_text = "\n".join(report_lines)

        if st.download_button(
            "📄 Download Report (.txt)",
            data=report_text,
            file_name=f"investment_guidance_report.txt",
            mime="text/plain",
        ):
            pass
        st.success("✅ Your personalized report is ready to download above.")

        # --- Ask questions about this guidance (investor-facing chat) ---
        st.markdown("---")
        st.markdown("### Ask Questions About Your Guidance")
        st.caption(
            "Ask anything about your allocation, a specific stock's real historical "
            "performance, or how sectors are doing today — answered using the same "
            "real data shown above, never a prediction."
        )

        if "investor_chat_messages" not in st.session_state:
            st.session_state.investor_chat_messages = []

        for msg in st.session_state.investor_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                    with st.expander("🧠 Reasoning"):
                        for tc in msg.get("tool_calls", []):
                            st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                        if msg.get("latency_seconds") is not None:
                            st.caption(
                                f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                                f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                            )

        investor_question = st.chat_input(
            "e.g. Why low P/E stocks for me? How has TCS done over 3 years?",
            key="investor_chat_input",
        )

        if investor_question:
            st.session_state.investor_chat_messages.append({"role": "user", "content": investor_question})
            with st.chat_message("user"):
                st.markdown(investor_question)

            if not check_query_budget():
                st.stop()

            # Give the agent context about this investor's own guidance, so
            # "why did you suggest this for me" resolves without re-asking
            context_note = (
                f"[Context: this investor is age {guidance['age']}, risk category "
                f"{guidance['risk_category']}, goal {guidance['goal']}, investing "
                f"₹{guidance['investment_amount']:,.0f}.] {investor_question}"
            )

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = run_agent(context_note, client_id=None, verbose=False)
                        answer = result["answer"]
                        tool_calls = result["tool_calls"]
                        latency_seconds = result.get("latency_seconds")
                        input_tokens = result.get("input_tokens", 0)
                        output_tokens = result.get("output_tokens", 0)
                        approx_cost_usd = result.get("approx_cost_usd", 0)
                    except Exception as e:
                        answer = f"⚠️ Something went wrong: {e}"
                        tool_calls = []
                        latency_seconds = None
                        input_tokens = 0
                        output_tokens = 0
                        approx_cost_usd = 0
                st.markdown(answer)

            st.session_state.investor_chat_messages.append({
                "role": "assistant", "content": answer, "tool_calls": tool_calls,
                "latency_seconds": latency_seconds, "input_tokens": input_tokens,
                "output_tokens": output_tokens, "approx_cost_usd": approx_cost_usd,
            })
            st.rerun()

# ---------------------------------------------------------------------------
# STOCK SCREENER TAB - real current data (52-week high proximity, P/E,
# earnings growth), personalized by risk category. NOT a prediction tool.
# ---------------------------------------------------------------------------
with tab_screener:
    st.subheader("Stock Screener — Real Current Data")
    st.caption(
        "⚠️ This shows REAL, CURRENT market data (as of today) — proximity to "
        "52-week highs, P/E valuation, recent earnings growth. It is NOT a "
        "prediction of future performance and does not guarantee any outcome."
    )

    # Auto-suggest risk category from investor guidance if already generated
    default_risk = "Moderate"
    if "investor_guidance_result" in st.session_state:
        default_risk = st.session_state.investor_guidance_result["risk_category"]
        st.info(f"ℹ️ Using your risk category from the 'For Investors' tab: **{default_risk}**")

    risk_options = ["Conservative", "Moderate", "Aggressive"]
    selected_risk = st.selectbox(
        "Risk category", risk_options, index=risk_options.index(default_risk)
    )

    # Sector interest intake — if the user picks none, we screen all sectors
    # automatically rather than blocking them (manual fallback, per request)
    available_sectors = sorted(set(SYMBOL_TO_SECTOR.values()))
    selected_sectors = st.multiselect(
        "Which sectors are you interested in? (optional — leave blank to screen all sectors)",
        available_sectors,
    )
    if not selected_sectors:
        st.caption("No preference selected — screening across ALL sectors automatically.")

    if st.button("Run Screener", use_container_width=True):
        with st.spinner("Fetching real current market data..."):
            screener_result = get_stock_screener(
                selected_risk, preferred_sectors=selected_sectors if selected_sectors else None
            )
        st.session_state.last_screener_result = screener_result

    if "last_screener_result" in st.session_state:
        screener_result = st.session_state.last_screener_result

        if "error" in screener_result:
            st.warning(f"⚠️ {screener_result['error']}")
        else:
            st.success(f"Showing results sorted for **{screener_result['risk_category']}** risk category")

            screener_df = pd.DataFrame(screener_result["results"])
            if not screener_df.empty:
                screener_df["tags"] = screener_df["tags"].apply(lambda t: ", ".join(t) if t else "—")
                display_cols = ["symbol", "sector", "company_name", "current_price",
                                 "pct_of_52wk_high", "pe_ratio", "earnings_growth_pct", "tags", "reason"]
                display_cols = [c for c in display_cols if c in screener_df.columns]
                st.dataframe(screener_df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.info("No stocks currently match — try again shortly.")

            st.caption(f"ℹ️ {screener_result['disclaimer']}")

        # --- The complete picture: stocks aren't the whole story ---
        st.markdown("---")
        st.markdown("### The Complete Picture: Beyond Stocks")
        st.caption(
            "A few stock ideas above, plus what every self-service investor should "
            "also know about safer instruments — general education, not advice tied "
            "to any specific product."
        )

        education = get_asset_education()
        edu_cols = st.columns(4)
        edu_icons = {"Fixed Deposit (FD)": "🏦", "Recurring Deposit (RD)": "🔄",
                     "Emergency Fund": "🛟", "Cash": "💵"}

        for i, (asset_name, content) in enumerate(education.items()):
            with edu_cols[i % 4]:
                st.markdown(f"#### {edu_icons.get(asset_name, '💰')} {asset_name}")
                st.caption(content["what_it_is"])
                with st.expander("Benefits"):
                    for b in content["benefits"]:
                        st.markdown(f"- {b}")
                with st.expander("Tradeoffs"):
                    for t in content["tradeoffs"]:
                        st.markdown(f"- {t}")


        st.markdown("---")
        st.markdown("### Hypothetical Growth Illustrator")
        st.warning(
            "⚠️ **This is NOT a prediction or forecast.** It illustrates what an investment "
            "might hypothetically look like IF a stock's real historical average annual "
            "return continued unchanged — it will not necessarily do so. Past performance "
            "is not indicative of future returns."
        )

        illus_col1, illus_col2, illus_col3, illus_col4 = st.columns(4)
        illus_symbol = illus_col1.selectbox(
            "Stock", ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS", "HEROMOTOCO.NS", "SUNPHARMA.NS"],
            key="illustrator_symbol",
        )
        illus_amount = illus_col2.number_input("Hypothetical amount (₹)", min_value=1000, value=100000, step=1000)
        illus_years = illus_col3.slider("Years", min_value=1, max_value=4, value=4)
        illus_chart_type = illus_col4.radio("Chart type", ["Bar", "Line"], horizontal=True, key="illus_chart_type")

        if st.button("Show Hypothetical Illustration"):
            with st.spinner("Calculating from real historical data..."):
                growth_result = get_hypothetical_growth(illus_symbol, illus_amount, illus_years)

            if "error" in growth_result:
                st.warning(f"⚠️ {growth_result['error']}")
            else:
                st.caption(
                    f"Based on {illus_symbol}'s real historical average annual return of "
                    f"{growth_result['avg_annual_return_pct']:+.2f}%/year"
                )

                # Keys are already real future calendar years (e.g. "2027") — sorted for display
                years_list = sorted(growth_result["yearly_projection"].keys())
                values_list = [growth_result["yearly_projection"][y] for y in years_list]
                bar_color = "#2ECC71" if growth_result["avg_annual_return_pct"] >= 0 else "#E74C3C"

                if illus_chart_type == "Bar":
                    growth_fig = go.Figure(data=[go.Bar(
                        x=years_list, y=values_list,
                        marker=dict(color=bar_color),
                        text=[f"₹{v:,.0f}" for v in values_list],
                        textposition="outside",
                    )])
                else:
                    growth_fig = go.Figure(data=[go.Scatter(
                        x=years_list, y=values_list, mode="lines+markers+text",
                        line=dict(color=bar_color, width=3),
                        marker=dict(size=10),
                        text=[f"₹{v:,.0f}" for v in values_list],
                        textposition="top center",
                    )])
                growth_fig.update_layout(
                    xaxis_title="Year", yaxis_title="Hypothetical Value (₹)",
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=320,
                )
                st.plotly_chart(growth_fig, use_container_width=True, key="growth_illustrator_chart")
                st.error(f"⚠️ {growth_result['disclaimer']}")

        # --- Screener-specific chat section ---
        st.markdown("---")
        st.markdown("### Ask Questions About These Results")
        st.caption("Ask about any stock or sector shown above — answered using real data, never a prediction.")

        if "screener_chat_messages" not in st.session_state:
            st.session_state.screener_chat_messages = []

        for msg in st.session_state.screener_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                    with st.expander("🧠 Reasoning"):
                        for tc in msg.get("tool_calls", []):
                            st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                        if msg.get("latency_seconds") is not None:
                            st.caption(
                                f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                                f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                            )

        screener_question = st.chat_input(
            "e.g. Why is TCS tagged Low P/E? How has it performed historically?",
            key="screener_chat_input",
        )

        if screener_question:
            st.session_state.screener_chat_messages.append({"role": "user", "content": screener_question})
            with st.chat_message("user"):
                st.markdown(screener_question)

            if not check_query_budget():
                st.stop()

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        result = run_agent(screener_question, client_id=None, verbose=False)
                        answer = result["answer"]
                        tool_calls = result["tool_calls"]
                        latency_seconds = result.get("latency_seconds")
                        input_tokens = result.get("input_tokens", 0)
                        output_tokens = result.get("output_tokens", 0)
                        approx_cost_usd = result.get("approx_cost_usd", 0)
                    except Exception as e:
                        answer = f"⚠️ Something went wrong: {e}"
                        tool_calls = []
                        latency_seconds = None
                        input_tokens = 0
                        output_tokens = 0
                        approx_cost_usd = 0
                st.markdown(answer)

            st.session_state.screener_chat_messages.append({
                "role": "assistant", "content": answer, "tool_calls": tool_calls,
                "latency_seconds": latency_seconds, "input_tokens": input_tokens,
                "output_tokens": output_tokens, "approx_cost_usd": approx_cost_usd,
            })
            st.rerun()

# ---------------------------------------------------------------------------
# TAXATION TAB - real, researched, dated tax rules (LTCG/STCG, Section 80C)
# with a chat section for follow-up questions. NOT a live feed - clearly
# labeled with a data_as_of date and a "verify with a CA" disclaimer,
# consistent with this project's honesty-first philosophy.
# ---------------------------------------------------------------------------
with tab_tax:
    st.subheader("💰 Taxation & Tax-Saving Guidance (India)")

    cg_data = get_capital_gains_rules()
    st.info(
        f"ℹ️ Data as of: **{cg_data['data_as_of']}**. This is a researched, dated "
        f"snapshot — NOT a live feed. {cg_data['disclaimer']}"
    )

    tax_col1, tax_col2 = st.columns(2)

    with tax_col1:
        st.markdown("### Capital Gains Tax Rules")
        for asset_type, rules in CAPITAL_GAINS_RULES.items():
            with st.expander(asset_type.replace("_", " ").title()):
                if "short_term_stcg" in rules:
                    st.markdown("**Short-Term (STCG)**")
                    st.markdown(f"- Holding period: {rules['short_term_stcg']['holding_period']}")
                    st.markdown(f"- Tax rate: {rules['short_term_stcg']['tax_rate']}")
                if "long_term_ltcg" in rules:
                    st.markdown("**Long-Term (LTCG)**")
                    st.markdown(f"- Holding period: {rules['long_term_ltcg']['holding_period']}")
                    st.markdown(f"- Tax rate: {rules['long_term_ltcg']['tax_rate']}")
                    if "annual_exemption" in rules["long_term_ltcg"]:
                        st.markdown(f"- Annual exemption: {rules['long_term_ltcg']['annual_exemption']}")
                if "note" in rules:
                    st.caption(f"ℹ️ {rules['note']}")

    with tax_col2:
        st.markdown("### Section 80C Tax-Saving Instruments")
        ts_data = get_tax_saving_instruments()["section_80c"]
        st.markdown(f"**Overall limit:** {ts_data['overall_limit']}")
        st.markdown(f"**Available only under:** {ts_data['available_only_under']}")
        st.markdown(
            f"**Additional deduction ({ts_data['additional_deduction']['section']}):** "
            f"{ts_data['additional_deduction']['amount']}"
        )
        st.markdown("---")
        instruments_df = pd.DataFrame(ts_data["instruments"])
        st.dataframe(instruments_df, use_container_width=True, hide_index=True)

    # --- Tax chat section ---
    st.markdown("---")
    st.markdown("### Ask a Tax Question")
    st.caption("e.g. \"How is ELSS taxed on exit?\", \"What's the LTCG rate on gold?\", \"How much can I save under 80C?\"")

    if "tax_chat_messages" not in st.session_state:
        st.session_state.tax_chat_messages = []

    for msg in st.session_state.tax_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                with st.expander("🧠 Reasoning"):
                    for tc in msg.get("tool_calls", []):
                        st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                    if msg.get("latency_seconds") is not None:
                        st.caption(
                            f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                            f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                        )

    tax_question = st.chat_input("Ask about capital gains tax, 80C, ELSS, PPF...", key="tax_chat_input")

    if tax_question:
        st.session_state.tax_chat_messages.append({"role": "user", "content": tax_question})
        with st.chat_message("user"):
            st.markdown(tax_question)

        if not check_query_budget():
            st.stop()

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_agent(tax_question, client_id=None, verbose=False)
                    answer = result["answer"]
                    tool_calls = result["tool_calls"]
                    latency_seconds = result.get("latency_seconds")
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    approx_cost_usd = result.get("approx_cost_usd", 0)
                except Exception as e:
                    answer = f"⚠️ Something went wrong: {e}"
                    tool_calls = []
                    latency_seconds = None
                    input_tokens = 0
                    output_tokens = 0
                    approx_cost_usd = 0
            st.markdown(answer)

        st.session_state.tax_chat_messages.append({
            "role": "assistant", "content": answer, "tool_calls": tool_calls,
            "latency_seconds": latency_seconds, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "approx_cost_usd": approx_cost_usd,
        })
        st.rerun()

# ---------------------------------------------------------------------------
# SWING TAB - real technical indicators, volume analysis, range position,
# and news for swing/short-term data screening. DELIBERATELY NO Buy/Sell
# signal, entry price, stop-loss, price target, or confidence score - no
# one can reliably predict short-term price direction, and fabricating
# that would be actively misleading. This is a data screener, not a
# trading-signal generator.
# ---------------------------------------------------------------------------
with tab_swing:
    # --- Pre-Market Briefing: real overnight global cues ---
    st.markdown("### 🌅 Pre-Market Briefing")
    st.caption(
        "Real, factual overnight global cues — what already happened while India was "
        "closed. This does NOT predict today's session or any specific stock."
    )

    if st.button("Get Pre-Market Briefing", use_container_width=True):
        with st.spinner("Fetching real overnight global market data..."):
            briefing = get_premarket_briefing()
        st.session_state.premarket_briefing = briefing
        log_event("premarket_briefing_fetched", None, {"data_fetched": briefing.get("data_fetched")})

    if "premarket_briefing" in st.session_state:
        pb = st.session_state.premarket_briefing
        if pb["items"]:
            pb_cols = st.columns(len(pb["items"]))
            for i, (label, data) in enumerate(pb["items"].items()):
                delta_color = "normal" if data["is_positive"] else "inverse"
                pb_cols[i].metric(label, f"{data['level']:,.2f}", f"{data['change_pct']:+.2f}%", delta_color=delta_color)
            if pb["data_fetched"] < pb["data_attempted"]:
                st.caption(f"ℹ️ Fetched {pb['data_fetched']} of {pb['data_attempted']} — some overnight data was unavailable.")
        else:
            st.warning("⚠️ Could not fetch overnight global data right now — try again shortly.")
        st.error(f"⚠️ {pb['disclaimer']}")

    st.markdown("---")
    st.subheader("🔄 Swing Screener — Real Technical & Volume Data")
    st.error(
        "⚠️ **This is NOT a Buy/Sell signal, price target, or trading recommendation.** "
        "No one — including professional quant funds — can reliably predict short-term "
        "price direction. This shows REAL, calculated technical indicators, volume "
        "activity, and news so you can apply your own judgment."
    )

    swing_symbol = st.text_input(
        "Search any stock (e.g. TCS, INFY, RELIANCE, or any real NSE ticker like CRAMC — auto-detects .NS/.BO)",
        value="TCS.NS", key="swing_search_input",
    ).strip()
    st.caption(
        "ℹ️ This search works for ANY real, currently-listed NSE/BSE stock — not limited to "
        "well-known names. The sector-wise screener further below, however, scans a fixed "
        "broad basket (~65 stocks), not literally every NSE-listed company (see note there)."
    )

    if st.button("Run Swing Analysis", use_container_width=True):
        with st.spinner("Calculating real technical indicators and volume data..."):
            swing_result = get_swing_analysis(swing_symbol)
        st.session_state.swing_result = swing_result
        log_event("swing_analysis_run", None, {"symbol": swing_symbol})

    if "swing_result" in st.session_state:
        sw = st.session_state.swing_result

        if "error" in sw:
            st.warning(f"⚠️ {sw['error']}")
        else:
            resolved_note = f" (resolved to {sw['resolved_symbol']})" if sw.get("resolved_symbol") != sw.get("symbol") else ""
            st.success(f"Current price: ₹{sw['current_price']:,.2f}{resolved_note}")

            # --- Today's Indicator Scoreboard (a FACTUAL TALLY, not a signal) ---
            tally = sw["indicator_tally"]
            st.markdown("### Today's Indicator Scoreboard")
            st.markdown(f"""
            <div style="display:flex; width:100%; height:34px; border-radius:8px; overflow:hidden; margin-bottom:6px;">
                <div style="width:{tally['bullish_pct']}%; background:#2ECC71; display:flex; align-items:center;
                            justify-content:center; color:white; font-size:0.9rem; font-weight:700;">
                    {tally['bullish_pct']}%
                </div>
                <div style="width:{tally['bearish_pct']}%; background:#E74C3C; display:flex; align-items:center;
                            justify-content:center; color:white; font-size:0.9rem; font-weight:700;">
                    {tally['bearish_pct']}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.error(
                f"⚠️ **This is a factual TALLY, NOT a Buy/Sell signal or confidence score.** "
                f"{tally['bullish_count']} of {tally['total_indicators']} real indicators "
                f"(RSI, MACD, EMA crossover, price vs. EMA20, Bollinger position) are currently "
                f"on the bullish-leaning side of their own neutral midpoint TODAY — this "
                f"describes right now, not what happens next. No one can reliably predict "
                f"short-term price direction."
            )

            # --- Technical Agent ---
            st.markdown("### 📈 Technical Indicators (Real, Calculated)")
            t = sw["technical"]

            def render_gauge(value, title, zones, key):
                """
                Color-zoned gauge for a 0-100 scaled indicator. Zones are
                textbook-standard definitions (e.g. RSI overbought/oversold),
                NOT a personalized signal for this specific stock — same
                factual framing as the rest of this tool.
                """
                if value is None:
                    st.caption(f"{title}: not available")
                    return
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=value,
                    title={"text": title},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#0B1F4D"},
                        "steps": zones,
                        "threshold": {
                            "line": {"color": "black", "width": 3},
                            "thickness": 0.8,
                            "value": value,
                        },
                    },
                ))
                fig.update_layout(height=220, margin=dict(t=40, b=10, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True, key=key)

            gcol1, gcol2 = st.columns(2)
            with gcol1:
                rsi_val = t["rsi_14"]
                render_gauge(
                    rsi_val, f"RSI (14) — {rsi_val}",
                    zones=[
                        {"range": [0, 30], "color": "#B7E4C7"},   # oversold zone (textbook "green")
                        {"range": [30, 70], "color": "#E0E0E0"},  # neutral zone
                        {"range": [70, 100], "color": "#F5B7B1"}, # overbought zone (textbook "red")
                    ],
                    key="rsi_gauge",
                )
                if rsi_val is not None:
                    green_pct = round(100 - rsi_val, 1)  # % of the scale BELOW current reading
                    red_pct = round(rsi_val, 1)           # % of the scale AT/ABOVE current reading
                    st.caption(
                        f"🟢 {green_pct}% of the 0-100 scale lies below this reading · "
                        f"🔴 {red_pct}% lies at/above it. Zones: 0-30 oversold (textbook), "
                        f"30-70 neutral, 70-100 overbought (textbook). This describes WHERE "
                        f"on the scale the value sits — NOT a signal for this specific stock."
                    )
            with gcol2:
                bb_pos = t["bollinger_bands"]["pct_position_in_bands"]
                render_gauge(
                    bb_pos, f"Bollinger Band Position — {bb_pos}%",
                    zones=[
                        {"range": [0, 20], "color": "#B7E4C7"},   # near lower band
                        {"range": [20, 80], "color": "#E0E0E0"},  # middle of the bands
                        {"range": [80, 100], "color": "#F5B7B1"}, # near upper band
                    ],
                    key="bollinger_gauge",
                )
                st.caption(
                    f"🟢 {round(bb_pos, 1)}% of the way from the lower band toward the upper "
                    f"band · 🔴 {round(100 - bb_pos, 1)}% of the range remains above. "
                    f"Zones: 0-20% near lower band, 20-80% mid-range, 80-100% near upper band. "
                    f"Factual position within the bands, not a signal."
                )

            tcol2, tcol3, tcol4 = st.columns(3)
            tcol2.metric("ADX (14)", t["adx_14"])
            tcol2.caption("Trend STRENGTH (not direction). >25 conventionally = trending market")
            tcol3.metric("ATR (14)", t["atr_14"])
            tcol3.caption("Average daily price range — a volatility measure")
            tcol4.metric("MACD Histogram", t["macd"]["histogram"])
            tcol4.caption(f"MACD {'above' if t['macd']['macd_above_signal'] else 'below'} signal line (factual state)")

            ecol1, ecol2, ecol3 = st.columns(3)
            ecol1.metric("EMA 20", t["ema_status"]["ema20"])
            ecol2.metric("EMA 50", t["ema_status"]["ema50"])
            ecol3.metric(
                "EMA20 vs EMA50",
                "20 above 50" if t["ema_status"]["ema20_above_ema50"] else "20 below 50",
            )

            st.markdown("**Bollinger Bands (20, 2σ)**")
            bb = t["bollinger_bands"]
            bcol1, bcol2, bcol3 = st.columns(3)
            bcol1.metric("Lower Band", bb["lower_band"])
            bcol2.metric("Middle (SMA20)", bb["middle_band"])
            bcol3.metric("Upper Band", bb["upper_band"])

            # --- Volume Agent ---
            st.markdown("---")
            st.markdown("### 📊 Volume Analysis (Real)")
            v = sw["volume"]
            vcol1, vcol2, vcol3 = st.columns(3)
            vcol1.metric("Today's Volume", f"{v['current_volume']:,}")
            vcol2.metric("Prior 20-Day Avg", f"{v['avg_volume_20d_prior']:,}" if v['avg_volume_20d_prior'] else "—")
            vcol3.metric(
                "Volume Spike Ratio", f"{v['volume_spike_ratio']}x" if v['volume_spike_ratio'] else "—",
                "🔥 High Volume" if v["is_high_volume"] else "Normal",
            )

            # --- Pattern/Range Agent ---
            st.markdown("---")
            st.markdown("### 📐 Price Range Position (Real, Factual)")
            rp = sw["range_position"]
            rcol1, rcol2, rcol3 = st.columns(3)
            rcol1.metric("% From 20-Day High", f"{rp['pct_from_20d_high']:+.2f}%")
            rcol2.metric("% From 20-Day Low", f"{rp['pct_from_20d_low']:+.2f}%")
            rcol3.metric("% From 50-Day High", f"{rp['pct_from_50d_high']:+.2f}%")
            if rp["at_20d_high"]:
                st.caption("📍 Currently at or near its 20-day high (factual observation, not a breakout prediction)")

            # --- News Agent ---
            if sw.get("recent_headlines"):
                st.markdown("---")
                st.markdown("### 📰 Recent News (Real)")
                for headline in sw["recent_headlines"]:
                    st.markdown(f"- {headline}")

            st.markdown("---")
            st.error(f"⚠️ {sw['disclaimer']}")

    # --- Sector-Wise Swing Screener (batch, real data across the universe) ---
    st.markdown("---")
    st.markdown("### 📋 Sector-Wise Swing Screener — High Volume & Near-High Stocks")
    st.error(
        "⚠️ **Still NOT a breakout prediction or Buy/Sell signal.** These stocks show "
        "REAL, CURRENT high volume and/or proximity to their 20-day high — a factual "
        "snapshot of today only. Whether a real breakout follows cannot be predicted."
    )

    if st.button("Run Full Sector-Wise Screener", use_container_width=True):
        with st.spinner("Scanning the real stock universe (this takes a moment)..."):
            batch_result = get_swing_screener_by_sector()
        st.session_state.swing_batch_result = batch_result
        log_event("swing_sector_screener_run", None, {"total_flagged": batch_result.get("total_flagged")})

    if "swing_batch_result" in st.session_state:
        br = st.session_state.swing_batch_result

        if "error" in br:
            st.warning(f"⚠️ {br['error']}")
        else:
            st.success(
                f"{br['total_flagged']} of {br['universe_size']} stocks currently flagged "
                f"(high volume, near 20-day high, strong trend, or above both EMAs)."
            )

            if not br["sectors"]:
                st.info("No stocks currently match — this reflects real current market conditions, try again shortly.")
            else:
                # --- Compact view: just the symbols, grouped by sector ---
                st.markdown("**Quick list — flagged stocks by sector:**")
                for sector, stocks in br["sectors"].items():
                    symbols = ", ".join(s["symbol"] for s in stocks)
                    st.markdown(f"- **{sector}**: {symbols}")

                st.markdown("---")
                st.markdown("**Full detail:**")
                for sector, stocks in br["sectors"].items():
                    st.markdown(f"**{sector}**")
                    sector_df = pd.DataFrame(stocks)
                    sector_df["flags"] = sector_df["flags"].apply(lambda f: ", ".join(f) if f else "—")
                    display_cols = ["symbol", "current_price", "rsi_14", "adx_14",
                                     "volume_spike_ratio", "pct_from_20d_high", "flags"]
                    display_cols = [c for c in display_cols if c in sector_df.columns]
                    st.dataframe(sector_df[display_cols], use_container_width=True, hide_index=True)

            st.caption(f"ℹ️ {br['disclaimer']}")

    # --- Experimental: NSE Live All-Exchange Volume Feed ---
    st.markdown("---")
    st.markdown("### 🧪 Experimental: Live NSE Volume Feed (ALL of NSE, not a fixed list)")
    st.warning(
        "⚠️ **Experimental** — this attempts to fetch NSE's own live 'Most Active by "
        "Volume' data directly, covering the ENTIRE exchange (not the ~65-stock list "
        "above). This depends on NSE's unofficial public data feed and may not always "
        "work — if it fails, the Sector-Wise Screener above is the reliable option, or "
        "search any specific stock symbol directly (works for any real NSE/BSE ticker)."
    )

    if st.button("Try Live NSE Feed (All Exchange)", use_container_width=True):
        with st.spinner("Attempting to fetch NSE's live volume feed..."):
            nse_result = get_nse_most_active_by_volume(20)
        st.session_state.nse_result = nse_result

    if "nse_result" in st.session_state:
        nr = st.session_state.nse_result
        if "error" in nr:
            st.error(f"⚠️ {nr['error']}")
        else:
            st.success(f"Fetched {len(nr['stocks'])} stocks from {nr['source']}")
            nse_df = pd.DataFrame(nr["stocks"])
            st.dataframe(nse_df, use_container_width=True, hide_index=True)
            st.caption(f"ℹ️ {nr['disclaimer']}")

    # --- Swing chat section ---
    st.markdown("---")
    st.markdown("### Ask About This Stock's Data")
    st.caption("e.g. \"Is this stock overbought?\", \"What does the volume spike mean?\" — answered from real data, never a signal.")

    if "swing_chat_messages" not in st.session_state:
        st.session_state.swing_chat_messages = []

    for msg in st.session_state.swing_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                with st.expander("🧠 Reasoning"):
                    for tc in msg.get("tool_calls", []):
                        st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                    if msg.get("latency_seconds") is not None:
                        st.caption(
                            f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                            f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                        )

    swing_question = st.chat_input("Ask about technical indicators, volume, or news for this stock...", key="swing_chat_input")

    if swing_question:
        st.session_state.swing_chat_messages.append({"role": "user", "content": swing_question})
        with st.chat_message("user"):
            st.markdown(swing_question)

        if not check_query_budget():
            st.stop()

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_agent(swing_question, client_id=None, verbose=False)
                    answer = result["answer"]
                    tool_calls = result["tool_calls"]
                    latency_seconds = result.get("latency_seconds")
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    approx_cost_usd = result.get("approx_cost_usd", 0)
                except Exception as e:
                    answer = f"⚠️ Something went wrong: {e}"
                    tool_calls = []
                    latency_seconds = None
                    input_tokens = 0
                    output_tokens = 0
                    approx_cost_usd = 0
            st.markdown(answer)

        st.session_state.swing_chat_messages.append({
            "role": "assistant", "content": answer, "tool_calls": tool_calls,
            "latency_seconds": latency_seconds, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "approx_cost_usd": approx_cost_usd,
        })
        st.rerun()

# ---------------------------------------------------------------------------
# GOLD TAB - real gold price, real technical indicators (reusing the same
# tested functions as the Swing tab), real historical change, and real
# Sovereign Gold Bond facts. DELIBERATELY NO buy/sell price target, no
# "AI predicts" signal, no specific entry/exit level - same honesty
# pattern as the rest of this project.
# ---------------------------------------------------------------------------
with tab_gold:
    st.subheader("🪙 Gold Analysis — Real Price & Technical Data")
    st.error(
        "⚠️ **This is NOT a buy/sell price target or prediction.** No one can reliably "
        "predict gold's future price. This shows REAL current price, real technical "
        "indicators, and real historical change so you can apply your own judgment."
    )

    if st.button("Get Gold Analysis", use_container_width=True):
        with st.spinner("Fetching real gold price and calculating indicators..."):
            gold_result = get_gold_analysis()
        st.session_state.gold_result = gold_result
        log_event("gold_analysis_run", None, {})

    if "gold_result" in st.session_state:
        g = st.session_state.gold_result

        if "error" in g:
            st.warning(f"⚠️ {g['error']}")
        else:
            gcol1, gcol2 = st.columns(2)
            gcol1.metric("Gold Price (USD/oz)", f"${g['current_price_usd_per_oz']:,.2f}")
            if g["current_price_inr_per_10g_approx"]:
                gcol2.metric("Approx. INR/10g", f"₹{g['current_price_inr_per_10g_approx']:,.2f}")
                gcol2.caption("Approximate conversion — excludes import duty, GST, dealer premiums")

            # --- Today's Indicator Scoreboard (same honest tally as Swing) ---
            tally = g["indicator_tally"]
            st.markdown("### Today's Indicator Scoreboard")
            st.markdown(f"""
            <div style="display:flex; width:100%; height:34px; border-radius:8px; overflow:hidden; margin-bottom:6px;">
                <div style="width:{tally['bullish_pct']}%; background:#2ECC71; display:flex; align-items:center;
                            justify-content:center; color:white; font-size:0.9rem; font-weight:700;">
                    {tally['bullish_pct']}%
                </div>
                <div style="width:{tally['bearish_pct']}%; background:#E74C3C; display:flex; align-items:center;
                            justify-content:center; color:white; font-size:0.9rem; font-weight:700;">
                    {tally['bearish_pct']}%
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.error(
                f"⚠️ **Factual TALLY, NOT a Buy/Sell signal.** {tally['bullish_count']} of "
                f"{tally['total_indicators']} real indicators are currently bullish-leaning "
                f"TODAY — describes right now, not what happens next."
            )

            # --- Real technical indicators ---
            st.markdown("### 📈 Technical Indicators (Real, Calculated)")
            t = g["technical"]
            tcol1, tcol2, tcol3 = st.columns(3)
            tcol1.metric("RSI (14)", t["rsi_14"])
            tcol2.metric("ADX (14)", t["adx_14"])
            tcol3.metric("ATR (14)", t["atr_14"])

            ecol1, ecol2, ecol3 = st.columns(3)
            ecol1.metric("EMA 20", t["ema_status"]["ema20"])
            ecol2.metric("EMA 50", t["ema_status"]["ema50"])
            ecol3.metric("EMA20 vs EMA50", "20 above 50" if t["ema_status"]["ema20_above_ema50"] else "20 below 50")

            # --- Real historical change ---
            st.markdown("### 📊 Historical Change (Real, Backward-Looking)")
            hc = g["historical_change_pct"]
            hcol1, hcol2, hcol3 = st.columns(3)
            hcol1.metric("1 Month", f"{hc['1_month']:+.2f}%")
            hcol2.metric("3 Months", f"{hc['3_month']:+.2f}%")
            hcol3.metric("6 Months", f"{hc['6_month']:+.2f}%")

            # --- Sovereign Gold Bond facts ---
            st.markdown("---")
            st.markdown("### 🏛️ Sovereign Gold Bond (SGB) — Real Facts")
            sgb = g["sgb_facts"]
            st.caption(sgb["what_it_is"])
            sgcol1, sgcol2 = st.columns(2)
            with sgcol1:
                st.markdown("**Benefits**")
                for b in sgb["benefits"]:
                    st.markdown(f"- {b}")
            with sgcol2:
                st.markdown("**Tradeoffs**")
                for tr in sgb["tradeoffs"]:
                    st.markdown(f"- {tr}")

            st.markdown("---")
            st.error(f"⚠️ {g['disclaimer']}")

    # --- Gold chat section ---
    st.markdown("---")
    st.markdown("### Ask About Gold")
    st.caption("e.g. \"Is gold overbought right now?\", \"What are SGB tax benefits?\" — answered from real data, never a price target.")

    if "gold_chat_messages" not in st.session_state:
        st.session_state.gold_chat_messages = []

    for msg in st.session_state.gold_chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and (msg.get("tool_calls") or msg.get("latency_seconds") is not None):
                with st.expander("🧠 Reasoning"):
                    for tc in msg.get("tool_calls", []):
                        st.markdown(f"- Called `{tc['name']}` with `{tc['args']}`")
                    if msg.get("latency_seconds") is not None:
                        st.caption(
                            f"⏱️ {msg['latency_seconds']}s · 🔢 {msg.get('input_tokens', 0)}+{msg.get('output_tokens', 0)} tokens "
                            f"· 💵 ~${msg.get('approx_cost_usd', 0):.5f}"
                        )

    gold_question = st.chat_input("Ask about gold prices, indicators, or SGB...", key="gold_chat_input")

    if gold_question:
        st.session_state.gold_chat_messages.append({"role": "user", "content": gold_question})
        with st.chat_message("user"):
            st.markdown(gold_question)

        if not check_query_budget():
            st.stop()

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = run_agent(gold_question, client_id=None, verbose=False)
                    answer = result["answer"]
                    tool_calls = result["tool_calls"]
                    latency_seconds = result.get("latency_seconds")
                    input_tokens = result.get("input_tokens", 0)
                    output_tokens = result.get("output_tokens", 0)
                    approx_cost_usd = result.get("approx_cost_usd", 0)
                except Exception as e:
                    answer = f"⚠️ Something went wrong: {e}"
                    tool_calls = []
                    latency_seconds = None
                    input_tokens = 0
                    output_tokens = 0
                    approx_cost_usd = 0
            st.markdown(answer)

        st.session_state.gold_chat_messages.append({
            "role": "assistant", "content": answer, "tool_calls": tool_calls,
            "latency_seconds": latency_seconds, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "approx_cost_usd": approx_cost_usd,
        })
        st.rerun()
