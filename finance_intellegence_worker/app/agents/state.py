from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FinanceAgentState:
    user_query: str
    session_id: str

    selected_agents: List[str] = field(default_factory=list)
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)

    period: Optional[Dict[str, Any]] = None
    revenue_analysis: Optional[Dict[str, Any]] = None
    invoice_analysis: Optional[Dict[str, Any]] = None
    leakage_analysis: Optional[Dict[str, Any]] = None
    margin_analysis: Optional[Dict[str, Any]] = None
    statistics_analysis: Optional[Dict[str, Any]] = None
    business_insights: Optional[Dict[str, Any]] = None
    final_memo: Optional[str] = None

    errors: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "workflow_type": "finance_agent_orchestrator",
        "status": "initialized",
        "completed_agents": [],
        "failed_agents": [],
    })