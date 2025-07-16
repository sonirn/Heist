#!/usr/bin/env python3
"""
Test WebSocket implementation
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_with_proper_close():
    """Test WebSocket with proper close handling"""
    uri = "ws://localhost:8001/api/ws/test"
    
    try:
        logger.info(f"Connecting to {uri}")
        
        async with websockets.connect(
            uri,
            timeout=5,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as websocket:
            logger.info("WebSocket connected successfully!")
            
            # Receive initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3)
                logger.info(f"Received: {message}")
                
                # Send a test message
                test_msg = "Hello WebSocket"
                await websocket.send(test_msg)
                logger.info(f"Sent: {test_msg}")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                logger.info(f"Received response: {response}")
                
                # Properly close the connection
                await websocket.close()
                logger.info("WebSocket closed properly")
                
                return True
                
            except asyncio.TimeoutError:
                logger.error("Timeout during communication")
                return False
                
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_with_proper_close())
    if result:
        print("✅ WebSocket test passed!")
    else:
        print("❌ WebSocket test failed!")