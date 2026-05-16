from datetime import datetime
import pandas as pd
from app.connectors.base import BaseConnector


class CSVConnector(BaseConnector):
    def fetch_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.file_path)

        df["source"] = self.source_name
        df["source_file"] = self.file_path
        df["source_row_id"] = df.index + 1
        df["ingested_at"] = datetime.utcnow().isoformat()

        return df