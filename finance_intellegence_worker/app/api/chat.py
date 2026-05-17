# import asyncio
#
# from fastapi import APIRouter
# from pydantic import BaseModel
# from sse_starlette.sse import EventSourceResponse
#
# from app.services.data_validation import FinanceDataValidationService
# from app.agents.state import FinanceAgentState
# from app.agents.supervisor_agent import SupervisorAgent
# from app.agents.planner_agent import PlannerAgent
# from app.runtime.agent_runtime import FinanceAgentRuntime
# from app.utils.sse import sse_event
# from app.utils.json_cleaner import clean_json
# from app.utils.response_formatter import (
#     build_finance_response,
#     build_stream_final_response,
# )
#
# router = APIRouter()
#
#
# class ChatRequest(BaseModel):
#     query: str
#     session_id: str
#
#
# async def run_finance_workflow(request: ChatRequest) -> FinanceAgentState:
#     state = FinanceAgentState(
#         user_query=request.query,
#         session_id=request.session_id,
#     )
#
#     supervisor = SupervisorAgent()
#     planner = PlannerAgent()
#     runtime = FinanceAgentRuntime()
#
#     state = supervisor.plan(state)
#     state = planner.create_plan(state)
#
#     state = await runtime.run_plan(state)
#
#     return state
#
#
# @router.post("/chat")
# async def chat(request: ChatRequest):
#     state = await run_finance_workflow(request)
#
#     return build_finance_response(state)
#
#
# @router.post("/chat/raw")
# async def chat_raw(request: ChatRequest):
#     state = await run_finance_workflow(request)
#
#     response = {
#         "session_id": state.session_id,
#         "query": state.user_query,
#         "selected_agents": state.selected_agents,
#         "execution_plan": state.execution_plan,
#         "revenue_analysis": state.revenue_analysis,
#         "invoice_analysis": state.invoice_analysis,
#         "leakage_analysis": state.leakage_analysis,
#         "margin_analysis": state.margin_analysis,
#         "statistics_analysis": state.statistics_analysis,
#         "memo": state.final_memo,
#         "errors": state.errors,
#         "period": state.period,
#         "metadata": state.metadata,
#     }
#
#     return clean_json(response)
#
#
# @router.post("/chat/stream")
# async def chat_stream(request: ChatRequest):
#
#     async def event_generator():
#         state = FinanceAgentState(
#             user_query=request.query,
#             session_id=request.session_id,
#         )
#
#         supervisor = SupervisorAgent()
#         planner = PlannerAgent()
#         runtime = FinanceAgentRuntime()
#
#         yield sse_event("status", {
#             "stage": "started",
#             "message": "Finance Intelligence workflow started.",
#         })
#
#         yield sse_event("agent_started", {
#             "agent": "SupervisorAgent",
#             "task": "Select required finance specialist agents.",
#         })
#
#         state = supervisor.plan(state)
#
#         yield sse_event(
#             "agent_completed",
#             {
#                 "agent": "SupervisorAgent",
#                 "selected_agents": state.selected_agents,
#             },
#         )
#
#         yield sse_event("agent_started", {
#             "agent": "PlannerAgent",
#             "task": "Create sequential and parallel execution plan.",
#         })
#
#         state = planner.create_plan(state)
#
#         yield sse_event(
#             "agent_completed",
#             {
#                 "agent": "PlannerAgent",
#                 "execution_plan": state.execution_plan,
#             },
#         )
#
#         for step in state.execution_plan:
#             if step["mode"] == "parallel":
#                 yield sse_event("parallel_started", {
#                     "step": step["step"],
#                     "agents": step["agents"],
#                     "reason": step.get("reason"),
#                 })
#
#                 state = await runtime.run_parallel(step["agents"], state)
#
#                 yield sse_event("parallel_completed", {
#                     "step": step["step"],
#                     "agents": step["agents"],
#                 })
#
#             else:
#                 for agent_name in step["agents"]:
#                     yield sse_event("agent_started", {
#                         "agent": agent_name,
#                         "step": step["step"],
#                     })
#
#                     state = await runtime.run_agent(agent_name, state)
#
#                     yield sse_event("agent_completed", {
#                         "agent": agent_name,
#                         "step": step["step"],
#                     })
#
#         yield sse_event(
#             "final_output",
#             build_stream_final_response(state),
#         )
#
#     return EventSourceResponse(event_generator())
#
#
# @router.get("/validate-data")
# async def validate_data():
#     service = FinanceDataValidationService()
#
#     return {
#         "files": service.validate_required_files(),
#         "columns": service.validate_columns(),
#     }

