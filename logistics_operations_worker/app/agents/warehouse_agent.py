from app.agents.state import LogisticsAgentState
from app.connectors.connector_manager import ConnectorManager
from app.services.warehouse_assignment import assign_warehouses


class WarehouseAgent:
    name = "WarehouseAgent"

    def run(self, state: LogisticsAgentState) -> LogisticsAgentState:
        manager = ConnectorManager()
        data = manager.load_all()

        city = state.city or "Bangalore"

        result = assign_warehouses(
            orders=data["orders"],
            warehouses=data["warehouses"],
            inventory=data["inventory"],
            city=city,
            limit=100,
        )

        state.warehouse_plan = result

        state.add_step(
            self.name,
            "completed",
            f"Assigned {result['assigned_orders']} out of {result['pending_orders_checked']} pending orders",
        )

        return state