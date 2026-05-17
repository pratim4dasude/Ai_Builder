import pandas as pd

from app.config import CAMPAIGNS_DATA_PATH
from app.connectors.base_connector import BaseCSVConnector


class CampaignConnector(BaseCSVConnector):
    def __init__(self):
        super().__init__(CAMPAIGNS_DATA_PATH)

    def load_data(self) -> pd.DataFrame:
        df = self._read_csv()

        numeric_cols = [
            "impressions",
            "clicks",
            "spend",
            "conversions",
            "attributed_revenue",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["campaign_date"] = pd.to_datetime(df["campaign_date"], errors="coerce")
        df["post_time"] = df["post_time"].astype(str)

        return df