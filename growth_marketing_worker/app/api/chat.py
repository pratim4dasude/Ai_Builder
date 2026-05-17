import asyncio
from typing import Optional, Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.state import GrowthAgentState
from app.utils.sse import sse_event
from app.utils.response_formatter import GrowthResponseFormatter
from app.orchestrator.growth_orchestrator import GrowthOrchestrator
from app.memory.sqlite_memory import SQLiteConversationMemory
from app.memory.followup_resolver import resolve_followup_query


router = APIRouter()
memory_service = SQLiteConversationMemory()


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default-growth-session"


def _ensure_session_id(session_id: Optional[str]) -> str:
    return session_id or "default-growth-session"


def _extract_context_from_answer(
    original_query: str,
    resolved_query: str,
    answer: Dict[str, Any],
    state: GrowthAgentState,
) -> Dict[str, Any]:
    return {
        "last_query": original_query,
        "last_resolved_query": resolved_query,
        "last_intent": answer.get("query_intent") or getattr(state, "query_intent", None),

        "last_product_id": answer.get("product_id"),
        "last_product_name": answer.get("product_to_promote"),
        "last_sku": answer.get("sku"),

        "last_channel": answer.get("recommended_channel"),
        "last_posting_time": answer.get("recommended_posting_time"),
        "last_segment": answer.get("target_segment"),
        "last_city": answer.get("recommended_city"),
        "last_customer_type": answer.get("recommended_customer_type"),

        "last_promotion_score": answer.get("promotion_readiness_score"),
        "last_recommended_action": answer.get("recommended_action"),
        "last_products_to_avoid": answer.get("products_to_avoid"),
    }


def _prepare_memory_context(session_id: str, query: str):
    previous_context = memory_service.get_context(session_id)
    conversation_history = memory_service.get_history(session_id)

    resolved_query = resolve_followup_query(
        query=query,
        previous_context=previous_context,
    )

    return previous_context, conversation_history, resolved_query


def _run_orchestrator(
    resolved_query: str,
    session_id: str,
    previous_context: Dict[str, Any],
    conversation_history: list,
) -> GrowthAgentState:
    state = GrowthOrchestrator().run(
        query=resolved_query,
        session_id=session_id,
    )

    state.previous_context = previous_context
    state.conversation_history = conversation_history

    return state


def run_growth_workflow(request: ChatRequest) -> GrowthAgentState:
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

    state = _run_orchestrator(
        resolved_query=resolved_query,
        session_id=session_id,
        previous_context=previous_context,
        conversation_history=conversation_history,
    )

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

    state = _run_orchestrator(
        resolved_query=resolved_query,
        session_id=session_id,
        previous_context=previous_context,
        conversation_history=conversation_history,
    )

    response = GrowthResponseFormatter().format_chat_response(state)
    answer = response.get("answer", {})

    memory_service.add_message(
        session_id=session_id,
        role="assistant",
        message=answer,
    )

    memory_service.update_context(
        session_id=session_id,
        context=_extract_context_from_answer(
            original_query=request.query,
            resolved_query=resolved_query,
            answer=answer,
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

    return response


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

        yield sse_event("status", {
            "stage": "started",
            "message": "Growth Marketing Worker started",
            "query": request.query,
            "resolved_query": resolved_query,
            "memory_used": bool(previous_context),
        })
        await asyncio.sleep(0.2)

        yield sse_event("agent_started", {
            "agent": "GrowthOrchestrator",
            "task": "Validate data, plan dependencies, and run marketing agents",
        })
        await asyncio.sleep(0.2)

        state = _run_orchestrator(
            resolved_query=resolved_query,
            session_id=session_id,
            previous_context=previous_context,
            conversation_history=conversation_history,
        )

        yield sse_event("agent_completed", {
            "agent": "GrowthOrchestrator",
            "selected_agents": state.selected_agents,
            "query_intent": state.query_intent,
        })
        await asyncio.sleep(0.2)

        final_response = GrowthResponseFormatter().format_stream_completed_response(state)
        answer = final_response.get("answer", {})

        memory_service.add_message(
            session_id=session_id,
            role="assistant",
            message=answer,
        )

        memory_service.update_context(
            session_id=session_id,
            context=_extract_context_from_answer(
                original_query=request.query,
                resolved_query=resolved_query,
                answer=answer,
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

        yield sse_event("completed", {
            "message": "Growth Marketing Worker workflow completed",
            "result": final_response,
        })

    return EventSourceResponse(event_generator())