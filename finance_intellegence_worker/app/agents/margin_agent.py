from app.agents.state import FinanceAgentState
from app.tools.setup_tools import tool_registry


class MarginAgent:
    name = "MarginAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        tool = tool_registry.get_tool("margin_refund_tool")
        state.margin_analysis = tool.run(period=state.period)
        return state