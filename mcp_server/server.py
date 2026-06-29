import asyncio
import os
import json
import sys
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from connectors.sqlite_conn import SQLiteConnector
from connectors.csv_conn import CSVFolderConnector
from connectors.http_conn import HTTPAPIConnector
from search.engine import SearchEngine

search_engine = SearchEngine()
base_data_dir = "./data_storage"

csv_conn = CSVFolderConnector("csv_source", os.path.join(base_data_dir, "csv_sources"))

async def init_all_sources():
    await search_engine.index_source(csv_conn)

    db_dir = os.path.join(base_data_dir, "databases")
    if os.path.exists(db_dir):
        for file in os.listdir(db_dir):
            if file.endswith(".db"):
                db_name = file.split(".")[0]
                sqlite_conn = SQLiteConnector(f"sqlite_{db_name}", os.path.join(db_dir, file))
                await search_engine.index_source(sqlite_conn)

    api_dir = os.path.join(base_data_dir, "api_responses")
    if os.path.exists(api_dir):
        for file in os.listdir(api_dir):
            if file.endswith(".json") and file != "embeddings_cache.json":
                api_name = file.split(".")[0]
                abs_json_path = os.path.abspath(os.path.join(api_dir, file))
                http_conn = HTTPAPIConnector(f"http_{api_name}", f"file://{abs_json_path}")
                await search_engine.index_source(http_conn)

server = Server("data-discovery-tool")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="listSources",
            description="List all available connected data sources",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="indexSource",
            description="Re-index a specific data source by its ID",
            inputSchema={
                "type": "object",
                "properties": {"sourceId": {"type": "string"}},
                "required": ["sourceId"]
            }
        ),
        types.Tool(
            name="search",
            description="Search for relevant tables or columns using natural language query",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        ),
        types.Tool(
            name="getSchema",
            description="Get detailed schema for a specific table or view path",
            inputSchema={
                "type": "object",
                "properties": {
                    "sourceId": {"type": "string"},
                    "path": {"type": "string"}
                },
                "required": ["sourceId", "path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if not arguments:
        arguments = {}
    
    try:
        if name == "listSources":
            sources = list(search_engine.catalog.keys())
            return [types.TextContent(type="text", text=json.dumps(sources))]
        
        elif name == "indexSource":
            source_id = arguments.get("sourceId")
            if source_id == "csv_source":
                await search_engine.index_source(csv_conn)
            elif source_id.startswith("sqlite_"):
                db_file = f"{source_id.replace('sqlite_', '')}.db"
                conn = SQLiteConnector(source_id, os.path.join(base_data_dir, "databases", db_file))
                await search_engine.index_source(conn)
            elif source_id.startswith("http_"):
                json_file = f"{source_id.replace('http_', '')}.json"
                abs_path = os.path.abspath(os.path.join(base_data_dir, "api_responses", json_file))
                conn = HTTPAPIConnector(source_id, f"file://{abs_path}")
                await search_engine.index_source(conn)
            return [types.TextContent(type="text", text=json.dumps({"status": "indexed", "sourceId": source_id}))]
        
        elif name == "search":
            query = arguments.get("query", "")
            results = search_engine.search(query)
            return [types.TextContent(type="text", text=json.dumps(results))]
        
        elif name == "getSchema":
            source_id = arguments.get("sourceId")
            path = arguments.get("path")
            schema = search_engine.get_schema(source_id, path)
            return [types.TextContent(type="text", text=json.dumps(schema))]
        
        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    await init_all_sources()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="data-discovery-tool",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
