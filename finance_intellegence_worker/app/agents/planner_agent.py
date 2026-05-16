from app.agents.state import FinanceAgentState


class PlannerAgent:
    name = "PlannerAgent"

    def create_plan(self, state: FinanceAgentState) -> FinanceAgentState:
        parallel_agents = [
            agent for agent in state.selected_agents
            if agent not in [
                "period_agent",
                "statistics_agent",
                "memo_agent",
            ]
        ]

        state.execution_plan = [
            {
                "step": 1,
                "mode": "sequential",
                "agents": ["period_agent"],
                "reason": "Period agent detects the time range before other agents run.",
            },
            {
                "step": 2,
                "mode": "parallel",
                "agents": parallel_agents,
                "reason": "Core finance agents can run independently after the period is resolved.",
            },
            {
                "step": 3,
                "mode": "sequential",
                "agents": ["statistics_agent"],
                "reason": "Statistics agent calculates deeper metrics and risk flags for the selected period.",
            },
            {
                "step": 4,
                "mode": "sequential",
                "agents": ["memo_agent"],
                "reason": "Memo agent needs all finance outputs and statistics before final response.",
            },
        ]

        return state