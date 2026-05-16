from logistics_operations_worker.app.agents.state import LogisticsAgentState
from logistics_operations_worker.app.agents.planner_agent import PlannerAgent


class SupervisorAgent:
    name = "SupervisorAgent"

    def __init__(self):
        self.planner = PlannerAgent()

    def fallback_plan(self, query: str):
        query = query.lower()

        if "dispatch" in query or "plan" in query:
            return [
                "warehouse_agent",
                "clustering_agent",
                "routing_agent",
                "risk_agent",
                "memo_agent",
            ]

        elif "warehouse" in query:
            return ["warehouse_agent", "memo_agent"]

        elif "cluster" in query or "group" in query:
            return ["clustering_agent", "memo_agent"]

        elif "route" in query:
            return ["routing_agent", "memo_agent"]

        elif "risk" in query or "rto" in query or "cod" in query:
            return ["risk_agent", "memo_agent"]

        return [
            "warehouse_agent",
            "clustering_agent",
            "routing_agent",
            "risk_agent",
            "memo_agent",
        ]

    def plan(self, state: LogisticsAgentState) -> LogisticsAgentState:
        try:
            plan_result = self.planner.plan(state.user_query)

            execution_plan = plan_result["execution_plan"]
            reason = plan_result["reason"]

            selected_agents = []

            for step in execution_plan:
                selected_agents.extend(step["agents"])

            state.execution_plan = execution_plan

            state.selected_agents = selected_agents
            state.add_step(
                self.name,
                "completed",
                f"LLM planner selected agents: {', '.join(selected_agents)} | Reason: {reason}",
            )

        except Exception as e:
            selected_agents = self.fallback_plan(state.user_query)

            state.selected_agents = selected_agents
            state.add_step(
                self.name,
                "fallback",
                f"LLM planner failed. Used fallback routing. Error: {str(e)}",
            )

        return state