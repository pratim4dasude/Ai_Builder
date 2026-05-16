import pandas as pd

from app.config import DATA_DIR
from app.connectors.base import BaseConnector


class CSVConnector(BaseConnector):
    def load(self, source: str) -> pd.DataFrame:
        file_path = DATA_DIR / source

        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            df = pd.read_csv(file_path)
        except Exception:
            df = pd.read_csv(file_path, sep=None, engine="python")

        df.columns = [col.strip() for col in df.columns]

        return df