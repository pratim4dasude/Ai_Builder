# Finance Intelligence Worker

Multi-agent CFO copilot for D2C ecommerce. Reads five raw CSV ledgers and returns a structured CFO memo with revenue forecast, invoice reconciliation, leakage %, margin breakdown, and risk flags — through one FastAPI surface (`/chat`, `/chat/raw`, `/chat/stream`).

---

## What it does

- Ingests `orders.csv`, `payments.csv`, `invoices.csv`, `refunds.csv`, `expenses.csv`.
- Routes the user query through a Supervisor → Planner → specialist-agents pipeline.
- Runs the heavy four agents (revenue, invoice, leakage, margin) in parallel via `asyncio.gather`.
- Forecasts the next 7 days of revenue with an XGBoost model that retrains on every run.
- Synthesises an LLM-written CFO memo grounded in the numeric output of the deterministic agents — the model is never asked to invent numbers.

---

## Architecture

```
                          FINANCE INTELLIGENCE WORKER  (FastAPI :8001)

  Client                                                                     Disk / Store
 ┌──────┐    POST /chat                                                     ┌─────────────┐
 │ User │ ─ /chat/raw  ────────────┐                                        │  data/*.csv │
 │      │ ─ /chat/stream (SSE) ────┤                                        │  5 ledgers  │
 └──────┘                          │                                        └─────┬───────┘
                                   ▼                                              │
                         ┌────────────────────┐         ┌──────────────────┐      │
                         │   api/chat.py      │ <────── │  SQLiteConvo     │      │
                         │  ChatRequest       │         │  Memory          │      │
                         │  followup resolver │ ──────> │  finance_memory  │      │
                         └─────────┬──────────┘         │  .db (2 tables)  │      │
                                   │ resolved query     └──────────────────┘      │
                                   ▼                                              │
                         ┌────────────────────┐                                   │
                         │  SupervisorAgent   │  keyword routing -> agent set     │
                         │     .plan()        │                                   │
                         └─────────┬──────────┘                                   │
                                   ▼                                              │
                         ┌────────────────────┐                                   │
                         │   PlannerAgent     │  builds 4-step execution plan     │
                         │  .create_plan()    │  (sequential | parallel hints)    │
                         └─────────┬──────────┘                                   │
                                   ▼                                              │
                  ╔═════════════════════════════════════╗                         │
                  ║  FinanceAgentRuntime.run_plan()     ║                         │
                  ║  (asyncio.gather for parallel step) ║                         │
                  ╚════╤═══════════╤═══════════╤═══════╤╝                         │
       Step 1 (seq)    │           │           │       │   Step 3 (seq)           │
   ┌──────────────┐    │           │           │       │  ┌───────────────┐       │
   │ PeriodAgent  │<───┘           │           │       └─>│ StatisticsAg. │       │
   │ parses range │                │           │          └───────┬───────┘       │
   └──────────────┘                │           │                  │               │
                  Step 2 (PARALLEL - asyncio.gather)              │               │
   ┌──────────────┐  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
   │ RevenueAgent │  │ InvoiceAgnt │  │ LeakageAgent │  │ MarginAgent  │          │
   └──────┬───────┘  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘          │
          ▼                 ▼                ▼                 ▼                  │
       ToolRegistry  ──>  6 tools  ──>  Services layer                            │
   ┌──────────────────────────────────────────────────────────────────┐           │
   │ RevenueForecastService   XGBoost (120 trees, depth 4, lr 0.08)   │◀─ artifacts/models/
   │ InvoiceMatchingService   duplicate / orphan / >15% or >Rs.500    │           │
   │ LeakageDetectionService  refund% by reason                       │           │
   │ MarginRefundService      margin = rev - exp - refunds; p95       │           │
   │ StatisticsService        p75/p90/p95, 8+ risk flags              │           │
   └────────────────────────────────────┬─────────────────────────────┘           │
                                        │   CSVConnector <────────────────────────┘
                                        ▼
                              ┌──────────────────┐
                       Step 4 │   MemoAgent      │ ──▶ LLMClient (OpenAI gpt-4o-mini, T=0.2)
                              │  CFO synthesis   │
                              └────────┬─────────┘
                                       ▼
                          ┌─────────────────────────┐
                          │ response_formatter      │  answer + summary + data +
                          │ .build_finance_response │  agents + provenance + memory
                          └────────┬────────────────┘
                                   ▼
                            JSON  /  SSE stream
                                   │
                                   └──▶ SQLiteConvoMemory.add_message + update_context
```

