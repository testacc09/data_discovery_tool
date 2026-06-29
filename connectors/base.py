from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseConnector(ABC):

    @abstractmethod
    def get_source_id(self) -> str:
        pass

    @abstractmethod
    def discover_schemas(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_table_preview(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass
