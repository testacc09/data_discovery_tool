import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import csv
import json
import sqlite3
import random
import ujson
from datetime import datetime, timedelta
from fastembed import TextEmbedding

def generate_seed_data():
    base_dir = "./data_storage"
    csv_dir = os.path.join(base_dir, "csv_sources")
    api_dir = os.path.join(base_dir, "api_responses")
    db_dir = os.path.join(base_dir, "databases")
    
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(api_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)

    actions = ["login", "logout", "click_banner", "view_product", "add_to_cart", "purchase", "remove_item", "search_query"]
    browsers = ["Chrome", "Firefox", "Safari", "Edge", "Opera"]
    countries = ["RU", "US", "DE", "FR", "GB", "CN", "JP", "KR"]
    os_list = ["Windows", "MacOS", "Linux", "Android", "iOS"]
    
    start_date = datetime(2026, 6, 1)
    
    indexed_elements = {}
    
    csv_columns = [
        "event_id", "user_id", "user_email", "action", "page_url", 
        "ip_address", "user_agent", "browser", "device_os", "country", 
        "session_duration", "timestamp", "is_premium_user", "referrer_source",
        "screen_resolution", "network_type", "utm_medium", "is_conversion"
    ]
    
    for day in range(15):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y_%m_%d")
        file_name = f"user_analytics_{date_str}.csv"
        file_path = os.path.join(csv_dir, file_name)
        
        indexed_elements[f"csv_source:table: {file_name}"] = f"table: {file_name}"
        for col in csv_columns:
            indexed_elements[f"csv_source:column: {file_name}.{col}"] = f"column: {file_name}.{col}"
            
        is_weekend = current_date.weekday() in [5, 6]
        if is_weekend:
            csv_rows = random.randint(1000, 5000)
        else:
            csv_rows = random.choice([random.randint(8000, 15000), random.randint(35000, 55000)])

        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(csv_columns)
            for i in range(csv_rows):
                uid = random.randint(10000, 99999)
                writer.writerow([
                    f"evt_{day}_{i:05d}",
                    f"usr_{uid}",
                    f"student_{uid}@mpei.ru",
                    random.choice(actions),
                    f"/catalog/item_{random.randint(1, 3000)}",
                    f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                    f"Mozilla/5.0 (Platform; {i})",
                    random.choice(browsers),
                    random.choice(os_list),
                    random.choice(countries),
                    random.randint(5, 3600),
                    (current_date + timedelta(seconds=i * 2)).strftime("%Y-%m-%d %H:%M:%S"),
                    random.choice(["True", "False"]),
                    random.choice(["google", "yandex", "direct", "vk", "telegram"]),
                    random.choice(["1920x1080", "1440x900", "375x812", "414x896"]),
                    random.choice(["4G", "5G", "Wi-Fi", "Ethernet"]),
                    random.choice(["cpc", "email", "social", "organic"]),
                    random.choice(["0", "1"])
                ])

    services = ["auth", "payment", "inventory", "delivery", "billing", "support", "crm", "notif"]
    json_columns = [
        "id", "service", "method", "path", "status_code", "latency_ms", 
        "bytes_sent", "bytes_received", "is_internal", "retry_count", 
        "node_id", "request_id", "client_ip", "api_version", "cache_hit"
    ]
    
    for service in services:
        for shard in range(3):
            file_name = f"logs_{service}_shard_{shard}.json"
            file_id = f"http_{file_name.split('.')[0]}"
            
            indexed_elements[f"{file_id}:table: {file_name}"] = f"table: {file_name}"
            for col in json_columns:
                indexed_elements[f"{file_id}:column: {file_name}.{col}"] = f"column: {file_name}.{col}"
            
            if service in ["auth", "payment", "crm"]:
                json_rows = random.randint(12000, 22000)
            elif service in ["support", "notif"]:
                json_rows = random.randint(500, 2500)
            else:
                json_rows = random.randint(4000, 9000)

            api_endpoints = []
            for i in range(json_rows):
                api_endpoints.append({
                    "id": f"{service}_{shard}_{i}",
                    "service": service,
                    "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                    "path": f"/api/v3/{service}/items/{random.randint(100, 999)}/action",
                    "status_code": random.choice([200, 201, 400, 401, 404, 500]),
                    "latency_ms": random.randint(10, 1500),
                    "bytes_sent": random.randint(256, 102400),
                    "bytes_received": random.randint(64, 4096),
                    "is_internal": random.choice([True, False]),
                    "retry_count": random.randint(0, 3),
                    "node_id": f"cluster-node-{random.randint(1, 8)}",
                    "request_id": f"req-{random.getrandbits(32)}",
                    "client_ip": f"10.0.{random.randint(1,254)}.{random.randint(1,254)}",
                    "api_version": "v3.1.2",
                    "cache_hit": random.choice([True, False])
                })
            file_path = os.path.join(api_dir, file_name)
            with open(file_path, mode="w", encoding="utf-8") as f:
                ujson.dump(api_endpoints, f)

    db_names = ["Production_CRM.db", "ECommerce_Sales.db", "HR_Analytics.db"]
    db_columns = [
        "record_id", "email", "first_name", "last_name", "company_name", 
        "address_line", "city_name", "region_code", "country_name", "postal_val", 
        "phone_num", "fax_num", "score_rating", "status_flag", "category_group", 
        "created_at", "updated_at", "internal_code", "is_active", "verified_by_admin"
    ]
    first_names = ["Alexey", "Dmitry", "Ivan", "Sergey", "Andrey", "Mikhail", "Artem", "Nikolay"]
    last_names = ["Petrov", "Ivanov", "Smirnov", "Sidorov", "Vaskovskiy", "Kozhevnikov", "Popov", "Volkov"]
    
    for db_name in db_names:
        file_id = f"sqlite_{db_name.split('.')[0]}"
        conn = sqlite3.connect(os.path.join(db_dir, db_name))
        
        for t_idx in range(5):
            table_name = f"data_registry_table_{t_idx}"
            
            indexed_elements[f"{file_id}:table: {table_name}"] = f"table: {table_name}"
            for col in db_columns:
                indexed_elements[f"{file_id}:column: {table_name}.{col}"] = f"column: {table_name}.{col}"
                
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    record_id INTEGER PRIMARY KEY, email TEXT, first_name TEXT, last_name TEXT,
                    company_name TEXT, address_line TEXT, city_name TEXT, region_code TEXT,
                    country_name TEXT, postal_val TEXT, phone_num TEXT, fax_num TEXT,
                    score_rating REAL, status_flag TEXT, category_group TEXT, 
                    created_at TEXT, updated_at TEXT, internal_code TEXT, 
                    is_active INTEGER, verified_by_admin INTEGER
                );
            """)
            conn.execute(f"DELETE FROM {table_name};")
            
            if db_name == "Production_CRM.db":
                sqlite_rows = random.randint(25000, 40000)
            elif db_name == "HR_Analytics.db":
                sqlite_rows = random.randint(800, 3000)
            else:
                sqlite_rows = random.randint(10000, 18000)

            rows_data = []
            for i in range(1, sqlite_rows + 1):
                rows_data.append((
                    i, f"user_{t_idx}_{i}@mpei.ru", random.choice(first_names), random.choice(last_names),
                    f"Enterprise Corp {i}", f"Building {i} Suite {random.randint(1,100)}", "Moscow", "MO", "Russia",
                    f"111{random.randint(100,999)}", f"+7-999-{i:07d}", f"+7-495-{i:07d}",
                    round(random.uniform(1.0, 100.0), 2), random.choice(["NEW", "ACTIVE", "BANNED", "PENDING"]),
                    random.choice(["A", "B", "C", "D"]), "2026-06-01", "2026-06-27", f"CODE_{random.randint(1000,9999)}",
                    random.choice([1, 0]), random.choice([1, 0])
                ))
            conn.executemany(f"INSERT INTO {table_name} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", rows_data)
            
        conn.commit()
        conn.close()

    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
    cache_keys = list(indexed_elements.keys())
    texts_to_embed = list(indexed_elements.values())
    
    embeddings = list(model.embed(texts_to_embed, batch_size=256, parallel=os.cpu_count()))
    
    cache_to_save = {}
    for key, emb in zip(cache_keys, embeddings):
        cache_to_save[key] = emb.tolist()
        
    cache_file_path = os.path.join(base_dir, "embeddings_cache.json")
    with open(cache_file_path, "w", encoding="utf-8") as cache_file:
        json.dump(cache_to_save, cache_file)

if __name__ == "__main__":
    generate_seed_data()