---

## Data flow

1. `api/chat.py` receives `ChatRequest{query, session_id}`.
2. `SQLiteConversationMemory.get_context()` + `resolve_finance_followup_query()` rewrite shorthand queries (`"why"`, `"memo"`, `"what about X"`) against prior context.
3. `SupervisorAgent.plan()` picks agents from the query keywords.
4. `PlannerAgent.create_plan()` emits a 4-step execution plan (sequential / parallel hints).
5. `FinanceAgentRuntime.run_plan()` executes — Step 2 fans out four agents through `asyncio.gather`, deepcopying state for safe merge.
6. Each agent calls a tool from the `ToolRegistry`, which delegates to a Service that runs on Pandas DataFrames loaded by `CSVConnector`.
7. `RevenueForecastService` loads / trains `RevenueXGBoostModel` and persists it to `artifacts/models/`.
8. `MemoAgent` calls `LLMClient.generate()` with the system prompt + numeric outputs to produce a CFO memo.
9. `response_formatter.build_finance_response()` packages `answer`, `summary`, `data`, `agents`, `provenance.citations`, `memory`.
10. The conversation pair + extracted context (`last_query`, `last_main_issue`, `last_*_analysis`, …) are written back to SQLite.

---

## Module map

| Layer | Path | Key class / function |
|---|---|---|
| API | `app/api/chat.py` | `POST /chat`, `POST /chat/raw`, `POST /chat/stream` |
| State | `app/agents/state.py` | `FinanceAgentState` (dataclass) |
| Supervisor | `app/agents/supervisor_agent.py` | `SupervisorAgent.plan()` |
| Planner | `app/agents/planner_agent.py` | `PlannerAgent.create_plan()` |
| Period | `app/agents/period_agent.py` | natural-language date range parsing |
| Specialists | `app/agents/{revenue,invoice,leakage,margin,statistics,memo}_agent.py` | one class per agent |
| Runtime | `app/runtime/agent_runtime.py` | `FinanceAgentRuntime.run_plan()` |
| Tools | `app/tools/setup_tools.py` | `ToolRegistry` (6 tools) |
| Services | `app/services/*.py` | 5 deterministic analyzers |
| ML | `app/ml/revenue_xgboost.py` | `RevenueXGBoostModel` (120 trees, depth 4, lr 0.08) |
| LLM | `app/llm/client.py` | `LLMClient.generate()` (OpenAI gpt-4o-mini, T=0.2) |
| Memory | `app/memory/sqlite_memory.py` | `SQLiteConversationMemory`, `resolve_finance_followup_query()` |
| Connectors | `app/connectors/csv_connector.py` | `CSVConnector.load()` |
| Utils | `app/utils/response_formatter.py` | `build_finance_response()` |

---

## Tech stack

| Concern | Choice |
|---|---|
| HTTP framework | FastAPI + Uvicorn |
| Data | Pandas |
| ML | XGBoost (sklearn metrics for MAE / MAPE) |
| LLM | OpenAI Python SDK, `gpt-4o-mini`, T=0.2 |
| Memory | SQLite (`finance_memory.db`, 2 tables) |
| Streaming | Server-Sent Events |
| Concurrency | `asyncio.gather` (step-level parallelism) |

---

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Full structured response (memo + summary + per-agent data) |
| POST | `/chat/raw` | Raw agent outputs, no response shaping |
| POST | `/chat/stream` | SSE — emits `agent_started`, `agent_completed`, `parallel_started`, `final_output` |
| GET | `/validate-data` | File + column schema check on the 5 CSVs |

Sample request:

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How did margin look last 30 days?", "session_id": "demo"}'
```

---

## Run it

```bash
# from repo root, with venv active
pip install -r requirements.txt
cd finance_intellegence_worker
python app/main.py            # serves on http://127.0.0.1:8001
```

`.env` (at repo root or worker root):

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini       # optional
```

---

## Implementation status

