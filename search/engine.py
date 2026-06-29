import asyncio
import os
import json
import numpy as np
from typing import List, Dict, Any
from fastembed import TextEmbedding

class SearchEngine:
    def __init__(self):
        self.catalog: Dict[str, List[Dict[str, Any]]] = {}
        
        self.model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            threads=1
        )
        self.embeddings_cache: Dict[str, Any] = {}
        
        cache_path = "./data_storage/embeddings_cache.json"
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                self.embeddings_cache = json.load(f)

    async def index_source(self, connector) -> None:
        source_id = connector.get_source_id()
        schemas = await asyncio.to_thread(connector.discover_schemas)
        self.catalog[source_id] = schemas
        
        texts_to_embed = []
        for schema in schemas:
            table_name = schema["table_name"]
            text_t = f"table: {table_name}"
            if f"{source_id}:{text_t}" not in self.embeddings_cache:
                texts_to_embed.append(text_t)
            for col in schema["columns"]:
                text_c = f"column: {table_name}.{col['name']}"
                if f"{source_id}:{text_c}" not in self.embeddings_cache:
                    texts_to_embed.append(text_c)
                    
        if texts_to_embed:
            embeddings = await asyncio.to_thread(
                lambda: list(self.model.embed(texts_to_embed))
            )
            for text, emb in zip(texts_to_embed, embeddings):
                self.embeddings_cache[f"{source_id}:{text}"] = emb.tolist()
                
            cache_path = "./data_storage/embeddings_cache.json"
            await asyncio.to_thread(self._save_cache, cache_path)

    def _save_cache(self, cache_path: str) -> None:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(self.embeddings_cache, f, ensure_ascii=False, indent=2)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        results = []
        if not query:
            return results
            
        query_emb = list(self.model.embed([query]))[0]
        query_lower = query.lower()
        
        for source_id, schemas in self.catalog.items():
            for schema in schemas:
                table_name = schema["table_name"]
                keyword_score = 0.0
                if query_lower in table_name.lower():
                    keyword_score += 2.5
                    
                table_text = f"table: {table_name}"
                cache_key = f"{source_id}:{table_text}"
                semantic_score = 0.0
                
                if cache_key in self.embeddings_cache:
                    table_emb = np.array(self.embeddings_cache[cache_key])
                    norm_prod = np.linalg.norm(query_emb) * np.linalg.norm(table_emb)
                    if norm_prod > 0:
                        semantic_score = float(np.dot(query_emb, table_emb) / norm_prod)
                        
                total_score = keyword_score + semantic_score
                results.append({
                    "type": "table",
                    "score": total_score,
                    "semantic_score": semantic_score,
                    "keyword_score": keyword_score,
                    "sourceId": source_id,
                    "path": table_name,
                    "metadata": {
                        "row_count": schema["row_count"],
                        "column_count": len(schema["columns"])
                    }
                })
                
                for col in schema["columns"]:
                    col_name = col["name"]
                    col_keyword_score = 0.0
                    if query_lower in col_name.lower():
                        col_keyword_score += 1.5
                        
                    col_text = f"column: {table_name}.{col_name}"
                    col_cache_key = f"{source_id}:{col_text}"
                    col_semantic_score = 0.0
                    
                    if col_cache_key in self.embeddings_cache:
                        col_emb = np.array(self.embeddings_cache[col_cache_key])
                        col_norm_prod = np.linalg.norm(query_emb) * np.linalg.norm(col_emb)
                        if col_norm_prod > 0:
                            col_semantic_score = float(np.dot(query_emb, col_emb) / col_norm_prod)
                            
                    col_total_score = col_keyword_score + col_semantic_score
                    results.append({
                        "type": "column",
                        "score": col_total_score,
                        "semantic_score": col_semantic_score,
                        "keyword_score": col_keyword_score,
                        "sourceId": source_id,
                        "path": f"{table_name}.{col_name}",
                        "metadata": {
                            "data_type": col["type"]
                        }
                    })
                    
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_schema(self, source_id: str, path: str) -> Dict[str, Any]:
        if source_id not in self.catalog:
            return {}
        table_name = path.split(".")[0]
        for schema in self.catalog[source_id]:
            if schema["table_name"] == table_name:
                return schema
        return {}
