import pandas as pd

from app.config import SALES_DATA_PATH
from app.connectors.base_connector import BaseCSVConnector


class SalesConnector(BaseCSVConnector):
    def __init__(self):
        super().__init__(SALES_DATA_PATH)

    def load_data(self) -> pd.DataFrame:
        df = self._read_csv()

        numeric_cols = [
            "quantity",
            "gross_revenue",
            "discount_amount",
            "refund_amount",
            "net_revenue",
            "pincode",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

        return df