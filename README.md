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

## Stretch Features, Round 9: Daily Excel Valuation Snapshot

**A real bug was found and fixed:** FD/RD/Bond/government-scheme
valuations used a hardcoded fixed date instead of the actual current
date — meaning they would NEVER have genuinely updated over time, no
matter how many days passed. Fixed in `src/tools/fixed_income.py` to
use the real system date, so these valuations now correctly grow as
real time passes.

**New: `scripts/daily_valuation_snapshot.py`** — generates a
multi-sheet Excel workbook (`data/daily_valuation_snapshot.xlsx`) with
every client's current valuation: stocks at live market prices,
FD/RD/Bonds/schemes valued as of today's real date, cash balances,
risk scores, and full holdings detail. Useful as a physical file to
open, email, or archive — separate from running the live app.

Run it manually anytime:
```bash
python scripts/daily_valuation_snapshot.py
```

### Making it run automatically every day

**Option A — Windows Task Scheduler (simplest, no extra tools):**
1. Open Task Scheduler → Create Basic Task
2. Name it "Daily Portfolio Snapshot", trigger: Daily, set your preferred time
3. Action: "Start a program" →
   - Program: `<your-project-folder>\venv\Scripts\python.exe`
   - Arguments: `scripts\daily_valuation_snapshot.py`
   - Start in: `<your-project-folder>`
   (replace `<your-project-folder>` with wherever you cloned this repo, e.g. `C:\Projects\agentic-investment-assistant`)
4. Save — the Excel file now refreshes daily even if you never open the app

