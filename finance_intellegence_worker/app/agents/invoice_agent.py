from app.agents.state import FinanceAgentState
from app.tools.setup_tools import tool_registry


class InvoiceAgent:
    name = "InvoiceAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        tool = tool_registry.get_tool("invoice_matching_tool")
        state.invoice_analysis = tool.run()
        return state