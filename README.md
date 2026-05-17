# AI Builder

Three composable agent workers behind one Gradio control panel. Each worker is a self-contained FastAPI service that wraps a multi-agent pipeline over a domain CSV bundle and returns a structured "memo" plus the raw analytical data.

```
finance_intellegence_worker     CFO copilot           -> CFO memo + risk flags
growth_marketing_worker         Growth strategist     -> Growth Action Memo
logistics_operations_worker     Dispatch planner      -> Markdown dispatch memo
```

The three workers do not share code, but they share the **same 8-layer shape** — once you understand one, you understand the other two.

---

## System overview

```
                                AI BUILDER  -  system overview

                              ┌──────────────────────────────┐
                              │   gradio_frontend/app.py     │
                              │   ┌──────────────────────┐   │
                              │   │  Gradio control UI   │   │
                              │   └──────────┬───────────┘   │
                              │              │ subprocess.Popen
                              │              │ + health-check
                              └──────────────┼───────────────┘
                                             │
                  ┌──────────────────────────┼──────────────────────────┐
                  │                          │                          │
                  ▼                          ▼                          ▼
        ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
        │  Finance Worker  │       │ Logistics Worker │       │  Growth Worker   │
        │   FastAPI :8001  │       │  FastAPI :8000   │       │  FastAPI :8002   │
        └────────┬─────────┘       └────────┬─────────┘       └────────┬─────────┘
                 │                          │                          │
                 │   Each worker follows the SAME 8-layer shape:       │
                 │                                                     │
                 │     api  ->  Supervisor  ->  Planner/Orchestrator   │
                 │              |                                      │
                 │            Agents  ->  Tools  ->  Services          │
                 │              |                                      │
                 │            Connectors (CSV)                         │
                 │              |                                      │
                 │            Memory (SQLite, per-worker .db)          │
                 │              |                                      │
                 │            Response formatter + SSE                 │
                 │                                                     │
                 ▼                          ▼                          ▼
        ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
        │ data/*.csv       │       │ data/*.csv       │       │ data/*.csv       │
        │ 5 ledgers        │       │ orders, ship,    │       │ products, sales, │
        │                  │       │ warehouses, inv  │       │ campaigns, etc.  │
        ├──────────────────┤       ├──────────────────┤       ├──────────────────┤
        │ finance_memory   │       │ logistics_memory │       │ growth_memory.db │
        │ .db              │       │ .db              │       │                  │
        ├──────────────────┤       ├──────────────────┤       ├──────────────────┤
        │ artifacts/models │       │ reports/*.md     │       │ (in-state memos) │
        │ XGBoost forecast │       │ dispatch memos   │       │                  │
        └──────────────────┘       └──────────────────┘       └──────────────────┘

                            All three call OpenAI gpt-4o-mini
                            via their own llm/ client wrapper
                            (graceful fallback when no API key).
```

---

## Workers at a glance

| Worker | Port | Role | Memo output | README |
|---|---|---|---|---|
| `finance_intellegence_worker` | 8001 | CFO copilot — revenue forecast, invoice reconciliation, leakage, margin, risk flags | CFO memo (LLM) + risk flags (deterministic) | [README](finance_intellegence_worker/README.md) |
| `growth_marketing_worker` | 8002 | Growth strategist — promotion scoring, posting time, segment, 6 content variants | Growth Action Memo with confidence + next-best-actions | [README](growth_marketing_worker/README.md) |
| `logistics_operations_worker` | 8000 | Dispatch planner — warehouse assignment, clustering, routing, risk | Markdown dispatch memo written to `reports/` | [README](logistics_operations_worker/README.md) |

---

## Repo layout