import asyncio
from typing import Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.services.data_validation import FinanceDataValidationService
from app.agents.state import FinanceAgentState
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.planner_agent import PlannerAgent
from app.runtime.agent_runtime import FinanceAgentRuntime
from app.utils.sse import sse_event
from app.utils.json_cleaner import clean_json
from app.utils.response_formatter import (
    build_finance_response,
    build_stream_final_response,
)
from app.memory.sqlite_memory import SQLiteConversationMemory
from app.memory.followup_resolver import resolve_finance_followup_query


router = APIRouter()
memory_service = SQLiteConversationMemory()


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default-finance-session"


def _ensure_session_id(session_id: Optional[str]) -> str:
    return session_id or "default-finance-session"


def _prepare_memory_context(session_id: str, query: str):
    previous_context = memory_service.get_context(session_id)
    conversation_history = memory_service.get_history(session_id)

    resolved_query = resolve_finance_followup_query(
        query=query,
        previous_context=previous_context,
    )

    return previous_context, conversation_history, resolved_query


def _extract_finance_context(
    original_query: str,
    resolved_query: str,
    response: Dict[str, Any],
    state: FinanceAgentState,
) -> Dict[str, Any]:
    data = response.get("data", {})

    revenue_analysis = data.get("revenue_analysis") or response.get("revenue_analysis")
    invoice_analysis = data.get("invoice_analysis") or response.get("invoice_analysis")
    leakage_analysis = data.get("leakage_analysis") or response.get("leakage_analysis")
    margin_analysis = data.get("margin_analysis") or response.get("margin_analysis")
    statistics_analysis = data.get("statistics_analysis") or response.get("statistics_analysis")

    main_issue = None
    focus_area = None

    q = original_query.lower()

    if leakage_analysis or "leakage" in q or "refund" in q:
        main_issue = "revenue_leakage"
        focus_area = "leakage_analysis"
    elif invoice_analysis or "invoice" in q:
        main_issue = "invoice_risk"
        focus_area = "invoice_analysis"
    elif margin_analysis or "margin" in q:
        main_issue = "margin_performance"
        focus_area = "margin_analysis"
    elif revenue_analysis or "revenue" in q:
        main_issue = "revenue_performance"
        focus_area = "revenue_analysis"
    elif statistics_analysis:
        main_issue = "statistics_summary"
        focus_area = "statistics_analysis"

    return {
        "last_query": original_query,
        "last_resolved_query": resolved_query,
        "last_selected_agents": state.selected_agents,
        "last_execution_plan": state.execution_plan,
        "last_period": state.period,

        "last_main_issue": main_issue,
        "last_focus_area": focus_area,

        "last_revenue_analysis": revenue_analysis,
        "last_invoice_analysis": invoice_analysis,
        "last_leakage_analysis": leakage_analysis,
        "last_margin_analysis": margin_analysis,
        "last_statistics_analysis": statistics_analysis,

        "last_summary": response.get("summary"),
        "last_memo": response.get("answer") or response.get("memo") or response.get("final_memo"),
    }


async def run_finance_workflow(
    query: str,
    session_id: str,
    previous_context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[list] = None,
) -> FinanceAgentState:
    state = FinanceAgentState(
        user_query=query,
        session_id=session_id,
        previous_context=previous_context or {},
        conversation_history=conversation_history or [],
    )

    supervisor = SupervisorAgent()
    planner = PlannerAgent()
    runtime = FinanceAgentRuntime()

    state = supervisor.plan(state)
    state = planner.create_plan(state)

    state = await runtime.run_plan(state)

    return state


@router.post("/chat")
async def chat(request: ChatRequest):
    session_id = _ensure_session_id(request.session_id)

    previous_context, conversation_history, resolved_query = _prepare_memory_context(
        session_id=session_id,
        query=request.query,
    )

    memory_service.add_message(
        session_id=session_id,
        role="user",
        message=request.query,
    )

    state = await run_finance_workflow(
        query=resolved_query,
        session_id=session_id,
        previous_context=previous_context,
        conversation_history=conversation_history,
    )

    response = build_finance_response(state)

    memory_service.add_message(
        session_id=session_id,
        role="assistant",
        message=response,
    )

    memory_service.update_context(
        session_id=session_id,
        context=_extract_finance_context(
            original_query=request.query,
            resolved_query=resolved_query,
            response=response,
            state=state,
        ),
    )

    response["memory"] = {
        "enabled": True,
        "type": "sqlite",
        "session_id": session_id,
        "resolved_query": resolved_query,
        "previous_context_used": previous_context,
        "conversation_turns": len(conversation_history),
    }

    return clean_json(response)


