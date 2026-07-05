# Agentic Investment Research Assistant

TVS Next InnovAIte 2026 — Hackathon Project

An AI agent that routes natural-language financial queries to
specialized tools (portfolio summary, risk scoring, rebalancing,
market context) using GPT-4o, with persistent per-client memory via
ChromaDB.

## Day 1 Setup

1. **Clone this repo / unzip the project**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and paste your real OpenAI API key in place of
   `sk-your-key-here`. Get a key at https://platform.openai.com/api-keys
   (requires a funded OpenAI account — a few dollars is plenty for
   this whole project).

5. **Test the connection**
   ```bash
   python tests/test_gpt4o_connection.py
   ```
   You should see a short GPT-4o response printed to your terminal.
   If this works, Day 1 is done.

## Project Structure

```
agentic-investment-assistant/
├── README.md
├── requirements.txt
├── .env.example          # copy to .env, never commit .env
├── .gitignore
├── src/
│   ├── config.py         # loads API key + model name
│   └── tools/
│       ├── portfolio_summary.py   # Tool 1 (stub — Day 3)
│       ├── risk_score.py          # Tool 2 (stub — Day 3)
│       ├── rebalancing.py         # Tool 3 (stub — Day 3)
│       └── market_context.py      # Tool 4 (stub — Day 3)
├── data/                 # synthetic dataset goes here (Day 2)
└── tests/
    └── test_gpt4o_connection.py   # Day 1 connectivity check
```

## Day 2: Synthetic Dataset

Run the generator once to create your data files:
```bash
python data/generate_data.py
```

This creates:
- `data/clients.csv` — 10 fictional clients: `client_id`, `name`, `risk_profile` (Conservative/Moderate/Aggressive)
- `data/holdings.csv` — each client's stock holdings: `client_id`, `symbol`, `sector`, `quantity`, `purchase_price`

Uses real public stock tickers (AAPL, MSFT, JPM, etc.) so the market
context tool can pull live prices via yfinance later — but all client
names and account data are 100% fictional, generated locally.

Re-run the script anytime to regenerate (fixed random seed = same data every time).

## Day 3: Tool Implementation

All 4 tools are now fully implemented against the synthetic dataset:

- `get_portfolio_summary(client_id)` — total value, holdings, sector allocation
- `calc_risk_score(client_id)` — 0-100 score based on sector concentration, single-position concentration, and stated risk profile
- `suggest_rebalancing(client_id)` — rule-based rebalancing suggestions vs. equal-weight target
- `get_market_context(symbol)` — live public price data via yfinance (requires internet)

Test everything at once:
```bash
python tests/test_all_tools.py
```

Or test one tool individually:
```bash
python -m src.tools.portfolio_summary
python -m src.tools.risk_score
python -m src.tools.rebalancing
python -m src.tools.market_context
```

Valid client IDs are `CLIENT_001` through `CLIENT_010` (see `data/clients.csv`).

## Day 4: The Agent (LangChain + GPT-4o Function-Calling)

`src/agent.py` is the core of the project. It wraps all 4 tools with
LangChain's `@tool` decorator and lets GPT-4o decide which tool(s) to
call based on the user's natural-language query — this is the actual
"agentic" behavior the hackathon is judging.

How it works:
1. User asks a question in plain English
2. GPT-4o reads the question + each tool's docstring, decides which
   tool(s) apply
3. The agent executes those tools against your real synthetic data
4. GPT-4o synthesizes the tool output into a clear, advisor-friendly answer

Test it:
```bash
python tests/test_agent.py
```

This runs 5 sample queries, including one that should trigger **two
tools in a single query** (risk score + rebalancing) — that's the
clearest way to demonstrate multi-step agentic reasoning to judges.

Quick single-query test:
```bash
python -m src.agent
```

**What to check when you run it:**
- Does each query call the tool you'd expect? (printed as `🔧 Agent is calling: ...`)
- Does the multi-tool query (test 5) call both `risk_score_tool` AND `rebalancing_tool`?
- Is the final answer readable prose, not raw JSON dumped at you?

If a query calls the wrong tool, the fix is almost always to make that
tool's docstring in `src/agent.py` more specific — GPT-4o routes based
on those descriptions.

