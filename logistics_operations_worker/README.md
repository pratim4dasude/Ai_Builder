# Logistics Operations Worker

Daily dispatch planner for an ecommerce ops desk. The LLM **plans** a DAG of agents; Python **executes** it. Outputs warehouse assignments, geographic clusters, optimised routes, risk flags, and a markdown memo saved to `reports/` — every run, timestamped.

---

## What it does

- Loads `orders.csv`, `shipments.csv`, `warehouses.csv`, `inventory.csv`.
- Assigns each pending order to the best warehouse using haversine distance + stock + capacity.
- Groups deliveries inside a 3 km radius into clusters, warehouse-aware.
- Optimises each cluster's route with a nearest-neighbour TSP approximation.
- Flags COD / RTO / SLA-delay / high-value-COD / long-distance risks.
- Synthesises a grounded markdown memo and writes `reports/{city}_dispatch_memo_{timestamp}.md`.

---

## Architecture

```
                        LOGISTICS OPERATIONS WORKER  (FastAPI :8000)

  Client                                                                     Disk / Store
 ┌──────┐  POST /chat                                                       ┌─────────────┐
 │ User │  POST /chat/stream (SSE)                                          │ data/*.csv  │
 │      │  GET  /connectors/test                                            │ orders,     │
 │      │  GET  /memory/{session_id}                                        │ shipments,  │
 └───┬──┘                                                                   │ warehouses, │
     │                                                                      │ inventory   │
     ▼                                                                      └─────┬───────┘
 ┌──────────────────┐         ┌────────────────────┐                              │
 │   api/chat.py    │ <────── │ SQLiteConvoMemory  │                              │
 │ followup resolver│         │ logistics_memory.db│                              │
 └────────┬─────────┘         └────────────────────┘                              │
          ▼                                                                       │
 ┌──────────────────┐                                                             │
 │ SupervisorAgent  │  LLM routing  ──>  fallback heuristic on failure            │
 │     .plan()      │                                                             │
 └────────┬─────────┘                                                             │
          ▼                                                                       │
 ┌──────────────────┐                                                             │
 │  PlannerAgent    │  OpenAI gpt-4o-mini, T=0  →  JSON execution DAG             │
 │     .plan()      │  {step_id, agents, parallel: true|false, depends_on}        │
 └────────┬─────────┘                                                             │
          ▼                                                                       │
 ╔══════════════════════════════════════════════════════════════════╗             │
 ║  MultiAgentRouter - execution-plan interpreter                   ║             │
 ║                                                                  ║             │
 ║   - parallel step  -> ThreadPoolExecutor(max_workers=N)          ║             │
 ║   - sequential step-> linear loop                                ║             │
 ║   - AgentRuntime wraps each call: run_id, exec time, status      ║             │
 ╚════╤══════════════╤══════════════╤══════════════╤════════════════╝             │
      │              │              │              │                              │
      ▼              ▼              ▼              ▼                              │
 ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐                         │
 │Warehouse │  │Clustering │  │ Routing   │  │  Risk    │  <- depends on Warehouse│
 │  Agent   │  │  Agent    │  │  Agent    │  │  Agent   │                         │
 └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └────┬─────┘                         │
      ▼              ▼              ▼              ▼                              │
   ToolRegistry  ->  4 tools  ->  Services layer                                  │
 ┌──────────────────────────────────────────────────────────────────┐             │
 │ warehouse_assignment.py  haversine + stock + capacity            │<────────────┤
 │ clustering_service.py    3 km radius, warehouse-aware grouping   │             │
 │ route_service.py         nearest-neighbor TSP approximation      │             │
 │ risk_service.py          COD / RTO / SLA / high-value / distance │             │
 └──────────────────────────────────────┬───────────────────────────┘             │
                                        │   CSVConnector <────────────────────────┘
                                        ▼
                              ┌──────────────────┐
                              │   MemoAgent      │ ──> LLMClient (OpenAI gpt-4o-mini, T=0.2)
                              │  always last     │     fallback narrative on failure
                              └────────┬─────────┘
                                       ▼
                          ┌──────────────────────────┐         ┌──────────────────────┐
                          │ report_writer.save_      │ ──────> │ reports/             │
                          │  final_memo_as_markdown()│         │ {city}_dispatch_memo │
                          └──────────┬───────────────┘         │ _{timestamp}.md      │
                                     ▼                         └──────────────────────┘
                          ┌──────────────────────────┐
                          │ response_formatter +     │  execution_plan, agents,
                          │  ResponseFormatter       │  warehouse_plan, clusters,
                          └──────────┬───────────────┘  routes, risks, memo, memory
                                     ▼
                       JSON  /  SSE (status, agent_completed, report_generated, final)
                                     │
                                     └──▶ SQLiteConvoMemory.add_message + update_context
```

