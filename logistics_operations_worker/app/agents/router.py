from app.agents.state import LogisticsAgentState
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.warehouse_agent import WarehouseAgent
from app.agents.clustering_agent import ClusteringAgent
from app.agents.routing_agent import RoutingAgent
from app.agents.risk_agent import RiskAgent
from app.agents.memo_agent import MemoAgent
from app.runtime.agent_runtime import AgentRuntime
from app.memory.session_memory import session_memory
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.utils.report_writer import save_final_memo_as_markdown
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

    def run(self, query: str, session_id: str | None = None) -> LogisticsAgentState:
        state = LogisticsAgentState(
            user_query=query,
            session_id=session_id,
        )

        state = self.supervisor.plan(state)



        # for agent_name in state.selected_agents:
        #     agent = self.agent_map.get(agent_name)
        #
        #     if agent is None:
        #         state.add_step(
        #             "MultiAgentRouter",
        #             "skipped",
        #             f"Unknown agent skipped: {agent_name}",
        #         )
        #         continue
        #
        #     state = self.runtime.run_agent(
        #         agent_name=agent.name,
        #         agent=agent,
        #         state=state,
        #     )
        for execution_step in state.execution_plan:
            agents = execution_step["agents"]
            parallel = execution_step["parallel"]

            # --------------------------------
            # Parallel execution
            # --------------------------------

            if parallel:
                with ThreadPoolExecutor(
                        max_workers=len(agents)
                ) as executor:

                    futures = {}

                    for agent_name in agents:
                        agent = self.agent_map.get(agent_name)

                        if not agent:
                            state.add_step(
                                "ExecutionGraph",
                                "skipped",
                                f"Unknown agent: {agent_name}",
                            )
                            continue

                        futures[
                            executor.submit(
                                self.runtime.run_agent,
                                agent.name,
                                agent,
                                state,
                            )
                        ] = agent_name

                    for future in as_completed(futures):
                        try:
                            updated_state = future.result()

                            if updated_state.warehouse_plan:
                                state.warehouse_plan = updated_state.warehouse_plan

                            if updated_state.clusters:
                                state.clusters = updated_state.clusters

                            if updated_state.routes:
                                state.routes = updated_state.routes

                            if updated_state.risks:
                                state.risks = updated_state.risks

                            if updated_state.final_memo:
                                state.final_memo = updated_state.final_memo

                            state.steps = updated_state.steps
                            state.runtime_logs = updated_state.runtime_logs

                        except Exception as e:
                            state.add_step(
                                "ExecutionGraph",
                                "failed",
                                str(e),
                            )

            # --------------------------------
            # Sequential execution
            # --------------------------------

            else:
                for agent_name in agents:
                    agent = self.agent_map.get(agent_name)

                    if not agent:
                        state.add_step(
                            "ExecutionGraph",
                            "skipped",
                            f"Unknown agent: {agent_name}",
                        )
                        continue

                    state = self.runtime.run_agent(
                        agent_name=agent.name,
                        agent=agent,
                        state=state,
                    )
        state.memo_file_path = save_final_memo_as_markdown(state)
        warehouse_plan = state.warehouse_plan or {}
        clusters = state.clusters or {}
        routes = state.routes or {}
        risks = state.risks or {}
        memo_file_path = save_final_memo_as_markdown(state)
        session_memory.add_run(
            session_id=state.session_id,
            run_data={
                "query": state.user_query,
                "city": state.city,
                "date": state.date,
                "summary": {
                    "assigned_orders": warehouse_plan.get("assigned_orders", 0),
                    "total_clusters": clusters.get("total_clusters", 0),
                    "total_routes": routes.get("total_clusters_routed", 0),
                    "total_risky_orders": risks.get("total_risky_orders", 0),
                },
                "final_memo": state.final_memo,
                "memo_file_path": memo_file_path,
                "runtime_logs": state.runtime_logs,
            },
        )

        return state