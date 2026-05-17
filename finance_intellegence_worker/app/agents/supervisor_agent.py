from app.agents.state import FinanceAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: FinanceAgentState) -> FinanceAgentState:
        query = state.user_query.lower()

        selected_agents = ["period_agent"]

        revenue_keywords = [
            "forecast",
            "predict",
            "future",
            "revenue",
            "cashflow",
            "cash flow",
            "order amount",
            "sales",
            "income",
            "earning",
        ]

        invoice_keywords = [
            "invoice",
            "ocr",
            "bill",
            "reconcile",
            "mismatch",
            "duplicate",
            "payment match",
            "invoice match",
        ]

        leakage_keywords = [
            "leakage",
            "deduction",
            "dispute",
            "unpaid",
            "loss",
            "refund",
            "revenue loss",
            "payment gap",
        ]

        margin_keywords = [
            "margin",
            "expense",
            "profit",
            "cost",
            "refund",
            "net revenue",
            "profitability",
        ]

        statistics_keywords = [
            "statistics",
            "stats",
            "trend",
            "distribution",
            "anomaly",
            "risk",
            "insight",
            "summary",
            "performance",
        ]

        if any(word in query for word in revenue_keywords):
            selected_agents.append("revenue_agent")

        if any(word in query for word in invoice_keywords):
            selected_agents.append("invoice_agent")

        if any(word in query for word in leakage_keywords):
            selected_agents.append("leakage_agent")

        if any(word in query for word in margin_keywords):
            selected_agents.append("margin_agent")

        if any(word in query for word in statistics_keywords):
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

        if "memo_agent" not in selected_agents:
            selected_agents.append("memo_agent")

        state.selected_agents = self._dedupe(selected_agents)

        state.metadata["status"] = "planned"
        state.metadata["supervisor_agent"] = self.name
        state.metadata["selected_agents_count"] = len(state.selected_agents)

        return state

    def _dedupe(self, agents):
        seen = set()
        clean_agents = []

        for agent in agents:
            if agent not in seen:
                clean_agents.append(agent)
                seen.add(agent)

        return clean_agents