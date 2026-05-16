import asyncio

from app.agents.revenue_agent import RevenueAgent
from app.agents.invoice_agent import InvoiceAgent
from app.agents.leakage_agent import LeakageAgent
from app.agents.margin_agent import MarginAgent
from app.agents.memo_agent import MemoAgent


class FinanceAgentRuntime:
    def __init__(self):
        self.agents = {
            "revenue_agent": RevenueAgent(),
            "invoice_agent": InvoiceAgent(),
            "leakage_agent": LeakageAgent(),
            "margin_agent": MarginAgent(),
            "memo_agent": MemoAgent(),
        }

    async def run_agent(self, agent_name, state):
        agent = self.agents[agent_name]
        return await asyncio.to_thread(agent.run, state)

    async def run_parallel(self, agent_names, state):
        tasks = [
            self.run_agent(agent_name, state)
            for agent_name in agent_names
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                state.errors.append(str(result))
            else:
                state = result

        return state

    async def run_plan(self, state):
        for step in state.execution_plan:
            mode = step["mode"]
            agents = step["agents"]

            if mode == "parallel":
                state = await self.run_parallel(agents, state)

            else:
                for agent_name in agents:
                    state = await self.run_agent(agent_name, state)

        return state