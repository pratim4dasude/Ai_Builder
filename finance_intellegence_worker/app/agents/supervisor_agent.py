from app.agents.state import FinanceAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: FinanceAgentState) -> FinanceAgentState:
        query = state.user_query.lower()

        selected_agents = []

        if any(word in query for word in ["forecast", "revenue", "cashflow", "order amount"]):
            selected_agents.append("revenue_agent")

        if any(word in query for word in ["invoice", "ocr", "bill", "reconcile", "mismatch"]):
            selected_agents.append("invoice_agent")

        if any(word in query for word in ["leakage", "deduction", "dispute", "unpaid", "loss"]):
            selected_agents.append("leakage_agent")

        if any(word in query for word in ["margin", "refund", "expense", "profit", "cost"]):
            selected_agents.append("margin_agent")

        if not selected_agents:
            selected_agents = [
                "revenue_agent",
                "invoice_agent",
                "leakage_agent",
                "margin_agent",
            ]

        selected_agents.append("memo_agent")

        state.selected_agents = selected_agents
        return state