import pandas as pd

from app.config import CUSTOMERS_DATA_PATH
from app.connectors.base_connector import BaseCSVConnector


class CustomerConnector(BaseCSVConnector):
    def __init__(self):
        super().__init__(CUSTOMERS_DATA_PATH)

    def load_data(self) -> pd.DataFrame:
        df = self._read_csv()

        numeric_cols = [
            "pincode",
            "total_orders",
            "lifetime_value",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
        df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"], errors="coerce")

        return df