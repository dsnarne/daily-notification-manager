import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPCommunicationClient:
    """Singleton-style MCP client for the communication server (gmail/slack)."""

    _instance_lock: asyncio.Lock = asyncio.Lock()
    _session: Optional[ClientSession] = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is not None:
            return cls._session
        async with cls._instance_lock:
            if cls._session is None:
                params = StdioServerParameters(
                    command="python",
                    args=["mcp_servers/communication_server/server.py"],
                )
                cls._session = await stdio_client(params)
                logger.info("MCP communication server session initialized")
            return cls._session

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        session = await cls.get_session()
        result = await session.call_tool(name, arguments)
        # Expecting text content with JSON payload as produced by our server
        try:
            if result.content and hasattr(result.content[0], "text"):
                return json.loads(result.content[0].text)
        except Exception as e:
            logger.error(f"Failed to parse MCP tool result for {name}: {e}")
        return result


