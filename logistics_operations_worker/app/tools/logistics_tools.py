from app.tools.base_tool import BaseTool
from app.connectors.connector_manager import ConnectorManager
from app.services.warehouse_assignment import assign_warehouses
from app.services.clustering_service import cluster_assigned_orders
from app.services.route_service import generate_routes_for_clusters
from app.services.risk_service import detect_delivery_risks


class AssignWarehouseTool(BaseTool):
    name = "assign_warehouses"
    description = "Assign pending orders to best warehouse using stock, distance and capacity."

    def run(self, state):
        manager = ConnectorManager()
        data = manager.load_all()

        return assign_warehouses(
            orders=data["orders"],
            warehouses=data["warehouses"],
            inventory=data["inventory"],
            city=state.city or "Bangalore",
            limit=100,
        )


class CreateClustersTool(BaseTool):
    name = "create_clusters"
    description = "Create delivery clusters from warehouse assignments."

    def run(self, state):
        assignments = state.warehouse_plan.get("assignments", [])

        if not assignments:
            return {
                "summary": "No assigned orders available for clustering.",
                "total_clusters": 0,
                "radius_km": 3.0,
                "clusters": [],
                "sample_clusters": [],
            }

        return cluster_assigned_orders(
            assignments=assignments,
            radius_km=3.0,
        )


class GenerateRoutesTool(BaseTool):
    name = "generate_routes"
    description = "Generate optimized routes for delivery clusters."

    def run(self, state):
        return generate_routes_for_clusters(state.clusters)


class AnalyzeRiskTool(BaseTool):
    name = "analyze_risk"
    description = "Analyze COD, SLA, distance and delivery risk."

    def run(self, state):
        manager = ConnectorManager()
        data = manager.load_all()

        return detect_delivery_risks(
            orders=data["orders"],
            shipments=data["shipments"],
            warehouse_plan=state.warehouse_plan,
        )