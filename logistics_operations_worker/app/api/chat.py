import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from typing import Optional
from app.agents.router import MultiAgentRouter
from app.agents.state import LogisticsAgentState
from app.connectors.connector_manager import ConnectorManager
from app.utils.sse import sse_event
from app.utils.response_formatter import format_chat_response
from app.memory.session_memory import session_memory

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


def get_agent_task(agent_name: str):
    tasks = {
        "warehouse_agent": "Assign pending orders to the best warehouse",
        "clustering_agent": "Group nearby delivery addresses into dispatch clusters",
        "routing_agent": "Generate delivery sequence for each cluster",
        "risk_agent": "Detect COD, RTO, delay and address risks",
        "memo_agent": "Generate final business-readable dispatch memo",
    }
    return tasks.get(agent_name, "Run specialist logistics task")


def get_agent_tool(agent_name: str):
    tools = {
        "warehouse_agent": "assign_warehouses",
        "clustering_agent": "create_clusters",
        "routing_agent": "generate_routes",
        "risk_agent": "analyze_risk",
        "memo_agent": "llm_generate_memo",
    }
    return tools.get(agent_name, "unknown_tool")


def get_agent_result(agent_name: str, state: LogisticsAgentState):
    if agent_name == "warehouse_agent":
        return {
            "assigned_orders": state.warehouse_plan.get("assigned_orders", 0),
            "unassigned_orders": state.warehouse_plan.get("unassigned_orders", 0),
            "warehouse_wise_count": state.warehouse_plan.get("warehouse_wise_count", {}),
            "sample_assignments": state.warehouse_plan.get("sample_assignments", [])[:3],
        }

    if agent_name == "clustering_agent":
        return {
            "total_clusters": state.clusters.get("total_clusters", 0),
            "sample_clusters": state.clusters.get("sample_clusters", [])[:3],
        }

    if agent_name == "routing_agent":
        return {
            "total_clusters_routed": state.routes.get("total_clusters_routed", 0),
            "estimated_total_route_distance_km": state.routes.get("estimated_total_route_distance_km", 0),
            "sample_routes": state.routes.get("sample_routes", [])[:3],
        }

    if agent_name == "risk_agent":
        return {
            "total_risky_orders": state.risks.get("total_risky_orders", 0),
            "risk_counts": state.risks.get("risk_counts", {}),
            "sample_risks": state.risks.get("sample_risks", [])[:3],
        }

    if agent_name == "memo_agent":
        return {
            "memo_preview": state.final_memo[:500] if state.final_memo else None,
        }

    return {}


@router.post("/chat")
def chat(request: ChatRequest):
    agent_router = MultiAgentRouter()
    final_state = agent_router.run(
        query=request.query,
        session_id=request.session_id,
    )

    return format_chat_response(final_state)

#
# @router.post("/chat/stream")
# async def chat_stream(request: ChatRequest):
#     async def event_generator():
#         state = LogisticsAgentState(
#             user_query=request.query,
#             session_id=request.session_id,
#         )
#         agent_router = MultiAgentRouter()
#
#         yield sse_event("status", {
#             "stage": "started",
#             "message": "Multi-agent logistics workflow started",
#             "query": request.query,
#         })
#         await asyncio.sleep(0.3)
#
#         yield sse_event("agent_started", {
#             "agent": "SupervisorAgent",
#             "task": "Analyze user request and decide required specialist agents",
#         })
#
#         state = agent_router.supervisor.plan(state)
#
#         yield sse_event("agent_completed", {
#             "agent": "SupervisorAgent",
#             "selected_agents": state.selected_agents,
#             "reason": "Dispatch planning needs warehouse assignment, clustering, routing, risk detection and memo generation",
#         })
#         await asyncio.sleep(0.3)
#
#         for agent_name in state.selected_agents:
#             agent = agent_router.agent_map[agent_name]
#
#             yield sse_event("agent_started", {
#                 "agent": agent.name,
#                 "stage": agent_name,
#                 "task": get_agent_task(agent_name),
#                 "tool_called": get_agent_tool(agent_name),
#             })
#             await asyncio.sleep(0.3)
#
#             state = agent.run(state)
#
#             yield sse_event("tool_result", {
#                 "agent": agent.name,
#                 "stage": agent_name,
#                 "result": get_agent_result(agent_name, state),
#             })
#             await asyncio.sleep(0.3)
#
#             yield sse_event("agent_completed", {
#                 "agent": agent.name,
#                 "stage": agent_name,
#                 "message": f"{agent.name} completed successfully",
#             })
#             await asyncio.sleep(0.3)
#
#         yield sse_event("final", format_chat_response(state))
#
#     return EventSourceResponse(event_generator())
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        agent_router = MultiAgentRouter()

        yield sse_event("status", {
            "stage": "started",
            "message": "Multi-agent logistics workflow started",
            "query": request.query,
        })
        await asyncio.sleep(0.3)

        yield sse_event("status", {
            "stage": "planning",
            "message": "Planning agents and execution graph",
        })
        await asyncio.sleep(0.3)

        final_state = agent_router.run(
            query=request.query,
            session_id=request.session_id,
        )

        yield sse_event("agent_completed", {
            "agent": "SupervisorAgent",
            "selected_agents": final_state.selected_agents,
            "execution_plan": final_state.execution_plan,
            "message": "Planner created dependency-aware execution plan",
        })
        await asyncio.sleep(0.3)

        for log in final_state.runtime_logs:
            yield sse_event("agent_completed", {
                "agent": log["agent"],
                "status": log["status"],
                "execution_time_seconds": log["execution_time_seconds"],
                "message": f'{log["agent"]} completed successfully',
            })
            await asyncio.sleep(0.2)

        yield sse_event("report_generated", {
            "memo_file_path": final_state.memo_file_path,
        })
        await asyncio.sleep(0.3)

        yield sse_event("final", format_chat_response(final_state))

    return EventSourceResponse(event_generator())


@router.get("/connectors/test")
def test_connectors():
    manager = ConnectorManager()
    data = manager.load_all()

    return {
        "orders": len(data["orders"]),
        "shipments": len(data["shipments"]),
        "warehouses": len(data["warehouses"]),
        "inventory": len(data["inventory"]),
        "columns": {
            "orders": list(data["orders"].columns),
            "shipments": list(data["shipments"].columns),
            "warehouses": list(data["warehouses"].columns),
            "inventory": list(data["inventory"].columns),
        },
    }

@router.get("/memory/{session_id}")
def get_memory(session_id: str):
    return {
        "session_id": session_id,
        "history": session_memory.get_history(session_id),
        "last_run": session_memory.get_last_run(session_id),
    }