@router.post("/chat/raw")
async def chat_raw(request: ChatRequest):
    session_id = _ensure_session_id(request.session_id)

    previous_context, conversation_history, resolved_query = _prepare_memory_context(
        session_id=session_id,
        query=request.query,
    )

    state = await run_finance_workflow(
        query=resolved_query,
        session_id=session_id,
        previous_context=previous_context,
        conversation_history=conversation_history,
    )

    response = {
        "session_id": state.session_id,
        "query": request.query,
        "resolved_query": resolved_query,
        "selected_agents": state.selected_agents,
        "execution_plan": state.execution_plan,
        "revenue_analysis": state.revenue_analysis,
        "invoice_analysis": state.invoice_analysis,
        "leakage_analysis": state.leakage_analysis,
        "margin_analysis": state.margin_analysis,
        "statistics_analysis": state.statistics_analysis,
        "memo": state.final_memo,
        "errors": state.errors,
        "period": state.period,
        "metadata": state.metadata,
        "memory": {
            "enabled": True,
            "type": "sqlite",
            "session_id": session_id,
            "previous_context_used": previous_context,
            "conversation_turns": len(conversation_history),
        }
    }

    return clean_json(response)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    async def event_generator():
        session_id = _ensure_session_id(request.session_id)

        previous_context, conversation_history, resolved_query = _prepare_memory_context(
            session_id=session_id,
            query=request.query,
        )

        memory_service.add_message(
            session_id=session_id,
            role="user",
            message=request.query,
        )

        state = FinanceAgentState(
            user_query=resolved_query,
            session_id=session_id,
            previous_context=previous_context,
            conversation_history=conversation_history,
        )

        supervisor = SupervisorAgent()
        planner = PlannerAgent()
        runtime = FinanceAgentRuntime()

        yield sse_event("status", {
            "stage": "started",
            "message": "Finance Intelligence workflow started.",
            "query": request.query,
            "resolved_query": resolved_query,
            "memory_used": bool(previous_context),
        })

        yield sse_event("agent_started", {
            "agent": "SupervisorAgent",
            "task": "Select required finance specialist agents.",
        })

        state = supervisor.plan(state)

        yield sse_event(
            "agent_completed",
            {
                "agent": "SupervisorAgent",
                "selected_agents": state.selected_agents,
            },
        )

        yield sse_event("agent_started", {
            "agent": "PlannerAgent",
            "task": "Create sequential and parallel execution plan.",
        })

        state = planner.create_plan(state)

        yield sse_event(
            "agent_completed",
            {
                "agent": "PlannerAgent",
                "execution_plan": state.execution_plan,
            },
        )

        for step in state.execution_plan:
            if step["mode"] == "parallel":
                yield sse_event("parallel_started", {
                    "step": step["step"],
                    "agents": step["agents"],
                    "reason": step.get("reason"),
                })

                state = await runtime.run_parallel(step["agents"], state)

                yield sse_event("parallel_completed", {
                    "step": step["step"],
                    "agents": step["agents"],
                })

            else:
                for agent_name in step["agents"]:
                    yield sse_event("agent_started", {
                        "agent": agent_name,
                        "step": step["step"],
                    })

                    state = await runtime.run_agent(agent_name, state)

                    yield sse_event("agent_completed", {
                        "agent": agent_name,
                        "step": step["step"],
                    })

        final_response = build_stream_final_response(state)

        memory_service.add_message(
            session_id=session_id,
            role="assistant",
            message=final_response,
        )

        memory_service.update_context(
            session_id=session_id,
            context=_extract_finance_context(
                original_query=request.query,
                resolved_query=resolved_query,
                response=final_response,
                state=state,
            ),
        )

        final_response["memory"] = {
            "enabled": True,
            "type": "sqlite",
            "session_id": session_id,
            "resolved_query": resolved_query,
            "previous_context_used": previous_context,
            "conversation_turns": len(conversation_history),
        }

        yield sse_event(
            "final_output",
            final_response,
        )

    return EventSourceResponse(event_generator())


@router.get("/validate-data")
async def validate_data():
    service = FinanceDataValidationService()

    return {
        "files": service.validate_required_files(),
        "columns": service.validate_columns(),
    }