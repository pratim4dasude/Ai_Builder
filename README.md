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

---

## Honest status — where this v0 stands

Posting this so a reviewer doesn't have to dig. The brief explicitly scores eval-honesty, so calling out what's open before it gets found.

### What's solid
- 3 workers behind one 8-layer shape — learn one, you know the others.
- Numbers are computed in Pandas services and *narrated* by the LLM, never invented by it. The citation contract has the right architecture.
- Per-row citation metadata on ingest (logistics) and per-claim citation builders (finance, growth).
- SQLite memory + follow-up resolver per worker.
- Gradio launcher boots the trio in one command.

### What's open

**1. Real SaaS data sources.** The brief asks for 3 proper SaaS connectors. Today the *abstraction* is real (`*_worker/app/connectors/base*.py`) but every concrete subclass reads a CSV. No live Shopify / Stripe / Shiprocket — I don't have sandbox credentials yet and didn't want to fake live calls. **Intended shape:** put a fixture HTTP layer (paginated, token-auth, rate-limited) in front of the existing CSVs so the connector code-path actually speaks HTTP, then swap the fixture URL for the real one when credentials land. Same `BaseConnector` interface, no refactor needed.

**2. Auth.** Single API-key gateway in front of the three workers is in the roadmap, not built. `session_id` is not tenant-namespaced — fine for one merchant, breaks the moment a second one connects.

**3. Eval harness.** Listed in the roadmap, not implemented. Intended shape: golden-answer regression per worker, LLM-as-judge for prose, numeric tolerances for KPIs, ~20 questions per worker.

**4. LLM vs. human authorship.** Architectural decisions, schema, orchestration logic, service-layer Pandas — written by hand. LLM (Claude) was used for: scaffolding agent classes, drafting prompts in `prompts.py`, and templating the dispatch memo. A per-file breakdown will land before final submission.

### Autonomous agent — concrete sketch

The brief asks for one "AI employee" that watches data, proposes a ₹-saving action, logs reasoning, and **does not send**. Proposed shape (not yet wired — this is the design):

**Where:** `logistics_operations_worker/app/runtime/watcher.py` (reuses the existing `agent_runtime.py` for `run_id` + timing + status).

**Why logistics:** `agent_runtime.py` already emits run-id / duration / status — least scaffolding to add. Courier-mix is also the cleanest ₹-savings story for a D2C founder.

**Trigger:** interval (`--every 6h`) or one-shot (`--once`). No webhook, no queue — local cron for v0.

**Data:** existing `orders.csv`, `shipments.csv`, `warehouses.csv`, `inventory.csv`.

**Decision rule:** for each origin→destination lane with ≥30 shipments in the last 7 days, compute cost-per-delivered by courier. If the current dominant courier on that lane is >15% above the cheapest courier that *also* meets the lane's SLA, emit a switch proposal.

**Action format — appended to `runs/agent_runs.jsonl`, never sent:**

```json
{
  "run_id": "watcher_2026-05-17T18:00:00Z_a3f1",
  "trigger": "cron",
  "lane": "BLR->DEL",
  "current_courier": "Delhivery",
  "proposed_courier": "Shiprocket",
  "current_cpd_inr": 78,
  "proposed_cpd_inr": 54,
  "projected_monthly_saving_inr": 12400,
  "evidence": ["shipments#row_412", "shipments#row_887", "shipments#row_904"],
  "reasoning": "Last 7d on BLR->DEL: Delhivery shipped 412 parcels @ avg ₹78. Shiprocket shipped 89 @ avg ₹54 with on-time 94% >= SLA. Saves ~₹24/parcel x ~520 monthly = ₹12,400/mo.",
  "confidence": 0.74,
  "do_not_send": true
}
```

**Failure modes (called out up front):**
- Thin lanes (<30 shipments) get suppressed — small-sample noise.
- Promo windows are ignored — a switch proposal during a sale week is suspect.
- SLA is measured on past data; if the proposed courier just started serving the lane, the comparison is unfair.
- One-step rule — doesn't capture multi-leg cost trade-offs (e.g. hub consolidation).

### Scale — what breaks at 10k merchants

| Bottleneck | First failure | Plan to absorb |
|---|---|---|
| In-memory Pandas per request | ~1–2k merchants | Per-merchant DuckDB files on object storage; load on demand. |
| Single SQLite writer per worker | ~1k writes/s | Per-merchant DB shards, or Postgres with row-level tenant isolation. |
| Synchronous LLM calls in `/chat` | p99 latency = OpenAI's p99 | Async client + cached embeddings + memo cache for repeated questions. |
| Connectors poll on demand | API rate limits hit fast | Queue (Celery / Cloud Tasks) running connectors in background, writing to per-merchant store. |
| Watcher runs in-process | Single-process bottleneck | Move watcher to a worker queue; one run per merchant in parallel. |


### Future Improvements
- Wire the watcher above; let it run 3 days against a real merchant; tune the 15% threshold and confidence calc.
- Replace one CSV connector with a real Shopify sandbox end-to-end.
- Build the eval harness — 20 golden questions per worker, numeric tolerances on KPIs.
- Tenant-namespace memory + add the API-key gateway.
- Promote provenance to a single `UniversalRow` shape across all three workers (logistics already does this — extend to finance and growth).
