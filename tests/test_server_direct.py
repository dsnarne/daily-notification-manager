#!/usr/bin/env python3
import subprocess
import json
import sys

def test_mcp_server():
    try:
        # Start the MCP server process
        print("Starting MCP server process...")
        proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_servers.communication_server.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        print("Sending initialize request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Wait for response
        print("Waiting for server response...")
        try:
            stdout, stderr = proc.communicate(timeout=10)
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            print(f"Return code: {proc.returncode}")
        except subprocess.TimeoutExpired:
            print("Server timed out - terminating...")
            proc.kill()
            stdout, stderr = proc.communicate()
            print(f"STDOUT after kill: {stdout}")
            print(f"STDERR after kill: {stderr}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_server()