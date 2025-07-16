#!/usr/bin/env python3
"""
Test WebSocket connection to the backend
"""
import asyncio
import websockets
import json
import sys

async def test_websocket():
    """Test WebSocket connection"""
    generation_id = "test_generation_123"
    uri = f"ws://localhost:8001/api/ws/{generation_id}"
    
    print(f"Connecting to WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Receive initial message
            message = await websocket.recv()
            print(f"Received: {message}")
            
            # Send a test message
            test_message = {"type": "test", "message": "Hello from client"}
            await websocket.send(json.dumps(test_message))
            print(f"Sent: {test_message}")
            
            # Receive echo
            echo = await websocket.recv()
            print(f"Received echo: {echo}")
            
            print("✅ WebSocket communication test passed!")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

async def test_simple_websocket():
    """Test simple WebSocket endpoint"""
    uri = "ws://localhost:8001/api/ws/test"
    
    print(f"Connecting to simple WebSocket: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Simple WebSocket connected successfully!")
            
            # Receive initial message
            message = await websocket.recv()
            print(f"Received: {message}")
            
            # Send a test message
            await websocket.send("Hello from test client")
            print("Sent: Hello from test client")
            
            # Receive echo
            echo = await websocket.recv()
            print(f"Received echo: {echo}")
            
            print("✅ Simple WebSocket communication test passed!")
            
    except Exception as e:
        print(f"❌ Simple WebSocket connection failed: {e}")
        return False
    
    return True

async def main():
    """Main test function"""
    print("Testing WebSocket connections...")
    
    # Test simple WebSocket first
    result1 = await test_simple_websocket()
    print()
    
    # Test generation WebSocket
    result2 = await test_websocket()
    
    if result1 and result2:
        print("\n🎉 All WebSocket tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some WebSocket tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())