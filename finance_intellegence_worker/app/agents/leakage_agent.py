from app.agents.state import FinanceAgentState
from app.tools.setup_tools import tool_registry


class LeakageAgent:
    name = "LeakageAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        tool = tool_registry.get_tool("leakage_detection_tool")
        state.leakage_analysis = tool.run(period=state.period)
        return state