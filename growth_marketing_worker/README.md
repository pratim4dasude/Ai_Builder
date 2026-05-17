# Growth Marketing Worker

Agentic growth memo engine for D2C ecommerce. Picks the product to promote, the channel, the posting window, the target segment, and writes six channel-specific captions — all gated by a transparent scoring formula and a topologically-ordered agent graph.

---

## What it does

- Loads `products.csv`, `sales.csv`, `campaigns.csv`, `customers.csv`, `content_calendar.csv`.
- Routes the query to one of six intents (`risk`, `campaign`, `posting`, `segment`, `content`, `sales`) — promotion is the default.
- Runs the eight agents in a dependency-aware order (no implicit chaining).
- Computes a **deterministic promotion score** under the LLM, not on top of it:
  `0.35·sales_growth + 0.25·campaign_engagement + 0.20·margin + 0.10·conversion − 0.10·risk`.
- Generates six content variants (Instagram, Facebook, WhatsApp, email subject, email body, LinkedIn) via OpenAI JSON-mode, with a safe fallback when no API key is set.
- Returns one **Growth Action Memo** with decision, score, channel, time, segment, city, confidence, next-best-actions, citations.

---

## Architecture

```
                           GROWTH MARKETING WORKER  (FastAPI :8002)

  Client                                                                       Disk / Store
 ┌──────┐  POST /chat        GET /growth/validate                            ┌─────────────┐
 │ User │  POST /chat/stream GET /growth/llm/status                          │ data/*.csv  │
 └───┬──┘                                                                    │ products,   │
     │ ChatRequest{query,session_id}                                         │ sales,      │
     ▼                                                                       │ campaigns,  │
 ┌──────────────────┐         ┌────────────────────┐                         │ customers,  │
 │   api/chat.py    │ <────── │ SQLiteConvoMemory  │                         │ content_cal │
 │ followup resolver│         │ growth_memory.db   │                         └─────┬───────┘
 └────────┬─────────┘         │ (conversations +   │                               │
          │                   │  session_context)  │                               │
          ▼                   └────────────────────┘                               │
 ┌──────────────────┐                                                              │
 │ SupervisorAgent  │  6 intents: risk / campaign / posting /                      │
 │     .plan()      │  segment / content / sales / promotion(default)              │
 └────────┬─────────┘                                                              │
          ▼                                                                        │
 ╔═══════════════════════════════════════════════════════════════════╗             │
 ║  GrowthOrchestrator.run()                                         ║             │
 ║                                                                   ║             │
 ║   1. _validate_data()  ──>  GrowthDataValidationService           ║<────────────┤
 ║   2. SupervisorAgent.plan() → selected_agents                     ║             │
 ║   3. _expand_dependencies()  -- topological sort over             ║             │
 ║                                 AGENT_DEPENDENCIES                ║             │
 ║                                                                   ║             │
 ║      sales_trend ─┐                                               ║             │
 ║      campaign_perf┤───> promotion_score ───> segment              ║             │
 ║      posting_time │                          │                    ║             │
 ║      risk         │                          ▼                    ║             │
 ║                   └──────────────────────> content ──> memo       ║             │
 ║                                                                   ║             │
 ║   4. for agent in ordered: MultiAgentRouter.run_agent(name)       ║             │
 ╚════════════════════════════╤══════════════════════════════════════╝             │
                              │                                                    │
                              ▼                                                    │
              ┌────────────────────────────────┐                                   │
              │   MultiAgentRouter (8 agents)  │                                   │
              └───────────────┬────────────────┘                                   │
                              ▼                                                    │
   ┌───────────────────────────────────────────────────────────────────┐           │
   │ SalesAnalyticsService       7-day rolling growth %                │           │
   │ CampaignAnalyticsService    CTR / ROAS / conv by channel          │           │
   │ PromotionScoringService     0.35*s + 0.25*e + 0.20*m + 0.10*c -   │           │
   │                             0.10*r  (top-20 promote, bottom-10)   │           │
   │ PostingTimeService          peak engagement window                │           │
   │ SegmentService              city + customer-type match            │           │
   │ risk rules                  6 heuristics (inactive/inv/refund/..) │           │
   │ ContentGenerationService    ──┐                                   │           │
   │ MemoService                   ├──> LLMService                     │           │
   │ ConfidenceService           ──┘    (OpenAI gpt-4o-mini,           │           │
   │ ActionPlanService                   JSON-mode, T=0.4/0.5,         │           │
   │                                     fallback dict on failure)     │           │
   └───────────────────────────┬───────────────────────────────────────┘           │
                               │   connectors load all 5 CSVs ─────────────────────┘
                               ▼
                 ┌────────────────────────────┐
                 │ GrowthAgentState (Pydantic)│  sales_trends, campaign_perf,
                 │ accumulates module outputs │  promotion_scores, posting_time,
                 └─────────────┬──────────────┘  target_segment, risk, content,
                               ▼                  final_memo, confidence, citations
                 ┌────────────────────────────┐
                 │ GrowthResponseFormatter    │
                 │  .format_chat_response()   │
                 └─────────────┬──────────────┘
                               ▼
                  JSON  /  SSE stream (started -> agent_started -> agent_completed -> completed)
                               │
                               └──> SQLiteConvoMemory.add_message + update_context
```

