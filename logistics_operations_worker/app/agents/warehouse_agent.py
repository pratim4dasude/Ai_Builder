from app.agents.state import LogisticsAgentState
from app.tools.setup_tools import tool_registry


class WarehouseAgent:
    name = "WarehouseAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        tool = tool_registry.get_tool("assign_warehouses")

        if tool is None:
            state.add_step(
                self.name,
                "failed",
                "assign_warehouses tool not found in tool registry",
            )
            return state

        result = tool.run(state)

        state.warehouse_plan = result

        state.add_step(
            self.name,
            "completed",
            f"Assigned {result.get('assigned_orders', 0)} out of {result.get('pending_orders_checked', 0)} pending orders",
        )

        return state