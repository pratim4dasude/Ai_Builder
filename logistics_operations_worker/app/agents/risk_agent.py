from app.agents.state import LogisticsAgentState
from app.tools.setup_tools import tool_registry


class RiskAgent:
    name = "RiskAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.warehouse_plan:
            state.risks = {
                "summary": "No warehouse plan found. Run WarehouseAgent first.",
                "total_orders_checked": 0,
                "total_risky_orders": 0,
                "risk_counts": {},
                "high_rto_areas": [],
                "sample_risks": [],
                "all_risks": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Warehouse plan not available, so risk detection was skipped",
            )

            return state

        tool = tool_registry.get_tool("analyze_risk")

        if tool is None:
            state.risks = {
                "summary": "analyze_risk tool not found in tool registry.",
                "total_orders_checked": 0,
                "total_risky_orders": 0,
                "risk_counts": {},
                "high_rto_areas": [],
                "sample_risks": [],
                "all_risks": [],
            }

            state.add_step(
                self.name,
                "failed",
                "analyze_risk tool not found in tool registry",
            )

            return state

        state.risks = tool.run(state)

        state.add_step(
            self.name,
            "completed",
            f"Detected {state.risks.get('total_risky_orders', 0)} risky orders",
        )

        return state