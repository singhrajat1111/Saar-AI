from abc import ABC, abstractmethod
import pandas as pd
from typing import Any, Dict

class BaseDataConnector(ABC):
    """
    Abstract base class for all data connectors.
    Ensures that any new data source (SQL, Snowflake, CSV, Excel)
    can be plugged into the workflow seamlessly.
    """

    @abstractmethod
    def read_data(self, source: str, **kwargs) -> pd.DataFrame:
        """
        Reads data from the given source and returns a pandas DataFrame.
        """
        pass

    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """
        Validates whether the source is accessible and well-formed.
        """
        pass

    @abstractmethod
    def get_metadata(self, source: str, **kwargs) -> Dict[str, Any]:
        """
        Quickly extracts metadata without loading the entire dataset into memory.
        """
        pass
