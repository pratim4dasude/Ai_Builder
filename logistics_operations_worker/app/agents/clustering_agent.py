from app.agents.state import LogisticsAgentState
from app.tools.setup_tools import tool_registry


class ClusteringAgent:
    name = "ClusteringAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.warehouse_plan:
            state.clusters = {
                "summary": "No warehouse plan found. Run WarehouseAgent first.",
                "total_clusters": 0,
                "clusters": [],
                "sample_clusters": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Warehouse plan not available, so clustering was skipped",
            )

            return state

        tool = tool_registry.get_tool("create_clusters")

        if tool is None:
            state.clusters = {
                "summary": "create_clusters tool not found in tool registry.",
                "total_clusters": 0,
                "clusters": [],
                "sample_clusters": [],
            }

            state.add_step(
                self.name,
                "failed",
                "create_clusters tool not found in tool registry",
            )

            return state

        state.clusters = tool.run(state)

        state.add_step(
            self.name,
            "completed",
            f"Created {state.clusters.get('total_clusters', 0)} delivery clusters",
        )

        return state