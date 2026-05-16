from app.agents.state import LogisticsAgentState
from app.services.clustering_service import cluster_assigned_orders


class ClusteringAgent:
    name = "ClusteringAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.warehouse_plan:
            state.clusters = {
                "summary": "No warehouse plan found. Run WarehouseAgent first.",
                "total_clusters": 0,
                "clusters": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Warehouse plan not available, so clustering was skipped",
            )

            return state

        assignments = state.warehouse_plan.get("assignments", [])

        if not assignments:
            state.clusters = {
                "summary": "No assigned orders available for clustering.",
                "total_clusters": 0,
                "clusters": [],
            }

            state.add_step(
                self.name,
                "completed",
                "No assigned orders found for clustering",
            )

            return state

        state.clusters = cluster_assigned_orders(
            assignments=assignments,
            radius_km=3.0,
        )

        state.add_step(
            self.name,
            "completed",
            f"Created {state.clusters.get('total_clusters', 0)} delivery clusters",
        )

        return state