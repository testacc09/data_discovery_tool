import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
    ) 

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            
            print(f"\nAvailable tools: {[t.name for t in tools.tools]}")
            
            queries = ["sales", "employees", "crm"]
            
            for query in queries:
                await asyncio.sleep(3)
                
                result = await session.call_tool("search", arguments={"query": query})
                
                print(f"\nResult for '{query}'")
                if result.content:
                    print(result.content[0].text)
                else:
                    print("Empty response")

if __name__ == "__main__":
    asyncio.run(main())
