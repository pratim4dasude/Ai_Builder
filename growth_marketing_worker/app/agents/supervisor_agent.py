from app.agents.state import GrowthAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: GrowthAgentState) -> GrowthAgentState:
        query = state.user_query.lower()

        selected_agents = []

        if "promote" in query or "promotion" in query or "recommend" in query:
            selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "posting_time_agent",
                "segment_agent",
                "risk_agent",
                "content_agent",
                "memo_agent",
            ]

        elif "sales" in query or "trend" in query or "growing" in query:
            selected_agents = [
                "sales_trend_agent",
                "memo_agent",
            ]

        elif "campaign" in query or "performance" in query or "ctr" in query:
            selected_agents = [
                "campaign_performance_agent",
                "memo_agent",
            ]

        elif "risk" in query or "avoid" in query or "pause" in query or "weak" in query:
            selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "risk_agent",
                "memo_agent",
            ]

        elif "time" in query or "post" in query or "posting" in query:
            selected_agents = [
                "posting_time_agent",
                "memo_agent",
            ]

        elif "segment" in query or "target" in query or "customer" in query or "city" in query:
            selected_agents = [
                "promotion_score_agent",
                "segment_agent",
                "memo_agent",
            ]

        elif "caption" in query or "content" in query or "copy" in query:
            selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "posting_time_agent",
                "segment_agent",
                "risk_agent",
                "content_agent",
                "memo_agent",
            ]

        else:
            selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "posting_time_agent",
                "segment_agent",
                "risk_agent",
                "content_agent",
                "memo_agent",
            ]

        state.selected_agents = selected_agents
        return state