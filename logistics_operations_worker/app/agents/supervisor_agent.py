from logistics_operations_worker.app.agents.state import LogisticsAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: LogisticsAgentState) -> LogisticsAgentState:
        query = state.user_query.lower()

        selected_agents = []

        if "dispatch" in query or "plan" in query:
            selected_agents = [
                "warehouse_agent",
                "clustering_agent",
                "routing_agent",
                "risk_agent",
                "memo_agent",
            ]

        elif "warehouse" in query:
            selected_agents = ["warehouse_agent", "memo_agent"]

        elif "cluster" in query or "group" in query:
            selected_agents = ["clustering_agent", "memo_agent"]

        elif "route" in query:
            selected_agents = ["routing_agent", "memo_agent"]

        elif "risk" in query or "rto" in query or "cod" in query:
            selected_agents = ["risk_agent", "memo_agent"]

        else:
            selected_agents = [
                "warehouse_agent",
                "clustering_agent",
                "routing_agent",
                "risk_agent",
                "memo_agent",
            ]

        state.selected_agents = selected_agents
        state.add_step(
            self.name,
            "completed",
            f"Selected agents: {', '.join(selected_agents)}",
        )

        return state