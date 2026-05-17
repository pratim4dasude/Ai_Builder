import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.state import GrowthAgentState
from app.agents.router import MultiAgentRouter
from app.utils.sse import sse_event
from app.utils.response_formatter import GrowthResponseFormatter

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


def _agent_output_key(agent_name: str) -> str:
    mapping = {
        "sales_trend_agent": "sales_trends",
        "campaign_performance_agent": "campaign_performance",
        "promotion_score_agent": "promotion_scores",
        "posting_time_agent": "posting_time",
        "segment_agent": "target_segment",
        "risk_agent": "risk_analysis",
        "content_agent": "generated_content",
        "memo_agent": "final_memo",
    }
    return mapping.get(agent_name, "final_memo")


def run_growth_workflow(request: ChatRequest) -> GrowthAgentState:
    state = GrowthAgentState(
        user_query=request.query,
        session_id=request.session_id,
    )

    agent_router = MultiAgentRouter()

    state = agent_router.supervisor.plan(state)

    for agent_name in state.selected_agents:
        state = agent_router.run_agent(agent_name, state)

    return state

@router.post("/chat")
async def chat(request: ChatRequest):
    state = run_growth_workflow(request)

    return GrowthResponseFormatter().format_chat_response(state)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        state = GrowthAgentState(
            user_query=request.query,
            session_id=request.session_id,
        )

        agent_router = MultiAgentRouter()

        yield sse_event("status", {
            "stage": "started",
            "message": "Growth Marketing Worker started",
            "query": request.query,
        })
        await asyncio.sleep(0.2)

        yield sse_event("agent_started", {
            "agent": "SupervisorAgent",
            "task": "Analyze user query and select marketing specialist agents",
        })

        state = agent_router.supervisor.plan(state)

        yield sse_event("agent_completed", {
            "agent": "SupervisorAgent",
            "selected_agents": state.selected_agents,
            "reason": "Selected agents based on marketing query intent",
        })
        await asyncio.sleep(0.2)

        for agent_name in state.selected_agents:
            yield sse_event("agent_started", {
                "agent": agent_name,
                "task": f"Running {agent_name}",
            })
            await asyncio.sleep(0.2)

            state = agent_router.run_agent(agent_name, state)

            yield sse_event("agent_completed", {
                "agent": agent_name,
                "output": getattr(state, _agent_output_key(agent_name), {}),
            })
            await asyncio.sleep(0.2)

        yield sse_event("completed", {
            "message": "Growth Marketing Worker workflow completed",
            "result": GrowthResponseFormatter().format_stream_completed_response(state),
        })

    return EventSourceResponse(event_generator())