import sqlite3
import pytest
import pandas as pd
from connectors.sqlite_conn import SQLiteConnector
from connectors.http_conn import HTTPAPIConnector


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "temp_test.db"
    db_path = str(db_file)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test_table (id INTEGER, name TEXT);")
    cursor.execute("INSERT INTO test_table VALUES (1, 'item');")
    conn.commit()
    conn.close()
    
    yield db_path


def test_sqlite_discover_and_preview(temp_db):
    connector = SQLiteConnector("test_id", temp_db)
    schemas = connector.discover_schemas()
    assert len(schemas) == 1
    assert schemas[0]["table_name"] == "test_table"
    preview = connector.get_table_preview("test_table", limit=1)
    assert len(preview) == 1
    assert preview[0]["name"] == "item"


def test_sqlite_preview_limit_enforcement(temp_db):
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO test_table VALUES (2, 'item2');")
    cursor.execute("INSERT INTO test_table VALUES (3, 'item3');")
    conn.commit()
    conn.close()

    connector = SQLiteConnector("test_id", temp_db)
    preview = connector.get_table_preview("test_table", limit=2)
    assert len(preview) == 2


def test_sqlite_preview_non_existent_table(temp_db):
    connector = SQLiteConnector("test_id", temp_db)
    preview = connector.get_table_preview("missing_table", limit=10)
    assert preview is None or (isinstance(preview, pd.DataFrame) and preview.empty) or preview == []


def test_sqlite_get_schema_metadata(temp_db):
    connector = SQLiteConnector("test_id", temp_db)
    schemas = connector.discover_schemas() 
    assert len(schemas) > 0
    table_schema = next((s for s in schemas if s["table_name"] == "test_table"), None)
    assert table_schema is not None
    assert "table_name" in table_schema


def test_http_connector_initialization():
    conn = HTTPAPIConnector("http_api", "file:///abs/path/to/file.json")
    assert conn.source_id == "http_api"
