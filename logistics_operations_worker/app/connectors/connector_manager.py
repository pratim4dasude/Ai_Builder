from pathlib import Path
from app.connectors.csv_connector import CSVConnector


class ConnectorManager:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parents[2]
        self.data_dir = self.root_dir / "data"

    def load_orders(self):
        return CSVConnector(
            source_name="orders_csv",
            file_path=str(self.data_dir / "orders.csv")
        ).fetch_data()

    def load_shipments(self):
        return CSVConnector(
            source_name="shipments_csv",
            file_path=str(self.data_dir / "shipments.csv")
        ).fetch_data()

    def load_warehouses(self):
        return CSVConnector(
            source_name="warehouses_csv",
            file_path=str(self.data_dir / "warehouses.csv")
        ).fetch_data()

    def load_inventory(self):
        return CSVConnector(
            source_name="inventory_csv",
            file_path=str(self.data_dir / "inventory.csv")
        ).fetch_data()

    def load_all(self):
        return {
            "orders": self.load_orders(),
            "shipments": self.load_shipments(),
            "warehouses": self.load_warehouses(),
            "inventory": self.load_inventory(),
        }