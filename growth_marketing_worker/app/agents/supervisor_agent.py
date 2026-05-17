from app.agents.state import GrowthAgentState


class SupervisorAgent:
    name = "SupervisorAgent"

    def plan(self, state: GrowthAgentState) -> GrowthAgentState:
        query = state.user_query.lower()

        if "avoid" in query or "pause" in query or "risk" in query or "weak" in query:
            state.query_intent = "risk_analysis"
            state.selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "risk_agent",
                "memo_agent",
            ]

        elif "campaign" in query or "performance" in query or "ctr" in query or "roas" in query:
            state.query_intent = "campaign_performance"
            state.selected_agents = [
                "campaign_performance_agent",
                "memo_agent",
            ]

        elif "time" in query or "post" in query or "posting" in query:
            state.query_intent = "posting_time"
            state.selected_agents = [
                "campaign_performance_agent",
                "posting_time_agent",
                "memo_agent",
            ]

        elif "segment" in query or "target" in query or "customer" in query or "city" in query:
            state.query_intent = "segment_recommendation"
            state.selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "segment_agent",
                "memo_agent",
            ]

        elif "caption" in query or "content" in query or "copy" in query:
            state.query_intent = "content_generation"
            state.selected_agents = [
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
            state.query_intent = "sales_trend"
            state.selected_agents = [
                "sales_trend_agent",
                "memo_agent",
            ]

        else:
            state.query_intent = "promotion_recommendation"
            state.selected_agents = [
                "sales_trend_agent",
                "campaign_performance_agent",
                "promotion_score_agent",
                "posting_time_agent",
                "segment_agent",
                "risk_agent",
                "content_agent",
                "memo_agent",
            ]

        return state