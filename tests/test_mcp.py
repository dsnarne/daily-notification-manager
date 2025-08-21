#!/usr/bin/env python3
import asyncio
import logging
from app.core.mcp_client import MCPCommunicationClient

logging.basicConfig(level=logging.DEBUG)

async def test_mcp():
    try:
        print("Testing MCP Communication Client...")
        print("1. Getting session...")
        session = await MCPCommunicationClient.get_session()
        print(f"2. Got session: {session}")
        print("3. Calling tool...")
        result = await MCPCommunicationClient.call_tool("list_gmail_notifications", {"max_results": 5})
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await MCPCommunicationClient.close()

if __name__ == "__main__":
    # Add timeout to prevent hanging
    async def main():
        try:
            await asyncio.wait_for(test_mcp(), timeout=30)
        except asyncio.TimeoutError:
            print("Test timed out - MCP server not responding")
    
    asyncio.run(main())