---

## Data flow

1. `api/chat.py` receives `ChatRequest{query, session_id}`.
2. `SQLiteConversationMemory` + `FollowupResolver` rewrite contextual queries like *"plan the clusters"* into *"plan the clusters for Bangalore on 2026-05-17"*.
3. `SupervisorAgent.plan()` picks the agent set — LLM call, fallback heuristic if it fails.
4. `PlannerAgent.plan()` calls OpenAI `gpt-4o-mini` at temperature 0 to emit a JSON execution DAG: `[{step_id, agents, parallel, depends_on}]`.
5. `MultiAgentRouter` interprets the DAG. Parallel steps run through `ThreadPoolExecutor`; sequential steps run linearly. `AgentRuntime` wraps each agent invocation with a `run_id`, wall-clock timer, and status field.
6. Tools (`assign_warehouses`, `create_clusters`, `generate_routes`, `analyze_risk`) call into Services that operate on Pandas DataFrames loaded by `CSVConnector`.
7. `MemoAgent` always runs last, with the system prompt forbidding fabrication and requiring citations of the order / warehouse IDs it touched.
8. `report_writer.save_final_memo_as_markdown()` persists the memo to `reports/`.
9. `ResponseFormatter` packages `execution_plan`, `warehouse_plan`, `clusters`, `routes`, `risks`, `final_memo`, `memory` metadata.
10. The assistant turn and extracted context (last city, last warehouse count, last risk flags) are written back to SQLite.

---

## Module map

| Layer | Path | Key class / function |
|---|---|---|
| API | `app/api/chat.py` | `POST /chat`, `POST /chat/stream`, `GET /memory/{session_id}` |
| State | `app/agents/state.py` | `LogisticsAgentState` (Pydantic) |
| Supervisor | `app/agents/supervisor_agent.py` | `SupervisorAgent.plan()` + fallback |
| Planner | `app/agents/planner_agent.py` | LLM-emitted JSON DAG, T=0 |
| Router | `app/agents/router.py` | `MultiAgentRouter` — DAG interpreter, ThreadPoolExecutor |
| Agents | `app/agents/{warehouse,clustering,routing,risk,memo}_agent.py` | one class per agent |
| Runtime | `app/runtime/agent_runtime.py` | `AgentRuntime.run_agent()` — run_id, exec time, status |
| Tools | `app/tools/logistics_tools.py` | `assign_warehouses`, `create_clusters`, `generate_routes`, `analyze_risk` |
| Services | `app/services/warehouse_assignment.py` | haversine + stock + capacity |
| Services | `app/services/clustering_service.py` | 3 km radius grouping |
| Services | `app/services/route_service.py` | nearest-neighbour TSP |
| Services | `app/services/risk_service.py` | COD / RTO / SLA / high-value / distance |
| LLM | `app/llm/client.py` | OpenAI `gpt-4o-mini`, T=0.2 for memo |
| LLM | `app/llm/prompts.py` | `LOGISTICS_MEMO_SYSTEM_PROMPT`, `SUPERVISOR_SYSTEM_PROMPT` |
| Memory | `app/memory/sqlite_memory.py` | `SQLiteConversationMemory` |
| Memory | `app/memory/followup_resolver.py` | context-aware query rewriting |
| Utils | `app/utils/report_writer.py` | `save_final_memo_as_markdown()` |
| Connectors | `app/connectors/csv_connector.py` | `CSVConnector` (Pandas + citation metadata) |

---

## Tech stack

| Concern | Choice |
|---|---|
| HTTP framework | FastAPI + Uvicorn |
| Data | Pandas |
| LLM | OpenAI Python SDK, `gpt-4o-mini` |
| Memory | SQLite (`logistics_memory.db`, 2 tables) |
| Streaming | Server-Sent Events |
| Concurrency | `ThreadPoolExecutor` (pandas-heavy, CPU-friendly with threads) |
| Geometry | Haversine great-circle distance |

---

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Run the dispatch pipeline, return JSON |
| POST | `/chat/stream` | SSE — `status`, `agent_completed`, `report_generated`, `final` |
| GET | `/connectors/test` | Returns the column schema of all 4 CSVs |
| GET | `/memory/{session_id}` | Conversation history + last context |