| Area | Status |
|---|---|
| Supervisor + Planner + Runtime | done |
| 7 agents (period, revenue, invoice, leakage, margin, statistics, memo) | done |
| Revenue XGBoost forecast + artifact persistence | done |
| Invoice reconciliation (duplicate / orphan / mismatch) | done |
| Leakage detection by `refund_reason` | done |
| Margin + expense category + p95 anomaly | done |
| Statistics service (p75/p90/p95 + 8 risk flags) | done |
| SQLite memory + followup query resolution | done |
| SSE streaming with agent lifecycle events | done |
| Provenance / citations on response | done |
| CSV schema validation endpoint | done |
| Auth, multi-tenant memory namespace | next |
| OpenTelemetry traces around `run_plan` | next |
| Pluggable forecaster behind `ForecastBackend` | next |

---

## Engineering highlights

- **Supervisor / Planner / Runtime split.** Routing, planning, and execution are three separate objects. The Planner emits an execution plan (sequential + parallel steps) that the Runtime interprets — adding a new agent does not touch the Runtime.
- **Parallel step is real.** Step 2 fans `RevenueAgent`, `InvoiceAgent`, `LeakageAgent`, `MarginAgent` through `asyncio.gather`. State is deep-copied per branch and merged on completion, so two agents writing to different `FinanceAgentState` fields never race.
- **Grounded LLM.** `MemoAgent` is told *do not invent numbers, do not override the deterministic risk flags*. The Services produce the numbers; the LLM only narrates. Temperature 0.2.
- **ML, not vibes.** `RevenueXGBoostModel` engineers lag-1 / lag-3 / lag-7 features, rolling-3 / rolling-7 means, day-of-week, and reports MAE / MAPE in the response metadata so the memo can quote its own accuracy.
- **Two-table SQLite memory.** `conversations` (chronological turns) + `session_context` (extracted entities like `last_main_issue`, `last_focus_area`, every `last_*_analysis`). Followups like *"why?"* or *"compare to last week"* are rewritten against this context before routing.
- **Citation tracking.** Every service annotates which CSV rows it read; `provenance.citations.sources` is included in the response payload.

---

## Design trade-offs

- **Rule-based supervisor over an LLM router.** Finance needs reproducibility — the same query must select the same agents every time. Keyword routing is cheap, debuggable, and free.
- **SQLite over Redis / Postgres.** Zero-config single-file DB so a reviewer can clone and run. The `Memory` interface is narrow (`add_message` / `get_history` / `get_context` / `update_context`), so swapping the backend is a one-class change.
- **XGBoost over Prophet / ARIMA.** XGBoost handles lag / rolling features cleanly and retrains in seconds per request, with no seasonality assumption to babysit.
- **`asyncio.gather` over a thread pool.** Step 2 is pandas-heavy but already partitioned per agent, so the GIL is not the bottleneck — keeping everything in one event loop also keeps cancellation and timeouts simple.

---

## Numbers you can quote from the code

- **5** input CSV ledgers, **7** agents, **6** registered tools, **5** services.
- **XGBoost:** 120 trees, max_depth 4, learning_rate 0.08, random_state 42. 7-day forecast horizon. MAE + MAPE returned per run.
- **Risk thresholds:** refund leakage > 8 %, low margin < 10 %, failed-payment rate > 8 %, invalid invoice mapping > 5 %, payment mismatch > 15 % or > Rs.500.
- **Distributions:** p75 / p90 / p95 of order value computed every run.
- **LLM:** OpenAI `gpt-4o-mini`, temperature 0.2 for the memo.

---

## Roadmap

- **DuckDB / Parquet connector.** Drop CSVs once volume grows; keep the `Connector` interface.
- **Eval harness.** Golden-answer regression on the memo — LLM-as-judge for prose, numeric tolerances for KPIs.
- **OpenTelemetry traces.** Spans around `AgentRuntime` step boundaries so latency by agent is visible in any OTLP backend.
- **Pluggable forecasters.** `ForecastBackend` interface, with Prophet and LightGBM as the next two implementations.
- **Auth + multi-tenant memory.** API-key gate, `session_id` namespaced by tenant.
- **Dockerfile + compose.** Pin Python and the model name; reproducible boot.