```
Ai_Builder/
├── README.md
├── requirements.txt
├── finance_intellegence_worker/
│   ├── README.md
│   ├── app/
│   │   ├── main.py                   # FastAPI app on :8001
│   │   ├── api/chat.py               # /chat, /chat/raw, /chat/stream
│   │   ├── agents/                   # Supervisor, Planner, 7 specialists
│   │   ├── runtime/agent_runtime.py  # asyncio.gather execution
│   │   ├── services/                 # 5 deterministic analyzers
│   │   ├── ml/revenue_xgboost.py     # 7-day forecast
│   │   ├── tools/setup_tools.py      # 6-tool ToolRegistry
│   │   ├── llm/client.py             # OpenAI gpt-4o-mini
│   │   ├── memory/sqlite_memory.py   # finance_memory.db
│   │   ├── connectors/csv_connector.py
│   │   └── utils/response_formatter.py
│   ├── data/                         # 5 CSV ledgers
│   └── artifacts/models/             # persisted XGBoost model
├── growth_marketing_worker/
│   ├── README.md
│   ├── app/
│   │   ├── main.py                   # FastAPI app on :8002
│   │   ├── api/                      # /chat, /chat/stream, /growth/validate, /growth/llm/status
│   │   ├── orchestrator/growth_orchestrator.py  # AGENT_DEPENDENCIES + topo sort
│   │   ├── agents/                   # Supervisor + MultiAgentRouter
│   │   ├── services/                 # 9 services incl. PromotionScoringService + LLMService
│   │   ├── memory/                   # growth_memory.db + followup_resolver
│   │   └── connectors/               # 5 typed CSV connectors
│   └── data/                         # 5 CSVs (products, sales, campaigns, customers, content_calendar)
├── logistics_operations_worker/
│   ├── README.md
│   ├── app/
│   │   ├── main.py                   # FastAPI app on :8000
│   │   ├── api/chat.py               # /chat, /chat/stream, /memory/{id}
│   │   ├── agents/                   # Supervisor + Planner (LLM DAG) + 4 specialists + Memo
│   │   ├── runtime/agent_runtime.py  # per-agent run_id, timing, status
│   │   ├── services/                 # warehouse_assignment, clustering, route, risk
│   │   ├── tools/                    # 4 tools + ToolRegistry
│   │   ├── llm/                      # OpenAI client + grounded memo prompt
│   │   ├── memory/                   # logistics_memory.db + followup_resolver
│   │   ├── utils/report_writer.py    # markdown export
│   │   └── connectors/csv_connector.py
│   ├── data/                         # orders, shipments, warehouses, inventory
│   └── reports/                      # generated dispatch memos
└── gradio_frontend/
    ├── app.py                        # boots all 3 workers as subprocesses
    └── outputs/
```

---

## Shared architectural conventions

Every worker follows the same eight-layer shape:

1. **API** — FastAPI router with `POST /chat` and `POST /chat/stream` (SSE).
2. **Supervisor** — keyword / intent / LLM router that picks the agent set.
3. **Planner / Orchestrator** — either an explicit dependency graph (growth) or an LLM-emitted JSON DAG (logistics) or a procedural runtime (finance).
4. **Agents** — thin wrappers, one per analytical capability.
5. **Tools / Services** — deterministic Pandas analyzers. The LLM is never asked to compute a number; it only narrates.
6. **Connectors** — CSV loaders with citation metadata.
7. **Memory** — SQLite (`conversations` + `session_context` tables) with a followup-query resolver that rewrites *"why"* / *"compare"* / *"memo"* against prior context.
8. **Response formatter + SSE** — packages the response payload and streams lifecycle events.

Learn it once, read the other two READMEs in five minutes.

---

## Run everything

The Gradio launcher boots all three workers via `subprocess.Popen` and exposes a unified chat UI:

```bash
pip install -r requirements.txt
python gradio_frontend/app.py
```

Or run a single worker directly:

```bash
# finance
python finance_intellegence_worker/app/main.py        # :8001

# growth
python growth_marketing_worker/app/main.py            # :8002

# logistics
python logistics_operations_worker/app/main.py        # :8000
```

Smoke test:

```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarise last 30 days", "session_id": "demo"}'
```

---

## Environment

A single `.env` at repo root is enough:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional; default used if absent
USE_LLM=true               # optional; set false to force deterministic fallbacks
```

Every LLM-touching call has a fallback path, so missing `OPENAI_API_KEY` will degrade the memo / captions to deterministic templates but will not crash any endpoint.

---

## Cross-cutting roadmap

- **Eval harness** — golden-answer regression on each worker's memo (LLM-as-judge for prose, numeric tolerances for KPIs).
- **OpenTelemetry** — uniform spans around runtime / orchestrator / router step boundaries; one OTLP endpoint visualises all three.
- **Dockerfile per worker + docker-compose** — reproducible boot for the trio with pinned Python and model versions.
- **Auth gateway** — single API-key gate in front of the three workers; `session_id` namespaced by tenant.
- **CI** — GitHub Actions: lint, type-check, smoke-test each `/chat` endpoint against a sample CSV bundle.
- **Shared `connectors/` package** — once one worker moves off CSV (DuckDB / Parquet / Postgres / Kafka), promote the interface to a shared library.

---

## Known issues

- `gradio_frontend/app.py` currently maps logistics to port `8002` and growth to port `8003`, but the workers listen on `8000` and `8002` respectively. The launcher's `WORKERS` dict needs to be corrected to match the `uvicorn.run(..., port=...)` lines in each `app/main.py`.

---

## Tech stack (shared)

| Concern | Choice |
|---|---|
| HTTP | FastAPI + Uvicorn |
| Data | Pandas |
| ML | XGBoost (finance only — 7-day revenue forecast) |
| LLM | OpenAI Python SDK, `gpt-4o-mini` |
| Streaming | Server-Sent Events |
| Memory | SQLite, two-table schema (`conversations`, `session_context`) |
| Geometry | Haversine (logistics) |
| Config | `python-dotenv` |
