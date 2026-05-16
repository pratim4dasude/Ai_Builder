from app.agents.state import FinanceAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: FinanceAgentState) -> FinanceAgentState:
        query = state.user_query.lower()

        selected_agents = ["period_agent"]

        if any(word in query for word in ["forecast", "revenue", "cashflow", "order amount", "sales"]):
            selected_agents.append("revenue_agent")

        if any(word in query for word in ["invoice", "ocr", "bill", "reconcile", "mismatch", "duplicate"]):
            selected_agents.append("invoice_agent")

        if any(word in query for word in ["leakage", "deduction", "dispute", "unpaid", "loss", "refund"]):
            selected_agents.append("leakage_agent")

        if any(word in query for word in ["margin", "expense", "profit", "cost", "refund"]):
            selected_agents.append("margin_agent")

        if any(word in query for word in ["statistics", "stats", "trend", "distribution", "anomaly", "risk", "insight"]):
            selected_agents.append("statistics_agent")

        if len(selected_agents) == 1:
            selected_agents.extend([
                "revenue_agent",
                "invoice_agent",
                "leakage_agent",
                "margin_agent",
            ])

        if "statistics_agent" not in selected_agents:
            selected_agents.append("statistics_agent")

        selected_agents.append("memo_agent")

        state.selected_agents = selected_agents
        return state