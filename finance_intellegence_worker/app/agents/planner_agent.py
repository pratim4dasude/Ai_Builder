from app.agents.state import FinanceAgentState


class PlannerAgent:
    name = "PlannerAgent"

    def create_plan(self, state: FinanceAgentState) -> FinanceAgentState:
        parallel_agents = [
            agent for agent in state.selected_agents
            if agent != "memo_agent"
        ]

        state.execution_plan = [
            {
                "step": 1,
                "mode": "parallel",
                "agents": parallel_agents,
                "reason": "Finance analysis agents can run independently.",
            },
            {
                "step": 2,
                "mode": "sequential",
                "agents": ["memo_agent"],
                "reason": "Memo agent needs all analysis outputs first.",
            },
        ]

        return state