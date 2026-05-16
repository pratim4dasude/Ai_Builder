from app.agents.state import LogisticsAgentState
from app.tools.setup_tools import tool_registry


class RoutingAgent:
    name = "RoutingAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.clusters:
            state.routes = {
                "summary": "No clusters found. Run ClusteringAgent first.",
                "total_clusters_routed": 0,
                "estimated_total_route_distance_km": 0,
                "routes": [],
                "sample_routes": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Clusters not available, so routing was skipped",
            )

            return state

        tool = tool_registry.get_tool("generate_routes")

        if tool is None:
            state.routes = {
                "summary": "generate_routes tool not found in tool registry.",
                "total_clusters_routed": 0,
                "estimated_total_route_distance_km": 0,
                "routes": [],
                "sample_routes": [],
            }

            state.add_step(
                self.name,
                "failed",
                "generate_routes tool not found in tool registry",
            )

            return state

        state.routes = tool.run(state)

        state.add_step(
            self.name,
            "completed",
            f"Generated routes for {state.routes.get('total_clusters_routed', 0)} clusters",
        )

        return state