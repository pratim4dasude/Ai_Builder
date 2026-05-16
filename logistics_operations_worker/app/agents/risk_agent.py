from app.agents.state import LogisticsAgentState
from app.connectors.connector_manager import ConnectorManager
from app.services.risk_service import detect_delivery_risks


class RiskAgent:
    name = "RiskAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        if not state.warehouse_plan:
            state.risks = {
                "summary": "No warehouse plan found. Run WarehouseAgent first.",
                "total_risky_orders": 0,
                "risk_counts": {},
                "sample_risks": [],
            }

            state.add_step(
                self.name,
                "skipped",
                "Warehouse plan not available, so risk detection was skipped",
            )

            return state

        manager = ConnectorManager()
        data = manager.load_all()

        state.risks = detect_delivery_risks(
            orders=data["orders"],
            shipments=data["shipments"],
            warehouse_plan=state.warehouse_plan,
        )

        state.add_step(
            self.name,
            "completed",
            f"Detected {state.risks.get('total_risky_orders', 0)} risky orders",
        )

        return state