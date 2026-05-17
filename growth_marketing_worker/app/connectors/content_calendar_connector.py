import pandas as pd

from app.config import CONTENT_CALENDAR_DATA_PATH
from app.connectors.base_connector import BaseCSVConnector


class ContentCalendarConnector(BaseCSVConnector):
    def __init__(self):
        super().__init__(CONTENT_CALENDAR_DATA_PATH)

    def load_data(self) -> pd.DataFrame:
        df = self._read_csv()

        df["campaign_id"] = df["campaign_id"].astype(str).replace(
            {
                "": "NA",
                "nan": "NA",
                "None": "NA",
                "null": "NA",
            }
        )

        numeric_cols = [
            "engagements",
            "likes",
            "comments",
            "shares",
            "saves",
            "clicks",
            "conversions",
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["scheduled_datetime"] = pd.to_datetime(df["scheduled_datetime"], errors="coerce")
        df["published_datetime"] = pd.to_datetime(df["published_datetime"], errors="coerce")

        return df