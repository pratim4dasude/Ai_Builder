from app.agents.state import FinanceAgentState
from app.connectors.connector_manager import ConnectorManager
from app.utils.period_parser import parse_period_from_query


class PeriodAgent:
    name = "PeriodAgent"

    def run(self, state: FinanceAgentState) -> FinanceAgentState:
        connector = ConnectorManager()
        orders = connector.load_csv("orders.csv")

        state.period = parse_period_from_query(
            query=state.user_query,
            orders_df=orders,
        )

        return state