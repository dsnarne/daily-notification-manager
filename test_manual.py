#!/usr/bin/env python3
"""
Manual test - trigger reprioritization while monitoring logs
"""

import asyncio
import aiohttp

async def trigger_reprioritization():
    print("🔄 Triggering reprioritization...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:8000/api/v1/notifications/reprioritize') as response:
                result = await response.json()
                print(f"✅ Reprioritization result: {response.status} - {result.get('message', 'No message')}")
                return True
    except Exception as e:
        print(f"❌ Failed to trigger reprioritization: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(trigger_reprioritization())