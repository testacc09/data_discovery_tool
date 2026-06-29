import os
from connectors.sqlite_conn import SQLiteConnector
from connectors.csv_conn import CSVFolderConnector
from connectors.http_conn import HTTPAPIConnector
from search.engine import SearchEngine

def run_evaluation():
    engine = SearchEngine()
    sqlite_conn = SQLiteConnector("sqlite_source", "Chinook.db")
    csv_conn = CSVFolderConnector("csv_source", "./csv_data")
    abs_json_path = os.path.abspath("./csv_data/mock_api.json")
    http_conn = HTTPAPIConnector("http_source", f"file://{abs_json_path}")
    
    engine.index_source(sqlite_conn)
    engine.index_source(csv_conn)
    engine.index_source(http_conn)

    test_cases = [
        {"query": "customer email", "expected": "Customer.Email"},
        {"query": "track invoices", "expected": "InvoiceLine"},
        {"query": "payment status", "expected": "payment_logs"},
        {"query": "auth service", "expected": "api_records"}
    ]
    reciprocal_ranks = []
    for case in test_cases:
        query = case["query"]
        expected = case["expected"]
        results = engine.search(query, limit=10)
        rank = 0
        for idx, res in enumerate(results):
            path = res["path"]
            if expected in path or expected == path:
                rank = idx + 1
                break
        if rank > 0:
            rr = 1.0 / rank
        else:
            rr = 0.0
        reciprocal_ranks.append(rr)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    print(f"Evaluation Results")
    print(f"-------------------------------------")
    print(f"Total Test Cases: {len(test_cases)}")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.4f}")

if __name__ == "__main__":
    run_evaluation()
