import os
import shlex
import asyncio
import json
import logging
from typing import Any, Dict

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPCommunicationClient:
    """MCP client for the communication server (gmail/slack)."""

    _tool_lock: asyncio.Lock = asyncio.Lock()

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
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            params = cls._get_params()
            try:
                async with stdio_client(params) as (read_stream, write_stream):
                    session = ClientSession(read_stream, write_stream)
                    await session.initialize()
                    # Send initialized notification (required by MCP protocol)
                    # Note: The ClientSession should handle this automatically
                    result = await session.call_tool(name, arguments)
                    try:
                        if getattr(result, "content", None) and hasattr(result.content[0], "text"):
                            return json.loads(result.content[0].text)
                    except Exception as e:
                        logger.error(f"Failed to parse MCP tool result for {name}: {e}")
                    return result
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                raise


class MCPUserContextClient:
    """MCP client for the user context server (Google Calendar)."""

    _tool_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            params = StdioServerParameters(
                command="python",
                args=["-m", "mcp_servers.user_context_server.server"]
            )
            try:
                async with stdio_client(params) as (read_stream, write_stream):
                    session = ClientSession(read_stream, write_stream)
                    await session.initialize()
                    # Send initialized notification (required by MCP protocol)
                    # Note: The ClientSession should handle this automatically
                    result = await session.call_tool(name, arguments)
                    try:
                        if getattr(result, "content", None) and hasattr(result.content[0], "text"):
                            return json.loads(result.content[0].text)
                    except Exception as e:
                        logger.error(f"Failed to parse MCP tool result for {name}: {e}")
                    return result
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                raise