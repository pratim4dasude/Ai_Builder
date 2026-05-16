from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from datetime import date
class AgentStep(BaseModel):
    agent: str
    status: str
    message: str


class LogisticsAgentState(BaseModel):
    user_query: str
    city: Optional[str] = "Bangalore"
    date: Optional[str] = str(date.today())

    selected_agents: List[str] = Field(default_factory=list)
    steps: List[AgentStep] = Field(default_factory=list)
    runtime_logs: List[Dict[str, Any]] = Field(default_factory=list)
    warehouse_plan: Optional[Dict[str, Any]] = None
    clusters: Optional[Dict[str, Any]] = None
    routes: Optional[Dict[str, Any]] = None
    risks: Optional[Dict[str, Any]] = None
    final_memo: Optional[str] = None

    citations: List[Dict[str, Any]] = Field(default_factory=list)

    def add_step(self, agent: str, status: str, message: str):
        self.steps.append(
            AgentStep(agent=agent, status=status, message=message)
        )