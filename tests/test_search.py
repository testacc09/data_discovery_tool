import os
import json
import sqlite3
import pytest
import pandas as pd
from search.engine import SearchEngine
from connectors.sqlite_conn import SQLiteConnector
from connectors.csv_conn import CSVFolderConnector
from connectors.http_conn import HTTPAPIConnector


@pytest.fixture
def test_env(tmp_path):
    csv_dir = tmp_path / "csv_sources"
    csv_dir.mkdir()
    df = pd.DataFrame({"user_id": [1, 2], "email": ["alice@test.com", "bob@test.com"]})
    df.to_csv(csv_dir / "users.csv", index=False)

    api_dir = tmp_path / "api_responses"
    api_dir.mkdir()
    api_data = {
        "endpoint": "/v1/products",
        "data": [
            {"product_id": 101, "title": "Wireless Mouse", "price": 29.99},
            {"product_id": 102, "title": "Mechanical Keyboard", "price": 89.99}
        ]
    }
    with open(api_dir / "products.json", "w") as f:
        json.dump(api_data, f)

    db_path = tmp_path / "databases"
    db_path.mkdir()
    db_file = db_path / "production.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE orders (order_id INTEGER, customer_name TEXT, total REAL);")
    cursor.execute("INSERT INTO orders VALUES (5001, 'Alice Smith', 150.5);")
    conn.commit()
    conn.close()

    return {
        "csv": CSVFolderConnector("csv_source", str(csv_dir)),
        "http": HTTPAPIConnector("http_products", f"file://{os.path.abspath(api_dir / 'products.json')}"),
        "sqlite": SQLiteConnector("sqlite_main", str(db_file))
    }


@pytest.mark.asyncio
async def test_search_across_all_sources(test_env):
    engine = SearchEngine()

    await engine.index_source(test_env["csv"])
    await engine.index_source(test_env["http"])
    await engine.index_source(test_env["sqlite"])

    results_csv = engine.search("email", limit=10)
    assert len(results_csv) > 0
    assert any(res["sourceId"] == "csv_source" for res in results_csv)

    results_api = engine.search("Wireless Mouse", limit=10)
    assert len(results_api) > 0
    assert any(res["sourceId"] == "http_products" for res in results_api)

    results_db = engine.search("orders", limit=10)
    assert len(results_db) > 0
    assert any(res["sourceId"] == "sqlite_main" for res in results_db)


@pytest.mark.asyncio
async def test_search_relevance_scoring(test_env):
    engine = SearchEngine()
    await engine.index_source(test_env["sqlite"])

    results = engine.search("orders", limit=5)
    assert len(results) > 0
    
    first_res = results[0]
    assert "score" in first_res
    assert "semantic_score" in first_res
    assert "keyword_score" in first_res
    assert first_res["score"] >= 0.0


@pytest.mark.asyncio
async def test_search_no_results(test_env):
    engine = SearchEngine()
    await engine.index_source(test_env["csv"])

    results = engine.search("non_existent_garbage_keyword_12345", limit=10)
    assert isinstance(results, list)
