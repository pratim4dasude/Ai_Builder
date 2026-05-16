from app.connectors.csv_connector import CSVConnector


class ConnectorManager:
    def __init__(self):
        self.csv = CSVConnector()

    def load_csv(self, filename: str):
        return self.csv.load(filename)