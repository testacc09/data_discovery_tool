import sqlite3
from typing import Dict, Any, List
from .base import BaseConnector

class SQLiteConnector(BaseConnector):

    def __init__(self, source_id: str, db_path: str):
        self.source_id = source_id
        self.db_path = db_path

    def get_source_id(self) -> str:
        return self.source_id

    def discover_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table_tuple in tables:
                table_name = table_tuple[0]
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns_info = cursor.fetchall()
                columns = [{"name": col[1], "type": col[2]} for col in columns_info]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]
                schemas.append({
                    "table_name": table_name,
                    "row_count": row_count,
                    "columns": columns
                })
        return schemas

    def get_table_preview(self, table_name: str, limit: int = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT ?;", (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            except sqlite3.OperationalError:
                return []
