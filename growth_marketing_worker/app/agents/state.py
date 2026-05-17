from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class GrowthAgentState(BaseModel):
    user_query: str
    session_id: Optional[str] = None

    selected_agents: List[str] = Field(default_factory=list)

    sales_trends: Dict[str, Any] = Field(default_factory=dict)
    campaign_performance: Dict[str, Any] = Field(default_factory=dict)
    promotion_scores: Dict[str, Any] = Field(default_factory=dict)
    posting_time: Dict[str, Any] = Field(default_factory=dict)
    target_segment: Dict[str, Any] = Field(default_factory=dict)
    generated_content: Dict[str, Any] = Field(default_factory=dict)
    final_memo: Dict[str, Any] = Field(default_factory=dict)
    risk_analysis: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Dict[str, Any]] = Field(default_factory=list)