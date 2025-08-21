#!/usr/bin/env python3
import asyncio
import logging
from app.core.mcp_client import MCPCommunicationClient

logging.basicConfig(level=logging.INFO)

async def test_mcp():
    try:
        print("Testing raw MCP Communication Client...")
        result = await MCPCommunicationClient.call_tool("list_gmail_notifications", {"max_results": 3})
        print(f"Success: {type(result)} - {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    async def main():
        try:
            await asyncio.wait_for(test_mcp(), timeout=15)
        except asyncio.TimeoutError:
            print("Test timed out")
    
    asyncio.run(main())