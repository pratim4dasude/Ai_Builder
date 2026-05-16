from app.agents.state import FinanceAgentState
from app.tools.setup_tools import tool_registry


class StatisticsAgent:
    name = "StatisticsAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        tool = tool_registry.get_tool("statistics_tool")
        state.statistics_analysis = tool.run(period=state.period)
        return state