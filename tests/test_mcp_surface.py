import pytest
import json
from unittest.mock import MagicMock, AsyncMock

class MockMCPServer:
    def __init__(self, engine, connectors_pool):
        self.engine = engine
        self.connectors_pool = connectors_pool

    async def list_tools(self):
        tool1 = MagicMock()
        tool1.name = "listSources"
        tool1.inputSchema = {"properties": {}}
        
        tool2 = MagicMock()
        tool2.name = "indexSource"
        
        tool3 = MagicMock()
        tool3.name = "search"
        tool3.inputSchema = {"properties": {"query": {"type": "string"}}}
        
        tool4 = MagicMock()
        tool4.name = "getSchema"
        
        return [tool1, tool2, tool3, tool4]

    async def call_tool(self, name, arguments):
        if name == "listSources":
            sources = list(self.connectors_pool.keys())
            mock_content = MagicMock()
            mock_content.text = json.dumps(sources)
            return [mock_content]
            
        elif name == "indexSource":
            mock_content = MagicMock()
            mock_content.text = json.dumps({"status": "success", "sourceId": arguments.get("sourceId")})
            return [mock_content]
            
        elif name == "search":
            results = self.engine.search(arguments.get("query"))
            mock_content = MagicMock()
            mock_content.text = json.dumps(results)
            return [mock_content]
            
        elif name == "getSchema":
            source_id = arguments.get("sourceId")
            schema = self.connectors_pool[source_id].get_schema()
            mock_content = MagicMock()
            mock_content.text = json.dumps(schema)
            return [mock_content]


@pytest.fixture
def mock_engine_and_pool():
    engine = MagicMock()
    engine.search.return_value = [
        {
            "type": "table",
            "score": 0.92,
            "sourceId": "csv_source",
            "path": "users.csv",
            "metadata": {"row_count": 500},
            "preview": [["id", "name"], [1, "Alice"]]
        }
    ]
    
    connectors_pool = {
        "csv_source": MagicMock(),
        "sqlite_main": MagicMock()
    }
    
    connectors_pool["csv_source"].get_schema.return_value = {
        "columns": {"id": "INTEGER", "name": "TEXT"},
        "row_count": 500
    }
    
    return engine, connectors_pool


@pytest.fixture
def mcp_server(mock_engine_and_pool):
    engine, connectors_pool = mock_engine_and_pool
    return MockMCPServer(engine=engine, connectors_pool=connectors_pool)


@pytest.mark.asyncio
async def test_mcp_manifest_structure(mcp_server):
    tools = await mcp_server.list_tools()
    tool_names = [tool.name for tool in tools]
    
    assert "listSources" in tool_names
    assert "indexSource" in tool_names
    assert "search" in tool_names
    assert "getSchema" in tool_names
    
    search_tool = next(t for t in tools if t.name == "search")
    assert search_tool.inputSchema is not None
    assert "properties" in search_tool.inputSchema


@pytest.mark.asyncio
async def test_mcp_list_sources(mcp_server):
    response = await mcp_server.call_tool("listSources", arguments={})
    assert isinstance(response, list)
    
    data = json.loads(response[0].text)
    assert isinstance(data, list)
    assert "csv_source" in data


@pytest.mark.asyncio
async def test_mcp_index_source(mcp_server):
    response = await mcp_server.call_tool("indexSource", arguments={"sourceId": "csv_source"})
    assert isinstance(response, list)
    
    data = json.loads(response[0].text)
    assert data["status"] == "success"
    assert data["sourceId"] == "csv_source"


@pytest.mark.asyncio
async def test_mcp_search_contract(mcp_server):
    arguments = {"query": "customer data", "filters": {"type": "table"}}
    response = await mcp_server.call_tool("search", arguments)
    
    assert isinstance(response, list)
    results = json.loads(response[0].text)
    assert isinstance(results, list)
    assert len(results) > 0
    
    item = results[0]
    assert item["type"] in ["table", "column", "row"]
    assert "score" in item
    assert "sourceId" in item
    assert "path" in item


@pytest.mark.asyncio
async def test_mcp_get_schema_contract(mcp_server):
    arguments = {"sourceId": "csv_source", "path": "users.csv"}
    response = await mcp_server.call_tool("getSchema", arguments)
    
    assert isinstance(response, list)
    schema = json.loads(response[0].text)
    assert "columns" in schema
    assert "row_count" in schema
