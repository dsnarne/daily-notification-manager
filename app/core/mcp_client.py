import os
import shlex
import asyncio
import json
import logging
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPCommunicationClient:
    """MCP client for the communication server (gmail/slack)."""

    _instance_lock: asyncio.Lock = asyncio.Lock()
    _tool_lock: asyncio.Lock = asyncio.Lock()  # Separate lock for tool calls
    _session: Optional[ClientSession] = None
    _session_context = None

    @staticmethod
    def _get_params() -> StdioServerParameters:
        # Allow overriding server command via env (e.g., "python -m mcp_servers.communication_server.server")
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
        # Use module import to avoid relative import issues
        return StdioServerParameters(command="python", args=["-m", "mcp_servers.communication_server.server"])

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is not None:
            return cls._session
        async with cls._instance_lock:
            if cls._session is None:
                params = cls._get_params()
                cls._session_context = stdio_client(params)
                # stdio_client returns (read_stream, write_stream)
                read_stream, write_stream = await cls._session_context.__aenter__()
                cls._session = ClientSession(read_stream, write_stream)
                await cls._session.initialize()
                logger.info("MCP communication server session initialized")
            return cls._session

    @classmethod
    async def close(cls):
        """Close the MCP session"""
        if cls._session_context is not None:
            await cls._session_context.__aexit__(None, None, None)
            cls._session = None
            cls._session_context = None

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            try:
                session = await cls.get_session()
                result = await session.call_tool(name, arguments)
                try:
                    if getattr(result, "content", None) and hasattr(result.content[0], "text"):
                        return json.loads(result.content[0].text)
                except Exception as e:
                    logger.error(f"Failed to parse MCP tool result for {name}: {e}")
                return result
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                # Reset session on error
                await cls.close()
                raise


class MCPUserContextClient:
    """MCP client for the user context server (Google Calendar)."""

    _instance_lock: asyncio.Lock = asyncio.Lock()
    _tool_lock: asyncio.Lock = asyncio.Lock()  # Separate lock for tool calls
    _session: Optional[ClientSession] = None
    _session_context = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is not None:
            return cls._session
        async with cls._instance_lock:
            if cls._session is None:
                params = StdioServerParameters(
                    command="python",
                    args=["-m", "mcp_servers.user_context_server.server"]
                )
                cls._session_context = stdio_client(params)
                # stdio_client returns (read_stream, write_stream)
                read_stream, write_stream = await cls._session_context.__aenter__()
                cls._session = ClientSession(read_stream, write_stream)
                await cls._session.initialize()
                logger.info("MCP user context server session initialized")
            return cls._session

    @classmethod
    async def close(cls):
        """Close the MCP session"""
        if cls._session_context is not None:
            await cls._session_context.__aexit__(None, None, None)
            cls._session = None
            cls._session_context = None

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            try:
                session = await cls.get_session()
                result = await session.call_tool(name, arguments)
                try:
                    if getattr(result, "content", None) and hasattr(result.content[0], "text"):
                        return json.loads(result.content[0].text)
                except Exception as e:
                    logger.error(f"Failed to parse MCP tool result for {name}: {e}")
                return result
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                # Reset session on error
                await cls.close()
                raise


