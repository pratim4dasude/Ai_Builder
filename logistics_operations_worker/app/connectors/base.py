from abc import ABC, abstractmethod
import pandas as pd


class BaseConnector(ABC):
    def __init__(self, source_name: str, file_path: str):
        self.source_name = source_name
        self.file_path = file_path

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        pass