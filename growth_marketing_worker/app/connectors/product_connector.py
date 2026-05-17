import pandas as pd

from app.config import PRODUCTS_DATA_PATH
from app.connectors.base_connector import BaseCSVConnector


class ProductConnector(BaseCSVConnector):
    def __init__(self):
        super().__init__(PRODUCTS_DATA_PATH)

    def load_data(self) -> pd.DataFrame:
        df = self._read_csv()

        numeric_cols = [
            "price",
            "cost_price",
            "margin_percent",
            "inventory_count",
            "refund_rate_percent",
            "rating",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")

        return df