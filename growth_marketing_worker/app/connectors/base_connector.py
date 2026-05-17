from abc import ABC, abstractmethod
import pandas as pd


class BaseCSVConnector(ABC):
    def __init__(self, file_path):
        self.file_path = file_path

    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        pass

    def _read_csv(self) -> pd.DataFrame:
        return pd.read_csv(self.file_path)