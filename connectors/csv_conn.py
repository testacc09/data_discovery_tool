import os
import csv
from typing import Dict, Any, List
from .base import BaseConnector

class CSVFolderConnector(BaseConnector):

    def __init__(self, source_id: str, folder_path: str):
        self.source_id = source_id
        self.folder_path = folder_path

    def get_source_id(self) -> str:
        return self.source_id

    def discover_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        if not os.path.exists(self.folder_path):
            return schemas
        for file_name in os.listdir(self.folder_path):
            if file_name.endswith('.csv'):
                table_name = os.path.splitext(file_name)[0]
                file_path = os.path.join(self.folder_path, file_name)
                with open(file_path, mode='r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        header = next(reader)
                    except StopIteration:
                        continue
                    columns = [{"name": col, "type": "TEXT"} for col in header]
                    row_count = sum(1 for _ in reader)
                schemas.append({
                    "table_name": table_name,
                    "row_count": row_count,
                    "columns": columns
                })
        return schemas

    def get_table_preview(self, table_name: str, limit: int = None) -> List[Dict[str, Any]]:
        file_path = os.path.join(self.folder_path, f"{table_name}.csv")
        if not os.path.exists(file_path):
            return []
        preview_rows = []
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                preview_rows.append(dict(row))
        return preview_rows