Sample request:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan dispatch for Bangalore", "session_id": "demo"}'
```

---

## Run it

```bash
pip install -r requirements.txt
cd logistics_operations_worker
python app/main.py            # serves on http://127.0.0.1:8000
# or:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini      # optional
```

---

## Implementation status

| Area | Status |
|---|---|
| Supervisor (LLM + heuristic fallback) | done |
| LLM planner emitting JSON execution DAG | done |
| Router with parallel `ThreadPoolExecutor` + sequential steps | done |
| `AgentRuntime` timing + per-agent status | done |
| Warehouse assignment (haversine + stock + capacity) | done |
| Geographic clustering (3 km radius) | done |
| Nearest-neighbour route optimisation | done |
| Risk detection (5 categories) | done |
| Memo generation + grounded citations + fallback | done |
| Markdown report writer to `reports/` | done |
| SQLite memory + followup query resolver | done |
| Schema validation | partial (`data_validation.py` exists, lightly used) |
| OR-Tools VRP solver | next |
| Real-time traffic ETA provider | next |
| Driver assignment + shift constraints | next |

---

## Engineering highlights

- **LLM plans, Python executes.** `PlannerAgent` emits a JSON DAG at temperature 0 (`{step_id, agents, parallel, depends_on}`). The Router validates and runs it. The LLM is never given tool-call permission — cheaper, safer, fully auditable.
- **Real parallel execution.** Parallel steps run through `ThreadPoolExecutor`. Services are pandas-heavy, so threads (not asyncio) actually help: Pandas releases the GIL inside its C kernels.
- **Per-agent observability.** `AgentRuntime` assigns a `run_id` (UUID), records `execution_time_seconds`, `status`, and `error` per agent. The state carries `runtime_logs` for auditing.
- **Two-layer fallback.** SupervisorAgent: LLM router → heuristic fallback. MemoAgent: LLM narrative → templated narrative from raw summaries. The worker never crashes because of OpenAI.
- **Grounded memo.** `LOGISTICS_MEMO_SYSTEM_PROMPT` extracts citations (order IDs, warehouse names) from the working data and only includes them if present — the model is explicitly told not to invent IDs.
- **Markdown artefact per run.** `save_final_memo_as_markdown()` writes a timestamped memo to `reports/` — the worker leaves a paper trail an ops manager can mail without modification.
- **Followup resolver with extracted context.** `session_context` stores the last city, the last warehouse count, the last risk flags. *"What about the risks?"* is rewritten to the full city / date / context before routing.

---

## Design trade-offs

- **LLM as planner, not executor.** A JSON DAG that Python interprets is far cheaper, easier to test, and never picks the wrong tool — the model only chooses an order.
- **`ThreadPoolExecutor` over `asyncio`.** All four core services are Pandas-bound. Threads release the GIL inside Pandas's C code, asyncio would just block the event loop.
- **Nearest-neighbour over OR-Tools.** For ≤ ~30 stops per cluster the greedy solver is within ~5–10 % of optimal and runs in milliseconds. OR-Tools VRP is on the roadmap once cluster sizes grow.
- **CSV over a streaming source.** A single dispatch run is batch by nature. Kafka / CDC ingestion is on the roadmap for tracking-event updates.
- **SQLite over Postgres.** Single-file, zero-config, sufficient for session memory. The `Memory` interface keeps swap cost low.

---

## Numbers you can quote from the code

- **4** input CSVs, **5** agents, **4** registered tools, **4** services.
- **Sample run in `app/reports/`:** 31 clusters, 44.31 km total routing distance, 65/100 risky orders flagged.
- **9 generated dispatch memos** across 2026-05-16 → 2026-05-17 prove the loop runs end-to-end.
- **3 km** cluster radius. Haversine great-circle math everywhere distance is touched.
- **LLM:** planner at T=0 (deterministic JSON), memo at T=0.2.

---

## Roadmap

- **OR-Tools VRP** with capacity + time-window constraints once cluster sizes pass ~30 stops.
- **RoutingProvider interface** — pluggable real-time traffic ETAs from OSRM / Google.
- **Driver assignment agent** with shift, break, and skill constraints.
- **Slack delivery + webhook** on `dispatched` so the ops desk gets the memo without polling.
- **Kafka / CDC ingestion** to replace static CSVs once tracking is live.
- **OpenTelemetry traces** around `AgentRuntime` so per-agent latency is visible in any OTLP backend.
