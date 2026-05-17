import asyncio
from copy import deepcopy

from app.agents.revenue_agent import RevenueAgent
from app.agents.invoice_agent import InvoiceAgent
from app.agents.leakage_agent import LeakageAgent
from app.agents.margin_agent import MarginAgent
from app.agents.statistics_agent import StatisticsAgent
from app.agents.memo_agent import MemoAgent
from app.agents.period_agent import PeriodAgent


class FinanceAgentRuntime:
    def __init__(self):
        self.agents = {
            "revenue_agent": RevenueAgent(),
            "invoice_agent": InvoiceAgent(),
            "leakage_agent": LeakageAgent(),
            "margin_agent": MarginAgent(),
            "statistics_agent": StatisticsAgent(),
            "memo_agent": MemoAgent(),
            "period_agent": PeriodAgent(),
        }

    async def run_agent(self, agent_name, state):
        agent = self.agents.get(agent_name)

        if not agent:
            state.errors.append(f"Agent not found: {agent_name}")
            state.metadata["failed_agents"].append(agent_name)
            return state

        try:
            updated_state = await asyncio.to_thread(agent.run, state)

            updated_state.metadata["completed_agents"].append(agent_name)

            return updated_state

        except Exception as e:
            state.errors.append(f"{agent_name} failed: {str(e)}")
            state.metadata["failed_agents"].append(agent_name)
            return state

    async def run_parallel(self, agent_names, state):
        if not agent_names:
            return state

        tasks = [
            self.run_agent(agent_name, deepcopy(state))
            for agent_name in agent_names
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        for agent_name, result in zip(agent_names, results):
            if isinstance(result, Exception):
                state.errors.append(f"{agent_name} failed: {str(result)}")
                state.metadata["failed_agents"].append(agent_name)
                continue

            state = self.merge_state(state, result)

        return state

    def merge_state(self, base_state, result_state):
        if result_state.revenue_analysis is not None:
            base_state.revenue_analysis = result_state.revenue_analysis

        if result_state.invoice_analysis is not None:
            base_state.invoice_analysis = result_state.invoice_analysis

        if result_state.leakage_analysis is not None:
            base_state.leakage_analysis = result_state.leakage_analysis

        if result_state.margin_analysis is not None:
            base_state.margin_analysis = result_state.margin_analysis

        if result_state.statistics_analysis is not None:
            base_state.statistics_analysis = result_state.statistics_analysis

        if result_state.business_insights is not None:
            base_state.business_insights = result_state.business_insights

        if result_state.final_memo is not None:
            base_state.final_memo = result_state.final_memo

        for error in result_state.errors:
            if error not in base_state.errors:
                base_state.errors.append(error)

        for agent in result_state.metadata.get("completed_agents", []):
            if agent not in base_state.metadata["completed_agents"]:
                base_state.metadata["completed_agents"].append(agent)

        for agent in result_state.metadata.get("failed_agents", []):
            if agent not in base_state.metadata["failed_agents"]:
                base_state.metadata["failed_agents"].append(agent)

        return base_state

    async def run_plan(self, state):
        state.metadata["status"] = "running"

        for step in state.execution_plan:
            mode = step["mode"]
            agents = step["agents"]

            if mode == "parallel":
                state = await self.run_parallel(agents, state)
            else:
                for agent_name in agents:
                    state = await self.run_agent(agent_name, state)

        if state.errors:
            state.metadata["status"] = "completed_with_errors"
        else:
            state.metadata["status"] = "completed"

        return state