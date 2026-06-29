import sys
import os
import time
import asyncio
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search.engine import SearchEngine
from connectors.sqlite_conn import SQLiteConnector
from connectors.csv_conn import CSVFolderConnector
from connectors.http_conn import HTTPAPIConnector

def ensure_db_exists(db_path):
    if os.path.exists(db_path):
        return
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE Customer (CustomerId INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, Email TEXT, Phone TEXT)")
    cursor.execute("CREATE TABLE Invoice (InvoiceId INTEGER PRIMARY KEY, CustomerId INTEGER, InvoiceDate TEXT, Total REAL)")
    
    customers = [(i, f"First_{i}", f"Last_{i}", f"user{i}@example.com", f"555-{i:04d}") for i in range(1, 2001)]
    cursor.executemany("INSERT INTO Customer VALUES (?, ?, ?, ?, ?)", customers)
    
    invoices = [(i, i, f"2026-01-{ (i % 28) + 1:02d}", 10.0 + i) for i in range(1, 200001)]
    cursor.executemany("INSERT INTO Invoice VALUES (?, ?, ?, ?)", invoices)
    
    conn.commit()
    conn.close()

async def run_evaluation():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, "data_storage", "catalog_data.db")
    csv_path = os.path.join(project_root, "csv_data")
    json_path = os.path.join(project_root, "csv_data", "mock_api.json")

    ensure_db_exists(db_path)

    search_engine = SearchEngine()

    sqlite_conn = SQLiteConnector("sqlite_source", db_path)
    csv_conn = CSVFolderConnector("csv_source", csv_path)
    http_conn = HTTPAPIConnector("http_source", f"file://{json_path}")

    await search_engine.index_source(sqlite_conn)
    await search_engine.index_source(csv_conn)
    await search_engine.index_source(http_conn)

    sources = ["sqlite_source", "csv_source", "http_source"]
    integrity_count = 0
    for s in sources:
        if s in search_engine.catalog:
            integrity_count += 1
    
    schema_integrity = (integrity_count / len(sources)) * 100

    test_queries = [
        {"query": "email", "expected_path": "Customer.Email"},
        {"query": "invoice", "expected_path": "Invoice"},
        {"query": "phone", "expected_path": "Customer.Phone"},
    ]

    total_latency = 0
    success_count = 0

    print("-" * 55)
    print(f"{'Запрос':<30} | {'Recall@3':<10} | {'Latency':<10}")
    print("-" * 55)

    for item in test_queries:
        start_time = time.perf_counter()
        results = search_engine.search(item["query"], limit=3)
        end_time = time.perf_counter()
        
        latency = (end_time - start_time) * 1000
        total_latency += latency
        
        paths = [res.get("path") for res in results]
        is_success = item["expected_path"] in paths
        
        if is_success:
            success_count += 1

        print(f"{item['query']:<30} | {'Да' if is_success else 'Нет':<10} | {latency:.2f}ms")

    recall_at_3 = success_count / len(test_queries)
    avg_latency = total_latency / len(test_queries)

    print("\n" + "-"*55)
    print(f"{'Метрика':<30} | {'Значение':<10} | {'Статус':<10}")
    print("-" * 55)
    print(f"{'Recall@3':<30} | {recall_at_3:.2f}{'':<6} | {'OK' if recall_at_3 > 0.8 else 'FAIL'}")
    print(f"{'Latency (avg)':<30} | {avg_latency:.2f}ms{'':<4} | {'OK' if avg_latency < 200 else 'FAIL'}")
    print(f"{'Schema Integrity':<30} | {schema_integrity:.0f}%{'':<6} | {'OK' if schema_integrity == 100 else 'FAIL'}")
    print("-" * 55)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
