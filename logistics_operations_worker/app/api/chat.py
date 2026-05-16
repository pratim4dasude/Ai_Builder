import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.router import MultiAgentRouter
from app.agents.state import LogisticsAgentState
from app.utils.sse import sse_event

router = APIRouter()


class ChatRequest(BaseModel):
    query: str

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
        "warehouse_agent": "warehouse_assignment_service.assign_warehouses()",
        "clustering_agent": "clustering_service.cluster_orders()",
        "routing_agent": "route_service.generate_routes()",
        "risk_agent": "risk_service.detect_risks()",
        "memo_agent": "memo_service.generate_dispatch_memo()",
    }
    return tools.get(agent_name, "unknown_tool")


def get_agent_result(agent_name: str, state: LogisticsAgentState):
    results = {
        "warehouse_agent": state.warehouse_plan,
        "clustering_agent": state.clusters,
        "routing_agent": state.routes,
        "risk_agent": state.risks,
        "memo_agent": {"memo_preview": state.final_memo[:300] if state.final_memo else None},
    }
    return results.get(agent_name)

@router.post("/chat")
def chat(request: ChatRequest):
    agent_router = MultiAgentRouter()
    result = agent_router.run(request.query)

    return {
        "query": result.user_query,
        "city": result.city,
        "date": result.date,
        "selected_agents": result.selected_agents,
        "steps": [step.dict() for step in result.steps],
        "runtime_logs": result.runtime_logs,
        "outputs": {
            "warehouse_plan": result.warehouse_plan,
            "clusters": {
                "total_clusters": result.clusters.get("total_clusters"),
                "sample_clusters": result.clusters.get("sample_clusters", [])[:5],
            },
            "routes": {
                "total_clusters_routed": result.routes.get("total_clusters_routed"),
                "estimated_total_route_distance_km": result.routes.get("estimated_total_route_distance_km"),
                "sample_routes": result.routes.get("sample_routes", [])[:5],
            },
            "risks": {
                "total_risky_orders": result.risks.get("total_risky_orders"),
                "risk_counts": result.risks.get("risk_counts"),
                "sample_risks": result.risks.get("sample_risks", [])[:5],
            },
        },
        "final_memo": result.final_memo,
    }

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        state = LogisticsAgentState(user_query=request.query)
        agent_router = MultiAgentRouter()

        yield sse_event("status", {
            "stage": "started",
            "message": "Multi-agent logistics workflow started",
            "query": request.query,
        })
        await asyncio.sleep(0.3)

        yield sse_event("agent_started", {
            "agent": "SupervisorAgent",
            "task": "Analyze user request and decide required specialist agents",
        })

        state = agent_router.supervisor.plan(state)

        yield sse_event("agent_completed", {
            "agent": "SupervisorAgent",
            "selected_agents": state.selected_agents,
            "reason": "Dispatch planning needs warehouse assignment, clustering, routing, risk detection and memo generation",
        })
        await asyncio.sleep(0.3)

        for agent_name in state.selected_agents:
            agent = agent_router.agent_map[agent_name]

            yield sse_event("agent_started", {
                "agent": agent.name,
                "stage": agent_name,
                "task": get_agent_task(agent_name),
                "tool_called": get_agent_tool(agent_name),
            })
            await asyncio.sleep(0.3)

            state = agent.run(state)

            yield sse_event("tool_result", {
                "agent": agent.name,
                "stage": agent_name,
                "result": get_agent_result(agent_name, state),
            })
            await asyncio.sleep(0.3)

            yield sse_event("agent_completed", {
                "agent": agent.name,
                "stage": agent_name,
                "message": f"{agent.name} completed successfully",
            })
            await asyncio.sleep(0.3)

        yield sse_event("final", {
            "query": state.user_query,
            "selected_agents": state.selected_agents,
            "summary": {
                "warehouse_plan": state.warehouse_plan,
                "clusters": state.clusters,
                "routes": state.routes,
                "risks": state.risks,
            },
            "steps": [step.dict() for step in state.steps],
            "final_memo": state.final_memo,
        })

    return EventSourceResponse(event_generator())

from app.connectors.connector_manager import ConnectorManager


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
        }
    }