**Option B — N8N (matches your hackathon's approved automation tool):**
1. Run `python api_server.py` (keep it running, e.g. as a background service)
2. In N8N: Schedule Trigger (daily) → HTTP Request node → `GET http://localhost:8000/snapshot`, with header `X-API-Key: <your API_SERVER_KEY from .env>` (the endpoint now requires authentication — see Security section below)
3. This regenerates the same Excel file via the API instead of a local scheduled script — useful if N8N is already your automation hub for other things (like the portfolio alert scan)

Both options produce the exact same file — pick whichever fits how you're already managing this project.

## Stretch Features, Round 10: "For Investors" — Self-Service End-User Tab

A genuinely new user-facing feature: a separate tab for a generic
self-service investor, distinct from the advisor tools throughout the
rest of the app. No client_id needed — takes a real person's own age,
investable amount, and goal directly.

**Important framing decision:** the original request included having
the agent name specific real, named individuals (e.g. well-known
investors) as "invested in this stock, so you should too." This was
NOT built — fabricating or guessing a real person's actual holdings
and presenting that as fact to influence someone else's money
decisions is a real misinformation risk (and one of the people
mentioned is deceased, making "current" claims about them actively
misleading). If you want a "notable investor" feature later, it
should only use real, cited, publicly-disclosed shareholding data
(a legitimate category in Indian markets via regulatory disclosure),
never fabricated picks.

**What WAS built, all using real data, no new paid APIs:**

**1. Age + amount + goal → risk profile & allocation** (`src/tools/investor_guidance.py`)
Rule-based, fully explainable (same philosophy as `calc_risk_score`):
uses the classic "100 minus age = equity %" rule of thumb, adjusted
for stated goal and time horizon. Returns a risk category
(Conservative/Moderate/Aggressive), a suggested allocation across
Equity/Debt/Gold/Cash, and the rupee breakdown — always with an
explicit disclaimer that this is educational guidance, not
personalized financial advice.

**2. Historical performance lookback** (`src/tools/historical_performance.py`)
Real 1/2/3-year historical returns via yfinance — shown as green
(positive) or red (negative) bars. This is a look BACKWARD at actual
data, never a forward prediction — consistent with the project's
existing rule against forecasting future prices.

**3. Sector comparison** (reuses existing `sector_performance_tool`)
Real, live today's performance across all Nifty sector indices, shown
as a color-coded bar chart — helps a self-service investor see where
current momentum is, using data already built in Round 7.

**4. Downloadable personalized report + notification**
One click generates a plain-text report (age, amount, goal, full
allocation breakdown, reasoning, disclaimer) via `st.download_button`,
with a confirmation message after generation.

Test it:
```bash
streamlit run app.py
```
Open the **🧑‍💼 For Investors** tab, enter an age/amount/goal, and
check: the allocation donut chart, the historical performance bars
(try TCS.NS), the sector comparison, and the downloadable report.

## Stretch Features, Round 11: Stock Screener + Investor Chat

**A boundary held, explained honestly:** the original request in this
round again asked for "breakout" stock predictions framed to make the
investor happy. This was declined for the same reason as before — no
one can reliably predict a breakout, and picking stocks to engineer a
positive emotional reaction is dishonest by design. What WAS built
instead is the responsible version: real, current, verifiable data,
personalized by risk category, never framed as a forecast.

**1. Stock Screener** (`src/tools/stock_screener.py`, new **🔎 Stock
Screener** tab) — screens a fixed universe of real Indian stocks for
three REAL, CURRENT data points: proximity to 52-week high, P/E
valuation, recent earnings growth. Results are tagged and SORTED by
relevance to a risk category (Conservative prioritizes low P/E value
picks; Aggressive prioritizes momentum/earnings growth) — but every
field shown is real, verifiable, as-of-today data. The tab explicitly
states this is not a prediction and auto-detects the investor's risk
category from the "For Investors" tab if already generated.

**2. Investor-facing chat** (bottom of the "For Investors" tab, after
guidance is generated) — a scoped chat where a self-service investor
can ask follow-up questions ("why low P/E stocks for me?", "how has
TCS done over 3 years?", "how's the IT sector today?") using 3 new
tools: `investment_guidance_tool`, `historical_performance_tool`,
`stock_screener_tool` — the agent automatically has context on that
investor's own age/risk category/goal so follow-ups don't need
re-explaining. Same reasoning-trace expander as the advisor chat.

**System prompt reinforcement:** explicit new rule — screener and
historical-performance results must be presented factually and
neutrally, never reframed as a forecast or with emotionally
persuasive language ("can't-miss," "will make you rich").

Test it:
```bash
python -m src.tools.stock_screener
streamlit run app.py
```
Generate guidance in "For Investors," check the risk category
auto-fills in "🔎 Stock Screener," run the screener, then ask a
follow-up question in the investor chat section.

## Stretch Features, Round 12: Screener Depth, Alerts, Dashboard Fix

**A boundary held again, explained honestly:** this round again asked
for future price predictions ("this stock will grow to X money").
Declined for the same reason as always — nobody can reliably know
that. Built instead: a **Hypothetical Growth Illustrator** — the same
graph experience (pick a stock, see 1-4 year values), computed from
the stock's REAL historical average return, with the same mandatory
"past performance is not indicative of future returns" framing real
mutual funds use. Verified the underlying compounding math is
mathematically correct with manual test cases.

**1. Screener sector-interest intake** — multiselect for sectors of
interest before running the screener; if left blank, automatically
screens ALL sectors (manual fallback, no dead end).

**2. Screener-specific chat section** — same pattern as the "For
Investors" chat, scoped to screener results.

**3. Plain-language "reason" per screener stock** — e.g. "P/E ratio of
14.2 is below the 20 threshold — trading cheaper relative to earnings
than average." Real current-data justification, explicitly not a
future claim (reinforced in the system prompt).

**4. "For Investors" chat now explicitly covers FD/RD/Bonds/Gold** —
system prompt updated so general asset-class questions (not tied to a
specific client) are answered helpfully regardless of asset type.

**5. Sector + stock names always paired** — new system prompt rule:
whenever a sector is discussed, name real stocks within it too, not
the sector alone.

**6. Hypothetical Growth Illustrator** (`src/tools/growth_illustrator.py`)
— see above. Honest reframe of the "future prediction" request.

**7. Portfolio Alerts now include a real, data-driven suggested action**
— `calc_risk_score()` returns structured fields (`top_sector`,
`max_sector_pct`, `safe_ratio_pct`); `monitoring.py` uses these to
build a SPECIFIC suggestion per client (e.g. "rebalance out of IT (59%
of holdings)" or "increase FD/RD/Bonds allocation") rather than a
generic message.

**8. Dashboard FD/RD/Bonds/Gold fix** — found and fixed a real gap: 3
of 10 clients had zero non-stock investments by design (aggressive
risk profile allowed 0-2 randomly), making that Dashboard section look
broken/empty. Fixed the generator to guarantee every client has at
least 1. Also clarified in the UI that Gold is represented via
Sovereign Gold Bond.

Test it all:
```bash
python data/generate_data.py      # regenerate with the guaranteed-minimum fix
python -m src.tools.stock_screener
python -m src.tools.growth_illustrator
python -m src.monitoring           # check suggested_action appears
streamlit run app.py
```

## Stretch Features, Round 13: Real Calendar Years + Chart Flexibility

**The "future prediction" ask came up again** ("stocks that will
perform best in upcoming years") — declined for the same reason as
every time before: no one can reliably know that. Everything below is
the honest, still-useful version of what was actually asked for.

**1. Real calendar years, not generic labels** — Historical
Performance Lookback now shows actual years (e.g. "2025", "2024",
"2023" if today is 2026) instead of "1 year/2 year/3 year". The
Hypothetical Growth Illustrator now shows real future years (e.g.
"2027", "2028") instead of "Year 1/Year 2". Verified the year-labeling
math directly: today's date correctly produces 2025/2024/2023 for a
1/2/3-year lookback.

**2. Monthly/weekly/daily granularity** (`get_price_history_series()`
in `historical_performance.py`) — a NEW real price history line chart
where you pick Daily (3 months), Weekly (1 year), or Monthly (3 years)
and see the actual historical closing price at that zoom level — real
yfinance data, not the discrete 1/2/3-year snapshot.

**3. Bar/Line chart toggle** — added to Historical Performance and the
Growth Illustrator, so you can view the same real data either way.

**4. Bar/Pie chart toggle** — added to Sector Comparison. Since
sector comparison is a same-day snapshot (not a time series), pie
shows relative magnitude of today's move per sector, still colored
green/red by direction.

Test it:
```bash
python -m src.tools.historical_performance
streamlit run app.py
```
Open "For Investors," generate guidance, then try the Historical
Performance section (switch Bar/Line, try Daily/Weekly/Monthly price
history) and the Growth Illustrator (real future years, Bar/Line).

## Stretch Features, Round 14: Honest Positive Framing + Visual Redesign

**Clarified, not a bug:** "% from 52-week high" is mathematically
almost always negative (only a stock exactly at its high shows 0%) —
that's expected, not an error. Fixed the *display*, not the data:

**1. Positive-framed metric** — now shows "97% of 52-week high"
instead of "-3% from high" — identical real number, far less alarming
presentation.

**2. Screener filters to genuine positive signals** — by default, only
shows stocks that crossed at least one real threshold (near 52-week
high, low P/E, or strong earnings growth). If genuinely nothing in
the universe qualifies right now, this is reported honestly rather
than silently showing unfiltered results.

**3. "The Complete Picture" education panel** (`src/tools/asset_education.py`)
— alongside stock ideas, general educational cards on Fixed Deposits,
Recurring Deposits, Emergency Fund, and Cash — benefits and tradeoffs
for each, standard personal-finance facts, not tied to any specific
product or rate.

**4. Visual redesign** — gradient hero banner, styled metric cards
with hover effects, polished tabs, gradient buttons, softer sidebar —
custom CSS injected via `st.markdown(unsafe_allow_html=True)`.

Test it:
```bash
python -m src.tools.stock_screener
python -m src.tools.asset_education
streamlit run app.py
```

## Stretch Features, Round 15: AI Sector-Wise Stock Suggestions

**Same honest framing, new delivery format:** the request was for "AI
stock suggestions, sector-wise, for future investment." Built the
honest version: an AI-written narrative, organized by sector, built
strictly from REAL current screener data (52-week high proximity,
P/E, earnings growth) — never a future prediction, and the system
prompt fed to the LLM explicitly forbids "will perform well" type
language.

**How it works:**
1. `get_stock_screener_by_sector()` (`src/tools/stock_screener.py`)
   runs the existing real-data screener across ALL sectors, filtered
   to genuine positive signals, grouped by sector
2. `generate_sector_wise_suggestions()` (`src/agent.py`) feeds that
   real data to GPT-4o with strict rules: every claim must come from
   the data given, never invent a number, never predict future
   performance — and asks it to write 2-3 sentences per sector naming
   the real stocks and what stood out about each
3. New **"🤖 AI Stock Suggestions by Sector"** section in the "For
   Investors" tab, using the investor's own risk category from their
   guidance — with the raw underlying real data viewable in an
   expander for full transparency

Test it:
```bash
python -m src.tools.stock_screener   # confirms get_stock_screener_by_sector
streamlit run app.py
```
Generate guidance in "For Investors," then click "Get AI Sector-Wise
Suggestions" — check the narrative reads factually (which sectors,
which real stocks, which real data point stood out) with no
forward-looking claims, and expand "View the real underlying data" to
confirm it matches.

## Stretch Features, Round 16: Stock Search Box for Historical Performance

**"Historical Performance Lookback" now accepts ANY stock, not just a
fixed dropdown of 6 examples.** Type a symbol (e.g. "TCS", "WIPRO",
"RELIANCE") and it auto-resolves the Indian exchange suffix (.NS/.BO)
if omitted — same smart resolution logic as `market_context_tool`.
Quick-pick buttons remain below the search box for convenience, but
any real stock can be searched directly.

**What changed:** `src/tools/historical_performance.py` gained a
`_resolve_symbol()` helper (tries the symbol as given, then `.NS`,
then `.BO`), used by both `get_historical_returns()` and
`get_price_history_series()`. The result now includes
`resolved_symbol` so the UI can show "resolved to TCS.NS" if you typed
just "TCS".

Test it:
```bash
python -c "from src.tools.historical_performance import get_historical_returns; print(get_historical_returns('WIPRO'))"
streamlit run app.py
```
Open "For Investors" → Historical Performance Lookback → type any
symbol (with or without `.NS`) → Show Historical Performance.

## Stretch Features, Round 17: Cloud Deployment Fix — Yahoo Finance Blocking

**Root cause of "works locally, fails on Streamlit Cloud":** Yahoo
Finance (which yfinance scrapes under the hood) increasingly blocks or
rate-limits requests from cloud-hosting data-center IP ranges (AWS,
GCP, Azure — including Streamlit Community Cloud), even for completely
valid, liquid tickers like TCS.NS. This is a known yfinance/Yahoo
Finance issue, not a bug in this codebase.

**Fix:** `src/tools/yf_session.py` — a shared session using `curl_cffi`
that impersonates a real Chrome browser's TLS fingerprint, which is
the fix recommended by yfinance's own maintainers for exactly this
symptom. Wired into every `yf.Ticker()` call across the project (7
call sites across `portfolio_summary.py`, `stock_screener.py`,
`market_context.py`, `historical_performance.py`,
`sector_performance.py`) — all pass `session=get_yf_session()` now.

Test it:
```bash
pip install -r requirements.txt   # picks up curl_cffi
python -c "from src.tools.yf_session import get_yf_session; print(get_yf_session())"
streamlit run app.py
```
Redeploy to Streamlit Cloud and try Historical Performance Lookback
again — should now resolve real tickers correctly from the cloud.

## Stretch Features, Round 18: External Review Fixes + Goal Gap Analysis

Based on an external technical review, split into "fix regardless"
items and the single highest-value enhancement recommended.

**1. API authentication** (`api_server.py`) — every endpoint except
the root health-check now requires a valid `X-API-Key` header via
FastAPI's standard `Depends()` pattern. Tested end-to-end: no key →
401, wrong key → 401, correct key → 200 with real data. Set
`API_SERVER_KEY` in `.env` for a stable key (see `.env.example`); if
unset, a temporary one is generated and printed to console each run.

**2. Removed hardcoded local paths from README** — Windows Task
Scheduler instructions now use a generic `<your-project-folder>`
placeholder instead of a literal `D:\Hackathon\...` path.

**3. Session-wide query rate cap** (`app.py`) — `MAX_QUERIES_PER_SESSION`
(default 40) applied across ALL chat surfaces (advisor chat, investor
chat, screener chat, AI sector suggestions) combined, since they share
one OpenAI account. Protects a live demo from a runaway bill if
someone spams the chat.

**4. Cost/latency in the reasoning trace** — every agent response now
tracks real latency (seconds) and token usage, with an approximate
cost estimate (static pricing table for gpt-4o/gpt-4o-mini — not
billing-accurate, but directionally useful: "this agent costs
~$0.0004/query"). Shown in every "🧠 Reasoning" expander across all
three chat surfaces. Verified the cost math and token-extraction logic
directly against hand-calculated expected values.

**5. Goal Gap Analysis** (`src/tools/goal_gap_analysis.py`, new
**"🎯 Goal Gap Analysis"** section in "For Investors") — the reviewer's
top-flagged gap: this project told users their current value and risk
score, but never whether that's *enough* for their actual goal. This
tool projects current corpus + planned monthly contributions forward
using a clearly-assumed return rate (7%/10%/12% for Conservative/
Moderate/Aggressive, based on historical asset-class averages — an
assumption for planning, explicitly never framed as a prediction),
compares to a target amount, and if there's a shortfall, calculates
the exact additional monthly SIP needed to close it using the
standard future-value-of-annuity formula. **Verified the math
directly**: added the calculated required SIP back into a shortfall
scenario and confirmed it closes the gap to within ₹0.23 on a ₹1 crore
target.

Test it:
```bash
python -m src.tools.goal_gap_analysis
python api_server.py    # then try curl with/without X-API-Key header
streamlit run app.py
```

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
| Stretch 9 | Daily Excel valuation snapshot + fixed-date bug fix ✅ |
| Stretch 10 | Real Indian tickers + sector data + "For Investors" self-service tab ✅ |
| Stretch 11 | Stock screener (real data, no predictions) + investor chat ✅ |
| Stretch 12 | Screener depth (reasons, sectors, chat), growth illustrator, data-driven alerts, dashboard fix ✅ |
| Stretch 13 | Real calendar years + monthly/weekly granularity + bar/line/pie chart toggles ✅ |
| Stretch 14 | Positive-framed metrics, asset education panel, full visual redesign ✅ |
| Stretch 15 | AI sector-wise stock suggestions (real data, GPT-4o narrated) ✅ |
| Stretch 16 | Stock search box with auto-resolved Indian ticker suffixes ✅ |
| Stretch 17 | Cloud deployment fix — browser-impersonating yfinance session ✅ |
| Stretch 18 | API auth, rate cap, cost/latency trace, Goal Gap Analysis ✅ |

🎉 **Build complete.** See `DEMO_SCRIPT.md` for your presentation guide.
