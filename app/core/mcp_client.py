import os
import shlex
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPCommunicationClient:
    """Singleton-style MCP client for the communication server (gmail/slack)."""

    _instance_lock: asyncio.Lock = asyncio.Lock()
    _session: Optional[ClientSession] = None
    _cm: Optional[Any] = None  # context manager returned by stdio_client

    @staticmethod
    def _get_params() -> StdioServerParameters:
        # Allow overriding server command via env (e.g., "python /path/to/server.py")
        override = os.getenv("MCP_COMM_SERVER")
        # Back-compat: accept GMAIL_SERVER_PATH / gmail_server_path pointing directly to a server.py
        if not override:
            direct_path = os.getenv("GMAIL_SERVER_PATH") or os.getenv("gmail_server_path")
            if direct_path:
                return StdioServerParameters(command="python", args=[direct_path])
        if override:
            parts = shlex.split(override)
            cmd = parts[0]
            args = parts[1:]
            return StdioServerParameters(command=cmd, args=args)
        return StdioServerParameters(command="python", args=["mcp_servers/communication_server/server.py"])

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is not None:
            return cls._session
        async with cls._instance_lock:
            if cls._session is None:
                params = cls._get_params()
                cls._cm = stdio_client(params)
                # Manually enter async context to keep session open for app lifetime
                read_stream, write_stream, session = await cls._cm.__aenter__()
                cls._session = session
                logger.info("MCP communication server session initialized")
            return cls._session

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        session = await cls.get_session()
        result = await session.call_tool(name, arguments)
        try:
            if getattr(result, "content", None) and hasattr(result.content[0], "text"):
                return json.loads(result.content[0].text)
        except Exception as e:
            logger.error(f"Failed to parse MCP tool result for {name}: {e}")
        return result


