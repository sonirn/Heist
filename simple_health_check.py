#!/usr/bin/env python3
"""
Simple Backend Health Check
"""

import asyncio
import aiohttp
import json

async def check_health():
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = "https://4735bc1c-ede9-4807-85b3-92815820cddc.preview.emergentagent.com/api/health"
            print(f"Testing: {url}")
            
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    
                    # Check key sections
                    print(f"Version: {data.get('version', 'N/A')}")
                    print(f"Status: {data.get('status', 'N/A')}")
                    print(f"Environment: {data.get('environment', 'N/A')}")
                    
                    # Check production sections
                    cache = data.get('cache', {})
                    queue = data.get('queue', {})
                    storage = data.get('storage', {})
                    
                    print(f"\nCache section keys: {list(cache.keys())}")
                    print(f"Queue section keys: {list(queue.keys())}")
                    print(f"Storage section keys: {list(storage.keys())}")
                    
                    # Check enhanced components
                    enhanced = data.get('enhanced_components', {})
                    print(f"Enhanced components: {list(enhanced.keys())}")
                    
                    return data
                else:
                    print(f"Error: HTTP {response.status}")
                    return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(check_health())