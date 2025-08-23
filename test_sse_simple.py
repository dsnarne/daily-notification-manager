#!/usr/bin/env python3
"""
Simple test to verify SSE events are emitted during reprioritization
"""

import asyncio
import aiohttp
import json
import time

async def test_sse_reprioritization():
    print("🧪 Testing SSE reprioritization events...")
    
    events_received = []
    
    async def listen_to_sse():
        """Listen to SSE stream and collect events"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                print("📡 Connecting to SSE stream...")
                async with session.get('http://localhost:8000/api/v1/notifications/stream') as response:
                    print(f"✅ SSE connected: {response.status}")
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            try:
                                event_data = json.loads(line_str[6:])
                                events_received.append(event_data)
                                
                                source = event_data.get('source', 'unknown')
                                event_type = event_data.get('type', 'unknown')
                                
                                print(f"📨 Received SSE event: source={source}, type={event_type}")
                                
                                if source == 'reprioritization' and event_type == 'notification_update':
                                    print(f"✅ Reprioritization event detected!")
                                    notif = event_data.get('notification', {})
                                    print(f"   Notification ID: {notif.get('id')}")
                                    print(f"   Subject: {notif.get('subject')}")
                                    print(f"   Priority: {notif.get('priority')}")
                                    return True
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ Failed to parse SSE data: {e}")
                                continue
                                
        except Exception as e:
            print(f"❌ SSE connection error: {e}")
            return False
    
    # Start listening in background
    listen_task = asyncio.create_task(listen_to_sse())
    
    # Wait a moment for connection to establish
    await asyncio.sleep(3)
    
    print("🔄 Triggering reprioritization...")
    
    # Trigger reprioritization
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/api/v1/notifications/reprioritize') as response:
                result = await response.json()
                print(f"📤 Reprioritization result: {response.status} - {result.get('message', 'No message')}")
    except Exception as e:
        print(f"❌ Failed to trigger reprioritization: {e}")
    
    # Wait for SSE events
    print("⏳ Waiting for reprioritization events...")
    try:
        success = await asyncio.wait_for(listen_task, timeout=15.0)
        if success:
            print("✅ SUCCESS: Reprioritization events are being emitted via SSE!")
            return True
        else:
            print("❌ FAILED: No reprioritization events detected")
            return False
    except asyncio.TimeoutError:
        print("⏰ TIMEOUT: No reprioritization events received within 15 seconds")
        listen_task.cancel()
        return False
    
    print(f"📊 Total events received: {len(events_received)}")
    return False

if __name__ == "__main__":
    asyncio.run(test_sse_reprioritization())