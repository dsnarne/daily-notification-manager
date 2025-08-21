#!/usr/bin/env python3
import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.DEBUG)

async def test_session():
    try:
        print("Creating stdio client...")
        params = StdioServerParameters(
            command="python", 
            args=["-m", "mcp_servers.communication_server.server"]
        )
        
        async with stdio_client(params) as (read_stream, write_stream):
            print("Got streams, creating session...")
            session = ClientSession(read_stream, write_stream)
            
            print("Initializing session...")
            init_result = await session.initialize()
            print(f"Initialized: {init_result}")
            
            print("Calling list_tools...")
            tools = await session.list_tools()
            print(f"Tools: {tools}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_session())