---

## Data flow

1. `api/chat.py` receives `ChatRequest{query, session_id}`.
2. `SQLiteConversationMemory.get_context()` + `resolve_followup_query()` rewrite `"why"`, `"caption"`, `"memo"`, `"compare"` against last product / channel / segment.
3. `GrowthOrchestrator.run()` loads the five CSVs and calls `GrowthDataValidationService.validate_all()` — invalid data short-circuits with an error memo.
4. `SupervisorAgent.plan()` sets `query_intent` and `selected_agents`.
5. `GrowthOrchestrator._expand_dependencies()` closes the dependency set (`promotion_score` requires `sales_trend` + `campaign_performance`, `segment` requires `promotion_score`, …) and topologically sorts.
6. `MultiAgentRouter.run_agent(name, state)` dispatches each agent to its Service. Outputs accumulate on `GrowthAgentState`.
7. `ContentGenerationService` and `MemoService` call `LLMService.generate_json()` (OpenAI JSON-mode). On any failure (no API key, parse error, network) they fall back to deterministic dict / string output — the endpoint never 500s on the LLM.
8. `ConfidenceService.calculate_confidence()` rolls up signal strength; `ActionPlanService.generate_next_best_actions()` proposes 3–5 follow-ups.
9. `GrowthResponseFormatter.format_chat_response()` builds the final JSON with `answer`, `citations`, `selected_agents`, `query_intent`.
10. Memory writes the assistant turn + extracted context (last product, channel, segment, city, posting_time).

---

## Module map

| Layer | Path | Key class / function |
|---|---|---|
| API | `app/api/chat.py` | `POST /chat`, `POST /chat/stream` |
| API | `app/api/growth.py` | `GET /growth/validate`, `GET /growth/llm/status` |
| Orchestrator | `app/orchestrator/growth_orchestrator.py` | `GrowthOrchestrator.run()`, `AGENT_DEPENDENCIES`, `AGENT_ORDER`, `_expand_dependencies()` |
| Supervisor | `app/agents/supervisor_agent.py` | `SupervisorAgent.plan()` (6 intents) |
| Router | `app/agents/router.py` | `MultiAgentRouter.run_agent()` |
| State | `app/agents/state.py` | `GrowthAgentState` (Pydantic) |
| Services | `app/services/sales_analytics_service.py` | 7-day rolling growth |
| Services | `app/services/campaign_analytics_service.py` | CTR / ROAS / conversion |
| Services | `app/services/promotion_scoring_service.py` | weighted score, top-20 / bottom-10 |
| Services | `app/services/posting_time_service.py` | peak engagement window |
| Services | `app/services/segment_service.py` | city / customer-type match |
| Services | `app/services/content_generation_service.py` | 6 channel variants |
| Services | `app/services/memo_service.py` | LLM JSON memo + fallback |
| Services | `app/services/confidence_service.py` | signal strength roll-up |
| Services | `app/services/action_plan_service.py` | next-best-actions |
| LLM | `app/services/llm_service.py` | `LLMService.generate_json()` / `generate_text()` |
| Memory | `app/memory/sqlite_memory.py` | `SQLiteConversationMemory` |
| Memory | `app/memory/followup_resolver.py` | `resolve_followup_query()` |
| Connectors | `app/connectors/{product,sales,campaign,customer,content_calendar}_connector.py` | CSV loaders |

---

## Tech stack

| Concern | Choice |
|---|---|
| HTTP framework | FastAPI + Uvicorn |
| Data | Pandas |
| LLM | OpenAI Python SDK, `gpt-4o-mini`, JSON-mode |
| Memory | SQLite (`growth_memory.db`, 2 tables) |
| Streaming | Server-Sent Events |
| State contract | Pydantic `GrowthAgentState` |
| Config | `python-dotenv` (`OPENAI_API_KEY`, `OPENAI_MODEL`, `USE_LLM`) |

