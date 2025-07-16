#!/usr/bin/env python3
"""
Simple WebSocket test using curl-like approach
"""
import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_websocket_simple():
    """Simple WebSocket test"""
    uri = "ws://localhost:8001/api/ws/test"
    
    try:
        logger.info(f"Connecting to {uri}")
        
        # Use a shorter timeout and more specific connection
        async with websockets.connect(
            uri,
            timeout=10,
            ping_interval=None,
            ping_timeout=None
        ) as websocket:
            logger.info("WebSocket connected!")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received: {message}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for initial message")
                return False
            
            # Send a message
            test_msg = "Hello WebSocket"
            await websocket.send(test_msg)
            logger.info(f"Sent: {test_msg}")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                logger.info(f"Received response: {response}")
                return True
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for response")
                return False
                
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket_simple())
    if result:
        print("✅ WebSocket test passed!")
    else:
        print("❌ WebSocket test failed!")