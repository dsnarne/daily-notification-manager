#!/usr/bin/env python3
"""
Test script for the reprioritization SSE functionality
"""

import asyncio
import aiohttp
import json

async def test_reprioritization_stream():
    """Test that reprioritization events are properly emitted via SSE"""
    
    print("🧪 Testing reprioritization SSE functionality...")
    
    # Start listening to SSE stream
    async with aiohttp.ClientSession() as session:
        print("📡 Connecting to SSE stream...")
        
        # Start SSE connection
        async with session.get('http://localhost:8000/api/v1/mcp/stream') as sse_response:
            print(f"✅ SSE connected: {sse_response.status}")
            
            # Start listening to events in background
            async def listen_sse():
                received_events = []
                async for line in sse_response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])  # Remove 'data: ' prefix
                            received_events.append(data)
                            print(f"📨 SSE Event received: {data.get('source')} - {data.get('type')}")
                            
                            if data.get('source') == 'reprioritization' and data.get('type') == 'notification_update':
                                print(f"✅ Reprioritization event detected!")
                                print(f"   Notification: {data.get('notification', {}).get('subject')}")
                                print(f"   New Priority: {data.get('notification', {}).get('priority')}")
                                return True
                        except json.JSONDecodeError:
                            continue
                return False
            
            # Start listening
            listen_task = asyncio.create_task(listen_sse())
            
            # Wait a moment for SSE to establish
            await asyncio.sleep(2)
            
            # Trigger reprioritization in a separate session
            print("🔄 Triggering reprioritization...")
            async with aiohttp.ClientSession() as test_session:
                try:
                    async with test_session.post('http://localhost:8000/api/v1/notifications/reprioritize') as response:
                        result = await response.json()
                        print(f"📤 Reprioritization response: {response.status} - {result.get('message')}")
                except Exception as e:
                    print(f"❌ Error triggering reprioritization: {e}")
            
            # Wait for SSE events
            print("⏳ Waiting for reprioritization events...")
            try:
                success = await asyncio.wait_for(listen_task, timeout=10.0)
                if success:
                    print("✅ Test PASSED: Reprioritization events are being emitted via SSE!")
                else:
                    print("❌ Test FAILED: No reprioritization events detected")
            except asyncio.TimeoutError:
                print("⏰ Test timeout: No reprioritization events received within 10 seconds")
                listen_task.cancel()

if __name__ == "__main__":
    print("Starting reprioritization SSE test...")
    asyncio.run(test_reprioritization_stream())