---

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/chat` | Full Growth Action Memo |
| POST | `/chat/stream` | SSE — `started`, `agent_started`, `agent_completed`, `completed` |
| GET | `/growth/validate` | Schema + null checks on the 5 CSVs |
| GET | `/growth/llm/status` | LLM configuration sanity check |
| GET | `/` | Endpoint index |

Sample request:

```bash
curl -X POST http://127.0.0.1:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which product should we promote this week?", "session_id": "demo"}'
```

---

## Run it

```bash
pip install -r requirements.txt
cd growth_marketing_worker
python app/main.py            # serves on http://127.0.0.1:8002
```

`.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini   # optional
USE_LLM=true               # optional; set false to force fallback paths
```

---

## Implementation status

| Area | Status |
|---|---|
| Supervisor (6 intents) | done |
| Orchestrator with explicit `AGENT_DEPENDENCIES` graph | done |
| 8 agents (sales, campaign, promotion, posting, segment, risk, content, memo) | done |
| Promotion scoring formula | done |
| 6 content variants via JSON-mode + fallback | done |
| Confidence + next-best-actions | done |
| SQLite memory + followup resolution | done |
| Data validation endpoint | done |
| LLM status endpoint | done |
| SSE streaming | done |
| Risk model (currently 6 heuristics) → small classifier | next |
| Vector memory for prior winning campaigns | next |
| A/B harness for caption variants | next |

---

## Engineering highlights

- **Explicit dependency graph.** `AGENT_DEPENDENCIES` is a dict and `_expand_dependencies()` is a topological sort — no `if-else` chains. Adding a new agent is one entry, not a refactor.
- **Deterministic core, generative shell.** The promotion score is a fixed formula in `PromotionScoringService` so stakeholders can audit it. The LLM only writes captions and the memo narrative on top of pre-computed numbers.
- **Two-mode LLM service.** `LLMService.generate_json()` uses OpenAI `response_format={"type": "json_object"}` so every memo / content call returns parseable JSON. Any failure (missing key, parse error, network) falls back to a deterministic dict — the endpoint never 500s.
- **Followup resolver.** `resolve_followup_query()` expands `"why"`, `"caption"`, `"memo"`, `"compare"` against the last product / channel / segment recovered from `session_context`. Multi-turn without re-prompting the user.
- **Citation tracking on every Service.** Each analyzer appends `{metric, source_file, row_ids}` to `state.citations`. The final payload includes the data lineage, not just the answer.
- **Pydantic state.** `GrowthAgentState` is one typed object passed through the pipeline — no untyped dict-of-dicts, no agent-to-agent ad-hoc keys.

---

## Design trade-offs

- **Rule-based intent router over an LLM router.** Six intents, keyword-driven. Reproducible, traceable, free.
- **Topological sort over hardcoded ordering.** The dependency graph survives reordering; a new agent declares its dependencies and is automatically slotted in.
- **OpenAI structured output + fallback over LangChain / pydantic-ai.** One thin wrapper, no framework lock-in. The fallback path is the contract.
- **SQLite over a vector store (for now).** Session memory needs key-value recall, not similarity search. Vector memory is on the roadmap for *winning campaigns retrieval*, not chat history.

---

## Numbers you can quote from the code

- **5** CSV sources, **8** agents, **6** intents, **6** content variants per run.
- **Promotion score weights:** sales 0.35 + engagement 0.25 + margin 0.20 + conversion 0.10 − risk 0.10. Top-**20** promote, bottom-**10** avoid.
- **Sales trend:** 7-day rolling window.
- **LLM:** OpenAI `gpt-4o-mini`, temp 0.4 for JSON content, 0.5 for free-form, JSON-mode on the structured calls.

---

## Roadmap

- **Risk classifier.** Replace 6-rule heuristic with a small model trained on `refund_rate`, `inventory_days`, `campaign_engagement`.
- **A/B harness for captions.** Persist variant → outcome, feed winners back into prompt context.
- **Vector memory for past winners.** Embedding store keyed on product / segment so prior winning campaigns surface as exemplars.
- **Multi-tenant config.** Per-brand voice prompt + per-channel guardrails loaded by tenant id.
- **Delivery channels.** Push the memo to Slack / Notion / a brand drive; webhook on `approved`.
- **OpenTelemetry traces** around `MultiAgentRouter.run_agent` so per-agent latency is visible.
