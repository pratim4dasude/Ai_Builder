from app.agents.state import GrowthAgentState
from app.agents.router import MultiAgentRouter

from app.connectors.product_connector import ProductConnector
from app.connectors.sales_connector import SalesConnector
from app.connectors.campaign_connector import CampaignConnector
from app.connectors.customer_connector import CustomerConnector
from app.connectors.content_calendar_connector import ContentCalendarConnector

from app.services.data_validation_service import GrowthDataValidationService


class GrowthOrchestrator:
    AGENT_DEPENDENCIES = {
        "sales_trend_agent": [],
        "campaign_performance_agent": [],
        "promotion_score_agent": [
            "sales_trend_agent",
            "campaign_performance_agent",
        ],
        "posting_time_agent": [
            "campaign_performance_agent",
        ],
        "segment_agent": [
            "sales_trend_agent",
            "promotion_score_agent",
        ],
        "risk_agent": [
            "promotion_score_agent",
        ],
        "content_agent": [
            "sales_trend_agent",
            "campaign_performance_agent",
            "promotion_score_agent",
            "posting_time_agent",
            "segment_agent",
            "risk_agent",
        ],
        "memo_agent": [
            "sales_trend_agent",
            "campaign_performance_agent",
            "promotion_score_agent",
            "posting_time_agent",
            "segment_agent",
            "risk_agent",
            "content_agent",
        ],
    }

    AGENT_ORDER = [
        "sales_trend_agent",
        "campaign_performance_agent",
        "promotion_score_agent",
        "posting_time_agent",
        "segment_agent",
        "risk_agent",
        "content_agent",
        "memo_agent",
    ]

    def __init__(self):
        self.agent_router = MultiAgentRouter()
        self.validation_service = GrowthDataValidationService()

    def run(self, query: str, session_id: str | None = None) -> GrowthAgentState:
        state = GrowthAgentState(
            user_query=query,
            session_id=session_id,
        )

        validation_result = self._validate_data()

        if not validation_result.get("is_valid"):
            state.selected_agents = []
            state.final_memo = {
                "status": "failed",
                "stage": "data_validation",
                "message": "Growth Marketing Worker stopped because data validation failed.",
                "errors": validation_result.get("errors", []),
                "summary": validation_result.get("summary", {}),
            }
            return state

        state = self.agent_router.supervisor.plan(state)

        state.selected_agents = self._expand_dependencies(state.selected_agents)

        for agent_name in state.selected_agents:
            state = self.agent_router.run_agent(agent_name, state)

        return state

    def _validate_data(self) -> dict:
        products_df = ProductConnector().load_data()
        sales_df = SalesConnector().load_data()
        campaigns_df = CampaignConnector().load_data()
        customers_df = CustomerConnector().load_data()
        content_df = ContentCalendarConnector().load_data()

        return self.validation_service.validate_all(
            products_df=products_df,
            sales_df=sales_df,
            campaigns_df=campaigns_df,
            customers_df=customers_df,
            content_df=content_df,
        )

    def _expand_dependencies(self, selected_agents: list[str]) -> list[str]:
        required_agents = set()

        def add_agent_with_dependencies(agent_name: str):
            dependencies = self.AGENT_DEPENDENCIES.get(agent_name, [])

            for dependency in dependencies:
                add_agent_with_dependencies(dependency)

            required_agents.add(agent_name)

        for agent_name in selected_agents:
            add_agent_with_dependencies(agent_name)

        ordered_agents = [
            agent_name
            for agent_name in self.AGENT_ORDER
            if agent_name in required_agents
        ]

        return ordered_agents