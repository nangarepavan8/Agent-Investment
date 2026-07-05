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

🎉 **Build complete.** See `DEMO_SCRIPT.md` for your presentation guide.
