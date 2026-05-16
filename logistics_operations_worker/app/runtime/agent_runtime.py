import time
import uuid
from typing import Dict, Any


class AgentRuntime:
    def __init__(self):
        self.run_id = str(uuid.uuid4())

    def run_agent(self, agent_name: str, agent, state):
        start_time = time.time()

        try:
            state.add_step(
                agent_name,
                "started",
                f"{agent_name} started execution",
            )

            state = agent.run(state)

            execution_time = round(time.time() - start_time, 3)

            state.add_step(
                agent_name,
                "runtime_completed",
                f"{agent_name} completed in {execution_time}s",
            )

            self._add_runtime_log(
                state=state,
                agent_name=agent_name,
                status="success",
                execution_time=execution_time,
                error=None,
            )

            return state

        except Exception as e:
            execution_time = round(time.time() - start_time, 3)

            state.add_step(
                agent_name,
                "failed",
                f"{agent_name} failed: {str(e)}",
            )

            self._add_runtime_log(
                state=state,
                agent_name=agent_name,
                status="failed",
                execution_time=execution_time,
                error=str(e),
            )

            return state

    def _add_runtime_log(
        self,
        state,
        agent_name: str,
        status: str,
        execution_time: float,
        error: str | None,
    ):
        if not hasattr(state, "runtime_logs") or state.runtime_logs is None:
            state.runtime_logs = []

        state.runtime_logs.append({
            "run_id": self.run_id,
            "agent": agent_name,
            "status": status,
            "execution_time_seconds": execution_time,
            "error": error,
        })