## Day 6: Vector Memory (ChromaDB)

`src/memory.py` adds persistent, per-client memory so the agent
remembers past exchanges instead of treating every question as brand
new. This is what makes follow-up questions work — e.g. "how should
we rebalance **it**?" after a risk question, without re-specifying
the client.

How it's wired into the agent (`src/agent.py`):
1. Before answering, the agent retrieves relevant past exchanges for
   that specific `client_id`
2. That context gets added to the system prompt so GPT-4o can use it
3. After answering, the new exchange gets stored for future turns

**⚠️ Test this today, not on demo day:** ChromaDB downloads a small
embedding model (~80MB) from `huggingface.co` the first time it runs.
If your company network blocks that domain, the download will fail.
Run the test below now — if it fails, try once from home wifi or a
personal hotspot to let it download and cache (only needs to happen
once; it's cached locally after that).

Test memory in isolation (no OpenAI calls, no cost):
```bash
python tests/test_memory.py
```

Test memory working inside a real conversation (uses your API key):
```bash
python -m src.agent
```
This runs two queries back-to-back — the second one ("rebalance **it**")
should correctly understand "it" refers to CLIENT_001's portfolio from
the first query, using retrieved memory context.

## Day 7: Streamlit Chat UI

`app.py` is the demo-facing front end. Run it with:
```bash
streamlit run app.py
```
It should open automatically in your browser at `http://localhost:8501`.

**What it does:**
- Sidebar lets you pick which synthetic client you're asking about (CLIENT_001-010)
- Main area is a chat interface — type a question, the agent responds
- Suggested example questions are listed in the sidebar for quick demo use
- "Clear conversation" button resets the visible chat (note: ChromaDB
  memory persists in the background regardless — this button only
  clears what's shown on screen)

**Try this flow to test memory + multi-tool routing together:**
1. Pick a client (e.g. CLIENT_001)
2. Ask: "How risky is this portfolio?"
3. Ask: "How should we rebalance it?" — should correctly use "it" =
   the same portfolio, and pull the risk context from memory
4. Ask: "What's the current price of AAPL?" — tests the market-data tool

If anything errors in the chat, the app will show it inline (⚠️) rather
than crashing — check your `.env` API key and internet connection first.

## Day 8: Dashboard View

`app.py` now has two tabs:
- **💬 Chat** — the conversational agent (from Day 7)
- **📊 Dashboard** — visual view of the selected client's portfolio

The dashboard shows:
- Total portfolio value, risk score (with color-coded 🟢🟡🔴), and holdings count as headline metrics
- A sector allocation bar chart
- The specific risk factors driving the score (same explanations the chat agent uses)
- A full holdings table

**Important design choice:** the dashboard calls `get_portfolio_summary()`
and `calc_risk_score()` **directly** — it does NOT go through GPT-4o.
This means the dashboard is instant and free (no API cost, no latency)
every time you switch clients, while the chat tab is where the actual
LLM reasoning happens. This is worth mentioning to judges: it shows you
understood which parts of the system need "agentic" reasoning
(natural language routing) versus which parts are just deterministic
data display (no LLM needed, faster and cheaper).

Run it:
```bash
streamlit run app.py
```
Switch between the two tabs, and switch clients in the sidebar to see
the dashboard update instantly.

## Day 9: Full Run-Through & Bug Fixing

**A real bug was found and fixed today:** previously, if GPT-4o called a
tool with an invalid `client_id` (e.g. a judge asks about a client that
doesn't exist, or mistypes one), the tool raised an uncaught error and
crashed the entire response. All 4 tools now catch errors internally
and return a graceful `{"error": "..."}` message that GPT-4o reads and
explains in plain language instead of crashing.

Run the full test suite (covers happy paths, multi-tool queries,
memory follow-ups, AND edge cases that should not crash):
```bash
python tests/test_day9_full_runthrough.py
```

**What to check in the output:**
- [ ] Every "happy path" query calls the tool you'd expect
- [ ] Multi-tool queries call BOTH tools, not just one
- [ ] The memory follow-up ("rebalance **it**") correctly resolves context
- [ ] Edge cases (invalid client, invalid symbol, off-topic, empty query) return a **graceful message**, not a crash
- [ ] All answers are clear prose — no raw JSON leaking through

**Also test the Streamlit app itself end-to-end:**
```bash
streamlit run app.py
```
- [ ] Switch between all 10 clients in the sidebar — dashboard updates correctly each time
- [ ] Ask a question about a client, then switch clients and ask again — no cross-contamination
- [ ] Try an intentionally bad question (e.g. "tell me about CLIENT_999") — confirm it doesn't crash the UI
- [ ] Note response times — if GPT-4o calls feel slow, that's normal for a first request; subsequent ones should be faster

**If you find a query that still breaks something**, the fix is one of:
1. Tighten that tool's docstring in `src/agent.py` if it's a routing problem
2. Add a similar try/except if it's a new crash source
3. Adjust the `SYSTEM_PROMPT` if the final answer's tone/format is off

## Day 10: Polish + Demo Rehearsal

- `app.py` now has a subtitle, an **"ℹ️ How this works"** expander (great
  for judges who ask about architecture — just click it, don't recite
  from memory), and clearer framing throughout
- **`DEMO_SCRIPT.md`** — a full rehearsal guide: pre-demo checklist,
  a timed 5-minute demo flow with the exact sequence of questions to
  ask, anticipated judge Q&A with suggested answers, and a "what to do
  if something breaks live" section

**Read `DEMO_SCRIPT.md` and rehearse it out loud at least once before
the actual demo** — saying your answers to the anticipated questions
out loud is very different from just having read them.

## Stretch Features (Post Day-10): Reasoning Trace + Human-in-the-Loop

Two additions on top of the core 10-day build, chosen because they map
directly to current trends in agentic AI (transparency and guardrails
before autonomous action) and to your hackathon poster's "Governance
and Security" judging category:

**1. Visible reasoning trace**
Every assistant reply in the chat now has a "🧠 Agent's reasoning"
expander showing exactly which tool(s) were called, with what
arguments, and how many memory items were used. This makes the
agent's decision-making inspectable rather than a black box — good
for judges, and genuinely useful for advisors who want to trust the
answer.

**2. Human-in-the-loop approval for rebalancing**
Whenever the agent's answer includes a rebalancing suggestion, the UI
shows an ✅ Approve / ❌ Reject step before treating it as actioned.
This reflects a real, current theme in agentic AI: autonomous agents
proposing actions should have a guardrail before anything is
"confirmed," especially in a financial context.

**What changed under the hood:** `run_agent()` now returns a dict
(`answer`, `tool_calls`, `memory_hits`, `requires_approval`) instead of
a plain string, so the UI can display the trace and approval step. If
you're calling `run_agent()` anywhere else, update accordingly:
```python
result = run_agent(query, client_id="CLIENT_001")
print(result["answer"])       # the text response
print(result["tool_calls"])   # [{"name": ..., "args": {...}}, ...]
print(result["requires_approval"])  # True if a rebalancing suggestion was made
```

Test it:
```bash
streamlit run app.py
```
Ask a rebalancing question and confirm the Approve/Reject buttons
appear; expand "🧠 Agent's reasoning" on any answer to see the trace.

## Stretch Features, Round 2: Proactive Monitoring + Sentiment-Aware Market Data

**1. Proactive Portfolio Health Scan (`src/monitoring.py`)**

This is the biggest differentiator added so far: everything before this
was *reactive* (the agent only responds when asked about a specific
client). This scans **all 10 clients at once** and surfaces anything
needing attention — unprompted. It flags:
- Any client currently at High risk
- Any client whose risk score increased since the last scan (tracked
  via a local snapshot file, `data/monitoring_snapshot.json`, auto-created
  and gitignored)

This directly matches the "proactive and adaptive" language from your
own problem statement — it's the clearest example of the agent doing
more than answer questions.

Try it: open the **"🔔 Portfolio Alerts"** tab in the app and click
**"Run Portfolio Scan."** Test it standalone (no API cost, pure Python):
```bash
python -m src.monitoring
```

**2. News/Sentiment-Aware Market Context**

`get_market_context()` now also pulls up to 3 recent news headlines
for a stock (via yfinance's free `.news` — no new API or key needed).
The agent's system prompt was updated so GPT-4o briefly characterizes
sentiment (positive/neutral/negative) from those headlines as part of
its answer, rather than just reporting price.

Try it: ask the chat *"What's the current sentiment on AAPL?"* or
*"What's happening with MSFT?"*

## Stretch Features, Round 3: Audit Trail + Evaluation + N8N Automation

**1. Audit Trail / Compliance Logging (`src/audit_log.py`)**

Directly addresses the "Governance and Security" judging category.
Every tool call, portfolio scan, and advisor approve/reject decision
is now written to a persistent log (`data/audit_log.csv`) — not just
shown live in the UI and lost when the session ends.

View it in the new **"📋 Audit Log"** tab — includes a CSV export
button, useful for showing judges a real compliance record.

Test standalone (no API cost):
```bash
python -m src.audit_log
```

**2. Agent Evaluation Harness (`tests/eval_harness.py`)**

Formalizes testing into a pass/fail scorecard: 10 test queries, each
with an expected tool (or tools), checked against what the agent
actually called. Produces both a console report and a saved
`data/eval_report.md` file — concrete evidence of testing rigor if a
judge asks "how do you know this is reliable?"

Run it (uses your API key, a few cents):
```bash
python tests/eval_harness.py
```

**3. N8N Automation Endpoint (`api_server.py`)**

Exposes the portfolio scan as an HTTP endpoint so N8N — your
hackathon's approved automation tool — can trigger it on a schedule
instead of requiring a manual button click. This hits the "Process
automation opportunities" judging category.

Run the API server (separately from Streamlit):
```bash
python api_server.py
```
Then visit `http://localhost:8000/scan` in a browser or via curl —
confirmed working end-to-end, returns the same alert data as the
Portfolio Alerts tab, as JSON.

**Wiring it to N8N** (do this only if you have N8N set up):
1. In N8N, add a **Schedule Trigger** node (e.g. "every day at 8 AM")
2. Add an **HTTP Request** node, method `GET`, URL `http://localhost:8000/scan`
   (or wherever you deploy this)
3. (Optional) Add a **Slack** or **Email** node after it, using the
   `alert_count` and `alerts` fields from the response to notify
   advisors automatically when clients need attention
4. Activate the workflow

If you don't have time to actually set up N8N before your demo, the
API server alone is still a valid, demonstrable "automation-ready"
component — you can explain the integration point exists and show the
working endpoint, without needing a live N8N instance in the room.

## Stretch Features, Round 4: Real-Time Market Valuation & Gain/Loss

**The gap this fixes:** Previously, "portfolio value" was calculated at
**purchase price** (cost basis) — meaning the assistant couldn't
correctly answer arguably the most important investing questions:
*"What's this worth right now?"* and *"Is this client up or down?"*

**What changed:** `get_portfolio_summary()` now fetches **live current
prices** per holding via yfinance and returns:
- `total_value` — current market value (not cost basis)
- `total_cost_basis` — what was originally paid
- `total_gain_loss` / `total_gain_loss_pct` — unrealized gain/loss
- Per-holding `current_value`, `gain_loss`, `gain_loss_pct`, and a
  `price_is_live` flag

**Graceful degradation:** if a live price can't be fetched for a
symbol (rate limit, network issue), that holding falls back to its
purchase price and is flagged `price_is_live: False`, with a visible
note — the whole tool never crashes just because one price lookup fails.

**Dashboard tab** now shows a dedicated "Unrealized Gain/Loss" metric
alongside the existing value/risk/holdings metrics.

**New questions this unlocks:**
- "What's this portfolio worth right now?"
- "Is this client up or down overall?"
- "Which holdings are performing best/worst?" (visible per-holding in
  the dashboard table)

Test it:
```bash
python -m src.tools.portfolio_summary
streamlit run app.py   # check Dashboard tab's new Gain/Loss metric
```

## Stretch Features, Round 5: Open-Ended Investment Questions

This round makes the assistant answer genuinely open-ended stock
questions, not just questions about the 10 synthetic clients — while
staying responsible about what an AI agent should and shouldn't claim.

**1. Enhanced Market Context (`src/tools/market_context.py`)**

Now returns fundamentals (P/E ratio, market cap), analyst recommendation
and target price, and recent news — not just price. **Also
auto-detects Indian tickers**: asking about "TCS" or "INFY" without a
suffix automatically tries `.NS` (NSE) and `.BO` (BSE) until one
resolves, so you don't need to know the exact suffix.

**2. Profit-Booking / Tax-Loss Harvesting Tool (`src/tools/profit_booking.py`)**

A genuinely answerable version of "which stocks should I sell" — uses
your real-time gain/loss data (Round 4) to flag holdings up ≥20% as
profit-booking candidates, and holdings down ≤15% as tax-loss
harvesting candidates. Rule-based and explainable, same philosophy as
the risk score and rebalancing tools. Like rebalancing, this now
requires advisor approval before being treated as actioned.

**3. Responsible-investing guardrails (baked into the agent's instructions)**

For questions like *"shall I invest in TCS?"* or *"what will AAPL's
future be?"*, the agent is explicitly instructed to:
- Present factual data (price, fundamentals, analyst view, sentiment) —
  **not** a confident "yes, buy it" recommendation
- **Never predict future prices** — explain current trend/fundamentals
  instead, and say plainly that future performance can't be reliably
  predicted
- For profit-booking questions, present the rule-based tool's findings
  directly, since that IS a legitimate, answerable calculation

This mirrors how real financial tools and licensed advisors operate,
and is a genuinely good talking point on responsible AI design if a
judge asks about it.

Try these in the chat:
- *"Should I invest in TCS?"* — tests Indian ticker resolution + balanced, non-prescriptive answer
- *"What's the outlook for AAPL?"* — tests fundamentals + sentiment synthesis, no price prediction
- *"Which stocks should I book profit on?"* — tests the new rule-based tool + approval gate

## Stretch Features, Round 6: General Finance Q&A Fallback

**The gap this fixes:** Previously, the system prompt told the agent
to "always use a tool" for any question, which could make it awkward
or reluctant on general finance/investing questions that don't
involve a specific client or live stock data — e.g. "what is
diversification?", "how does compound interest work?", "what's a
P/E ratio?" These are exactly the kind of questions a knowledgeable
assistant (or "normal GPT") should just answer directly.

**What changed:** The system prompt now explicitly distinguishes:
- Questions about a **specific client or stock** → use the appropriate
  tool, never guess at real numbers
- **General finance/investing education questions** → answer directly
  from the model's own knowledge, no tool call needed

**New sidebar category** — "Try asking — General Finance" — with
examples like "What is diversification?" and "What's the difference
between a mutual fund and an ETF?"

**Eval harness updated:** added a case verifying general-knowledge
questions correctly trigger **zero** tool calls (not just "at least
the expected tool," which is what the other cases check — this one
specifically checks the agent didn't unnecessarily call something).

Test it:
```bash
streamlit run app.py
```
Ask "What is diversification?" and confirm you get a direct,
knowledgeable answer with no "🔧 tool call" happening — check the
"🧠 Agent's reasoning" expander shows no tool calls for this one.

## Stretch Features, Round 7: Expanded Client Data & Multi-Asset Portfolios

Significantly richer synthetic dataset and portfolio logic:

**Richer client profiles** (`data/clients.csv`): age, investment goal
(Retirement/Wealth Growth/Child Education/Home Purchase/Regular
Income), time horizon, income bracket, and cash balance — not just
name and risk profile.

**Purchase dates on every stock holding** (`data/holdings.csv`) —
enables "when did I buy this" style questions and more realistic
holding-period context.

**New asset classes** (`data/other_investments.csv`): each client now
may hold Fixed Deposits, Recurring Deposits, Corporate Bonds, PPF,
NSC, and/or Sovereign Gold Bonds — valued using real compound-interest
and RD-maturity formulas in `src/tools/fixed_income.py` (simplified
for explainability, same philosophy as the risk score and rebalancing
logic — not actuarially precise, but transparent and correct in shape).

**A real currency bug was found and fixed during testing:** stocks are
priced in USD (real US tickers via yfinance) while cash/FD/RD/bonds
are denominated in INR. Early testing showed rupee amounts being
miscounted as if they were dollars in the grand total — an ~83x
overvaluation. Fixed with an explicit, documented conversion (`src/tools/fixed_income.py: inr_to_usd()`, fixed demo rate of 1 USD = 83 INR) applied consistently in both `portfolio_summary.py` and `risk_score.py`.

**`get_portfolio_summary()` now returns**, in addition to stocks:
- `other_investments` — each FD/RD/Bond/scheme with current value, gain/loss, maturity status
- `cash_balance_inr` — uninvested cash
- `asset_allocation` — Stocks/FD/RD/Bonds/schemes/Cash as % of total (currency-normalized)
- `age`, `investment_goal`, `time_horizon` — client profile context

**`calc_risk_score()` now includes a 4th factor**: safe-asset
allocation (cash + FD/RD/bonds/schemes) offsets pure stock-concentration
risk — a client heavily concentrated in one sector is genuinely less
risky if they also hold substantial safe assets elsewhere.

**Dashboard tab** now shows client profile (age/goal/horizon), cash
balance, an asset-allocation chart (all asset classes) alongside the
existing sector-allocation chart (stocks only), and a separate table
for FD/RD/Bond/government-scheme holdings.

Test it:
```bash
python data/generate_data.py          # regenerate the expanded dataset
python -m src.tools.fixed_income      # test FD/RD valuation math directly
python -m src.tools.portfolio_summary # full multi-asset summary for CLIENT_003
python -m src.tools.risk_score        # risk score with safe-asset factor
streamlit run app.py                  # see it all in the Dashboard tab
```

## Stretch Features, Round 8: Visual Polish

Two demo-facing UX improvements — no new backend logic, just makes the
existing app feel more polished and faster to demo live:

**1. Clickable suggested questions**

Sidebar example questions are now organized into collapsible
categories (Your Portfolio / Stock Research / General Finance) as
actual buttons, not static text. Clicking one sends it straight to
the agent — no typing needed during a live demo, no risk of a typo
mid-presentation. Switch to the **💬 Chat** tab to see the response
after clicking.

**2. Donut charts instead of bar charts**

Asset allocation and sector allocation now render as polished donut
charts (via Plotly) instead of plain bar charts — same data, more
visually engaging, reads faster at a glance. Colors match the app's
purple/pink/orange theme.

Test it:
```bash
pip install -r requirements.txt   # picks up plotly
streamlit run app.py
```
Click a sidebar suggestion button, then check the Chat tab for the
response. Open the Dashboard tab to see the new donut charts.

## Roadmap

| Day | Milestone |
|---|---|
| 1 | API key working, tool signatures defined, repo initialized ✅ |
| 2 | Synthetic portfolio dataset ✅ |
| 3 | Implement the 4 tool functions ✅ |
| 4 | LangChain agent + GPT-4o function-calling wired up ✅ |
| 5 | Agent tested end-to-end on sample queries ✅ |
| 6 | ChromaDB memory added ✅ |
| 7 | Streamlit chat UI ✅ |
| 8 | Dashboard view ✅ |
| 9 | Full run-through + bug fixes ✅ |
| 10 | Polish + demo rehearsal ✅ |
| Stretch | Reasoning trace + human-in-the-loop approval ✅ |
| Stretch 2 | Proactive monitoring + sentiment-aware market context ✅ |
| Stretch 3 | Audit trail + evaluation harness + N8N automation endpoint ✅ |
| Stretch 4 | Real-time market valuation + gain/loss ✅ |
| Stretch 5 | Open-ended investment Q&A + profit-booking tool ✅ |
| Stretch 6 | General finance Q&A fallback ✅ |
| Stretch 7 | Expanded client data + multi-asset portfolios (FD/RD/Bonds/schemes) ✅ |
| Stretch 8 | Visual polish: clickable questions + donut charts ✅ |

🎉 **Build complete.** See `DEMO_SCRIPT.md` for your presentation guide.
