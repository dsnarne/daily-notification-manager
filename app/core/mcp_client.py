import os
import shlex
import asyncio
import json
import logging
import subprocess
import sys
from typing import Any, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_file)

logger = logging.getLogger(__name__)


class MCPCommunicationClient:
    """MCP client for the communication server (gmail/slack) using raw protocol."""

    _tool_lock: asyncio.Lock = asyncio.Lock()

    @staticmethod
    def _get_params():
        # Allow overriding server command via env (e.g., "python -m mcp_servers.communication_server.server")
        override = os.getenv("MCP_COMM_SERVER")
        # Back-compat: accept GMAIL_SERVER_PATH / gmail_server_path pointing directly to a server.py
        if not override:
            direct_path = os.getenv("GMAIL_SERVER_PATH") or os.getenv("gmail_server_path")
            if direct_path:
                return [sys.executable, direct_path]
        if override:
            parts = shlex.split(override)
            return parts
        # Use module import to avoid relative import issues
        return [sys.executable, "-m", "mcp_servers.communication_server.server"]

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            cmd = cls._get_params()
            try:
                # Create process with environment
                env = os.environ.copy()
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                # Initialize
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "daily-client", "version": "1.0"}
                    }
                }
                
                proc.stdin.write((json.dumps(init_request) + "\n").encode())
                await proc.stdin.drain()
                
                # Read initialize response  
                init_response = await proc.stdout.readline()
                if not init_response:
                    stderr_output = await proc.stderr.read()
                    raise RuntimeError(f"Server failed to start: {stderr_output.decode()}")
                
                # Send initialized notification
                initialized_notif = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                
                proc.stdin.write((json.dumps(initialized_notif) + "\n").encode())
                await proc.stdin.drain()
                
                # Call tool
                call_tool_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                }
                
                proc.stdin.write((json.dumps(call_tool_request) + "\n").encode())
                await proc.stdin.drain()
                
                # Read tool response
                tool_response_raw = await proc.stdout.readline()
                tool_response = json.loads(tool_response_raw.decode().strip())
                
                # Close process
                proc.stdin.close()
                await proc.wait()
                
                # Parse result
                if "result" in tool_response and "content" in tool_response["result"]:
                    content = tool_response["result"]["content"]
                    if content and len(content) > 0 and "text" in content[0]:
                        return json.loads(content[0]["text"])
                
                return tool_response
                
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                if 'proc' in locals() and proc.returncode is None:
                    proc.terminate()
                    await proc.wait()
                raise


class MCPUserContextClient:
    """MCP client for the user context server (Google Calendar) using raw protocol."""

    _tool_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def call_tool(cls, name: str, arguments: Dict[str, Any]) -> Any:
        async with cls._tool_lock:  # Serialize all tool calls
            cmd = [sys.executable, "-m", "mcp_servers.user_context_server.server"]
            try:
                # Create process with environment
                env = os.environ.copy()
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                # Initialize
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "daily-client", "version": "1.0"}
                    }
                }
                
                proc.stdin.write((json.dumps(init_request) + "\n").encode())
                await proc.stdin.drain()
                
                # Read initialize response  
                init_response = await proc.stdout.readline()
                if not init_response:
                    stderr_output = await proc.stderr.read()
                    raise RuntimeError(f"Server failed to start: {stderr_output.decode()}")
                
                # Send initialized notification
                initialized_notif = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                
                proc.stdin.write((json.dumps(initialized_notif) + "\n").encode())
                await proc.stdin.drain()
                
                # Call tool
                call_tool_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": name,
                        "arguments": arguments
                    }
                }
                
                proc.stdin.write((json.dumps(call_tool_request) + "\n").encode())
                await proc.stdin.drain()
                
                # Read tool response
                tool_response_raw = await proc.stdout.readline()
                tool_response = json.loads(tool_response_raw.decode().strip())
                
                # Close process
                proc.stdin.close()
                await proc.wait()
                
                # Parse result
                if "result" in tool_response and "content" in tool_response["result"]:
                    content = tool_response["result"]["content"]
                    if content and len(content) > 0 and "text" in content[0]:
                        return json.loads(content[0]["text"])
                
                return tool_response
                
            except Exception as e:
                logger.error(f"MCP call_tool failed for {name}: {e}")
                if 'proc' in locals() and proc.returncode is None:
                    proc.terminate()
                    await proc.wait()
                raise