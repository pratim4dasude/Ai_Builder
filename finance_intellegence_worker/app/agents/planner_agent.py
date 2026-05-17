from app.agents.state import FinanceAgentState


class PlannerAgent:
    name = "PlannerAgent"

    def create_plan(self, state: FinanceAgentState) -> FinanceAgentState:
        selected = state.selected_agents

        parallel_agents = [
            agent for agent in selected
            if agent not in [
                "period_agent",
                "statistics_agent",
                "memo_agent",
            ]
        ]

        execution_plan = []

        if "period_agent" in selected:
            execution_plan.append({
                "step": 1,
                "mode": "sequential",
                "agents": ["period_agent"],
                "reason": "Period agent detects the requested time range before other finance agents run.",
            })

        if parallel_agents:
            execution_plan.append({
                "step": 2,
                "mode": "parallel",
                "agents": parallel_agents,
                "reason": "Core finance agents can run independently after the period is resolved.",
            })

        if "statistics_agent" in selected:
            execution_plan.append({
                "step": 3,
                "mode": "sequential",
                "agents": ["statistics_agent"],
                "reason": "Statistics agent calculates deeper metrics, trends, anomalies and risk flags.",
            })

        if "memo_agent" in selected:
            execution_plan.append({
                "step": 4,
                "mode": "sequential",
                "agents": ["memo_agent"],
                "reason": "Memo agent creates the final business-friendly finance response.",
            })

        for index, step in enumerate(execution_plan, start=1):
            step["step"] = index

        state.execution_plan = execution_plan

        state.metadata["status"] = "execution_plan_created"
        state.metadata["planner_agent"] = self.name
        state.metadata["execution_steps"] = len(execution_plan)

        return state