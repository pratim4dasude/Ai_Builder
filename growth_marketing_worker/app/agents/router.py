from app.agents.supervisor_agent import SupervisorAgent
from app.agents.state import GrowthAgentState

from app.connectors.product_connector import ProductConnector
from app.connectors.sales_connector import SalesConnector
from app.connectors.campaign_connector import CampaignConnector
from app.connectors.customer_connector import CustomerConnector
from app.connectors.content_calendar_connector import ContentCalendarConnector

from app.services.sales_analytics_service import SalesAnalyticsService
from app.services.campaign_analytics_service import CampaignAnalyticsService
from app.services.promotion_scoring_service import PromotionScoringService
from app.services.posting_time_service import PostingTimeService
from app.services.segment_service import SegmentService
from app.services.content_generation_service import ContentGenerationService
from app.services.memo_service import MemoService
from app.services.confidence_service import ConfidenceService
from app.services.action_plan_service import ActionPlanService


class MultiAgentRouter:
    def __init__(self):
        self.supervisor = SupervisorAgent()

        self.products_df = ProductConnector().load_data()
        self.sales_df = SalesConnector().load_data()
        self.campaigns_df = CampaignConnector().load_data()
        self.customers_df = CustomerConnector().load_data()
        self.content_df = ContentCalendarConnector().load_data()

        self.sales_service = SalesAnalyticsService()
        self.campaign_service = CampaignAnalyticsService()
        self.scoring_service = PromotionScoringService()
        self.posting_time_service = PostingTimeService()
        self.segment_service = SegmentService()
        self.content_service = ContentGenerationService()
        self.memo_service = MemoService()
        self.confidence_service = ConfidenceService()
        self.action_plan_service = ActionPlanService()

    def run_agent(self, agent_name: str, state: GrowthAgentState) -> GrowthAgentState:
        if agent_name == "sales_trend_agent":
            state.sales_trends = self.sales_service.analyze_sales_trends(
                sales_df=self.sales_df,
                products_df=self.products_df,
            )
            state.citations.extend(state.sales_trends.get("citations", []))

        elif agent_name == "campaign_performance_agent":
            state.campaign_performance = self.campaign_service.analyze_campaign_performance(
                campaigns_df=self.campaigns_df,
                products_df=self.products_df,
            )
            state.citations.extend(state.campaign_performance.get("citations", []))

        elif agent_name == "promotion_score_agent":
            state.promotion_scores = self.scoring_service.calculate_promotion_scores(
                products_df=self.products_df,
                sales_trends=state.sales_trends,
                campaign_performance=state.campaign_performance,
            )

        elif agent_name == "posting_time_agent":
            state.posting_time = self.posting_time_service.find_best_posting_time(
                campaigns_df=self.campaigns_df,
                content_df=self.content_df,
            )

        elif agent_name == "segment_agent":
            recommended_product = state.promotion_scores.get("recommended_product", {})

            state.target_segment = self.segment_service.recommend_target_segment(
                sales_df=self.sales_df,
                customers_df=self.customers_df,
                products_df=self.products_df,
                recommended_product=recommended_product,
            )

        elif agent_name == "risk_agent":
            avoid_products = state.promotion_scores.get("avoid_products", [])

            state.risk_analysis = {
                "status": "success",
                "risky_products": avoid_products[:10],
                "risk_rules": [
                    "Low or negative sales growth",
                    "High refund rate",
                    "Low margin",
                    "Low inventory",
                    "Inactive product",
                    "Weak campaign engagement",
                ],
                "recommendation": "Avoid or pause products with high risk score before running promotion campaigns.",
            }

        elif agent_name == "content_agent":
            recommended_product = state.promotion_scores.get("recommended_product", {})

            state.generated_content = self.content_service.generate_content(
                recommended_product=recommended_product,
                target_segment=state.target_segment,
                posting_time=state.posting_time,
                campaign_performance=state.campaign_performance,
            )

        elif agent_name == "memo_agent":
            state.final_memo = self.memo_service.create_growth_action_memo(
                query=state.user_query,
                sales_trends=state.sales_trends,
                campaign_performance=state.campaign_performance,
                promotion_scores=state.promotion_scores,
                posting_time=state.posting_time,
                target_segment=state.target_segment,
                generated_content=state.generated_content,
                citations=state.citations,
            )

            state.confidence = self.confidence_service.calculate_confidence(
                sales_trends=state.sales_trends,
                campaign_performance=state.campaign_performance,
                promotion_scores=state.promotion_scores,
                posting_time=state.posting_time,
                target_segment=state.target_segment,
                risk_analysis=state.risk_analysis,
            )

            state.next_best_actions = self.action_plan_service.generate_next_best_actions(
                query_intent=state.query_intent,
                promotion_scores=state.promotion_scores,
                posting_time=state.posting_time,
                target_segment=state.target_segment,
                risk_analysis=state.risk_analysis,
                generated_content=state.generated_content,
                confidence=state.confidence,
            )

        return state