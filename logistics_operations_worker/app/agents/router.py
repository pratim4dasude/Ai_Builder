# from logistics_operations_worker.app.agents.state import LogisticsAgentState
# from logistics_operations_worker.app.agents.supervisor_agent import SupervisorAgent
# from logistics_operations_worker.app.agents.warehouse_agent import WarehouseAgent
# from logistics_operations_worker.app.agents.clustering_agent import ClusteringAgent
# from logistics_operations_worker.app.agents.routing_agent import RoutingAgent
# from logistics_operations_worker.app.agents.risk_agent import RiskAgent
# from logistics_operations_worker.app.agents.memo_agent import MemoAgent
#
#
# class MultiAgentRouter:
#     def __init__(self):
#         self.supervisor = SupervisorAgent()
#
#         self.agent_map = {
#             "warehouse_agent": WarehouseAgent(),
#             "clustering_agent": ClusteringAgent(),
#             "routing_agent": RoutingAgent(),
#             "risk_agent": RiskAgent(),
#             "memo_agent": MemoAgent(),
#         }
#
#     def run(self, query: str) -> LogisticsAgentState:
#         state = LogisticsAgentState(user_query=query)
#
#         state = self.supervisor.plan(state)
#
#         for agent_name in state.selected_agents:
#             agent = self.agent_map[agent_name]
#             state = agent.run(state)
#
#         return state

from app.agents.state import LogisticsAgentState
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.warehouse_agent import WarehouseAgent
from app.agents.clustering_agent import ClusteringAgent
from app.agents.routing_agent import RoutingAgent
from app.agents.risk_agent import RiskAgent
from app.agents.memo_agent import MemoAgent
from app.runtime.agent_runtime import AgentRuntime


class MultiAgentRouter:
    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.runtime = AgentRuntime()

        self.agent_map = {
            "warehouse_agent": WarehouseAgent(),
            "clustering_agent": ClusteringAgent(),
            "routing_agent": RoutingAgent(),
            "risk_agent": RiskAgent(),
            "memo_agent": MemoAgent(),
        }

    def run(self, query: str) -> LogisticsAgentState:
        state = LogisticsAgentState(user_query=query)

        state = self.supervisor.plan(state)

        for agent_name in state.selected_agents:
            agent = self.agent_map[agent_name]
            state = self.runtime.run_agent(
                agent_name=agent.name,
                agent=agent,
                state=state,
            )

        return state