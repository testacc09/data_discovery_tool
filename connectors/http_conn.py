import json
import urllib.request
from typing import Dict, Any, List
from .base import BaseConnector

class HTTPAPIConnector(BaseConnector):

    def __init__(self, source_id: str, api_url: str):
        self.source_id = source_id
        self.api_url = api_url

    def _load_json_data(self) -> Any:
        if self.api_url.startswith("file://"):
            file_path = self.api_url.replace("file://", "")
            if file_path.startswith("/") and file_path[2] == ":":
                file_path = file_path[1:]
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            with urllib.request.urlopen(self.api_url) as response:
                return json.loads(response.read().decode())

    def get_source_id(self) -> str:
        return self.source_id

    def discover_schemas(self) -> List[Dict[str, Any]]:
        try:
            data = self._load_json_data()
            if isinstance(data, dict):
                table_name = "api_root"
                sample_item = data
                row_count = 1
            elif isinstance(data, list) and len(data) > 0:
                table_name = "api_records"
                sample_item = data[0]
                row_count = len(data)
            else:
                return []
            columns = []
            if isinstance(sample_item, dict):
                for key, value in sample_item.items():
                    val_type = "TEXT"
                    if isinstance(value, int):
                        val_type = "INTEGER"
                    elif isinstance(value, float):
                        val_type = "REAL"
                    columns.append({"name": key, "type": val_type})
            return [{
                "table_name": table_name,
                "row_count": row_count,
                "columns": columns
            }]
        except Exception:
            return []

    def get_table_preview(self, table_name: str, limit: int = None) -> List[Dict[str, Any]]:
        try:
            data = self._load_json_data()
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data[:limit]
            return []
        except Exception:
            return []
