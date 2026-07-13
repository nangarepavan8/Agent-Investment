# Where AI/Agent Is Used — Presentation Reference

## The core idea to lead with

This project deliberately uses AI (GPT-4o) **only where reasoning is
genuinely needed** — deciding which tool fits a question, and turning
structured data into readable language. Every calculation itself
(risk scores, tax math, gain/loss, historical replays) is **plain,
deterministic Python** — no AI, no hallucination risk, 100% auditable.

**This is the single strongest architecture point to make to judges:**
"AI decides *what* to do; code decides *the numbers*." That split is
exactly why the agent can be trusted with financial calculations.

---

## 1. Where GPT-4o (the Agent) is actually invoked — 2 places in the code

### A. `run_agent()` — the core agentic loop
**File:** `src/agent.py`

This is "the Agent." Given a natural-language question, GPT-4o:
1. Reads the question + the docstrings of all 14 available tools
2. Decides which tool(s) apply (can call more than one per question)
3. Executes those tools against real data
4. Synthesizes the results into a natural-language answer

**Used in 4 places in the UI** (each is a separate chat, same underlying agent):
| Chat surface | Tab |
|---|---|
| Advisor Chat | 💬 Chat |
| Investor Chat | 🧑‍💼 For Investors |
| Screener Chat | 🔎 Stock Screener |
| Tax Chat | 💰 Taxation |

### B. `generate_sector_wise_suggestions()` — narrative synthesis
**File:** `src/agent.py`

A second, simpler GPT-4o call (no tool-calling, just writing) that takes
already-fetched real screener data and writes a 2-3 sentence, per-sector
summary — used by the **"🤖 AI Stock Suggestions by Sector"** button in
"For Investors."

**That's it — those are the only two places an LLM is called anywhere
in this codebase.** Everything else described below is deterministic.

---

## 2. The 14 Tools GPT-4o can choose to call

*(This is the actual "agentic" surface — the reasoning is in **which**
tool gets picked, not in the tool's internal math.)*

| # | Tool | What it does (deterministic) | Example question that triggers it |
|---|---|---|---|
| 1 | `portfolio_summary_tool` | Real-time value across ALL assets (stocks, FD, RD, bonds, schemes, cash) | "What's this portfolio worth?" |
| 2 | `risk_score_tool` | 0-100 score: sector/position concentration, risk profile, safe-asset offset | "How risky is this portfolio?" |
| 3 | `rebalancing_tool` | Sector rebalancing vs. equal-weight target | "How should we rebalance?" |
| 4 | `profit_booking_tool` | **Tax-aware** gain/loss flagging with real STCG/LTCG treatment | "Which stocks should I book profit on?" |
| 5 | `market_context_tool` | Live price, fundamentals, analyst view, news sentiment for any stock | "Should I invest in TCS?" |
| 6 | `sector_performance_tool` | Real, live Nifty sector index performance | "How's the IT sector doing today?" |
| 7 | `investment_guidance_tool` | Age/amount/goal → risk profile & allocation (self-service) | "I'm 30, want to invest ₹2L, what allocation?" |
| 8 | `historical_performance_tool` | Real 1/2/3-year past returns (backward-looking only) | "How has TCS performed over 3 years?" |
| 9 | `stock_screener_tool` | Real current data (52-wk high, P/E, earnings growth) by risk category | "Give me stock ideas for my risk level" |
| 10 | `growth_illustrator_tool` | Hypothetical projection from real historical average (labeled, not a forecast) | "Show me a growth illustration for INFY" |
| 11 | `goal_gap_analysis_tool` | Projects corpus + SIP forward, real annuity math, shows shortfall/surplus | "Will I have ₹50L in 15 years?" |
| 12 | `capital_gains_tax_tool` | Real, researched LTCG/STCG tax rates (dated snapshot) | "What's the tax on equity LTCG?" |
| 13 | `tax_saving_instruments_tool` | Real Section 80C instrument details | "How can I save tax under 80C?" |
| 14 | `stress_test_tool` | Replays REAL historical crashes (2020/2022) against current holdings | "What if the market crashes?" |

---

## 3. Memory — the "remembers context" part of Agentic AI

**File:** `src/memory.py` (ChromaDB vector store)

Every exchange is stored per-client. On a new question, relevant past
exchanges are retrieved and given to GPT-4o as context — this is why
"how should we rebalance **it**?" works without re-specifying the client.
This is the one piece of genuine ML (embeddings/vector similarity)
outside the LLM calls themselves.

---

## 4. What is explicitly NOT AI (deterministic, and why that's a feature)

| Component | Why it's deliberately NOT AI |
|---|---|
| Dashboard tab metrics | Calls tools directly, bypassing the LLM — instant, free, no latency |
| Portfolio Alerts (proactive scan) | Pure Python risk-scan across all 10 clients — no AI needed for "is this number > threshold" |
| All tax/risk/gain math | Precision matters — an LLM should never be doing arithmetic that could hallucinate |
| Historical stress-test numbers | Real historical prices replayed exactly — a calculation, not a generation |

**Presentation line that works well here:** *"We don't use AI to do
math. We use AI to decide which math to run, and to explain the
result in plain English."*

---

## 5. Responsible-AI guardrails baked into the Agent (worth a slide)

- **Never predicts future prices** — `market_context_tool`,
  `historical_performance_tool`, `growth_illustrator_tool` all
  explicitly forbid forward-looking claims in the system prompt
- **Human-in-the-loop approval** — rebalancing and profit-booking
  suggestions require explicit advisor approval before being
  "actioned" in the UI
- **Every tax/assumption figure is labeled** — "this is an assumption
  for planning, not a guarantee" repeated in the system prompt rules
- **Audit trail** — every tool call and approval decision is logged
  with a timestamp (`src/audit_log.py`)

---

## Quick one-liner summary (for a slide or verbal intro)

> "GPT-4o acts as the reasoning layer — deciding which of 14
> specialized tools fits a question and writing the final answer in
> plain English. Every number those tools return comes from
> deterministic Python: real market data, real tax rules, real
> historical prices — never generated or guessed by the model."
