from app.agents.state import LogisticsAgentState
from app.services.route_service import generate_routes_for_clusters


class RoutingAgent:
    name = "RoutingAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.clusters:
            state.routes = {
                "summary": "No clusters found. Run ClusteringAgent first.",
                "total_clusters_routed": 0,
                "routes": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Clusters not available, so routing was skipped",
            )

            return state

        state.routes = generate_routes_for_clusters(state.clusters)

        state.add_step(
            self.name,
            "completed",
            f"Generated routes for {state.routes.get('total_clusters_routed', 0)} clusters",
        )

        return state