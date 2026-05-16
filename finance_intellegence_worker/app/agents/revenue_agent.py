from app.agents.state import FinanceAgentState
from app.tools.setup_tools import tool_registry


class RevenueAgent:
    name = "RevenueAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        tool = tool_registry.get_tool("revenue_forecast_tool")
        state.revenue_analysis = tool.run()
        return state