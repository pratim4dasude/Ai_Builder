import asyncio

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

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: str


async def run_finance_workflow(request: ChatRequest) -> FinanceAgentState:
    state = FinanceAgentState(
        user_query=request.query,
        session_id=request.session_id,
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
    state = await run_finance_workflow(request)

    return build_finance_response(state)


@router.post("/chat/raw")
async def chat_raw(request: ChatRequest):
    state = await run_finance_workflow(request)

    response = {
        "session_id": state.session_id,
        "query": state.user_query,
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
    }

    return clean_json(response)


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    async def event_generator():
        state = FinanceAgentState(
            user_query=request.query,
            session_id=request.session_id,
        )

        supervisor = SupervisorAgent()
        planner = PlannerAgent()
        runtime = FinanceAgentRuntime()

        yield sse_event("status", {
            "stage": "started",
            "message": "Finance Intelligence workflow started.",
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

        yield sse_event(
            "final_output",
            build_stream_final_response(state),
        )

    return EventSourceResponse(event_generator())


@router.get("/validate-data")
async def validate_data():
    service = FinanceDataValidationService()

    return {
        "files": service.validate_required_files(),
        "columns": service.validate_columns(),
    }