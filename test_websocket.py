#!/usr/bin/env python3
"""
Test WebSocket connection to backend
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection"""
    try:
        uri = "ws://localhost:8001/api/ws/test"
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            
            # Receive initial message
            try:
                initial_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Initial message: {initial_msg}")
            except asyncio.TimeoutError:
                print("⚠️  No initial message received")
            
            # Send a test message
            await websocket.send("Hello WebSocket")
            print("✅ Test message sent")
            
            # Try to receive a message (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✅ Response received: {response}")
            except asyncio.TimeoutError:
                print("⚠️  No response received (timeout)")
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)