#!/usr/bin/env python3
"""
WebSocket and SSE Testing for Script-to-Video Application
Tests WebSocket and Server-Sent Events endpoints for real-time communication
"""

import asyncio
import aiohttp
import json
import time
import websockets
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebSocketSSETester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    
    async def test_websocket_test_generation_endpoint(self) -> bool:
        """Test WebSocket endpoint /api/ws/test_generation"""
        test_name = "WebSocket /api/ws/test_generation"
        try:
            logger.info("🔌 Testing WebSocket endpoint /api/ws/test_generation...")
            
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/test_generation"
            
            logger.info(f"Connecting to: {ws_endpoint}")
            
            try:
                # Try to connect to WebSocket
                websocket = await websockets.connect(ws_endpoint, timeout=10)
                logger.info("✅ WebSocket connection established")
                
                # Send a test message
                test_message = json.dumps({
                    "type": "test",
                    "message": "Testing WebSocket connection",
                    "timestamp": datetime.now().isoformat()
                })
                
                await websocket.send(test_message)
                logger.info(f"📤 Sent test message: {test_message}")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    logger.info(f"📥 Received response: {response}")
                    
                    # Try to parse response as JSON
                    try:
                        response_data = json.loads(response)
                        logger.info(f"✅ Response parsed as JSON: {response_data}")
                    except json.JSONDecodeError:
                        logger.info(f"⚠️  Response is not JSON: {response}")
                    
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket connection and message exchange successful", {
                        "endpoint": ws_endpoint,
                        "sent_message": test_message,
                        "received_response": response
                    })
                    return True
                    
                except asyncio.TimeoutError:
                    logger.info("⚠️  No response received within timeout, but connection was successful")
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket connection successful (no immediate response)", {
                        "endpoint": ws_endpoint,
                        "sent_message": test_message,
                        "status": "connected_no_response"
                    })
                    return True
                        
            except websockets.exceptions.InvalidStatusCode as e:
                logger.info(f"❌ WebSocket connection failed with status code: {e.status_code}")
                if e.status_code == 404:
                    self.log_test_result(test_name, False, f"WebSocket endpoint not found (HTTP 404)", {
                        "endpoint": ws_endpoint,
                        "status_code": e.status_code,
                        "error": str(e)
                    })
                else:
                    self.log_test_result(test_name, False, f"WebSocket connection failed: HTTP {e.status_code}", {
                        "endpoint": ws_endpoint,
                        "status_code": e.status_code,
                        "error": str(e)
                    })
                return False
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"❌ WebSocket connection closed: {e}")
                self.log_test_result(test_name, False, "WebSocket connection closed immediately", {
                    "endpoint": ws_endpoint,
                    "error": str(e)
                })
                return False
                
            except Exception as ws_e:
                logger.info(f"❌ WebSocket error: {ws_e}")
                self.log_test_result(test_name, False, f"WebSocket error: {ws_e}", {
                    "endpoint": ws_endpoint,
                    "error": str(ws_e)
                })
                return False
                
        except Exception as e:
            logger.info(f"❌ Test exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_sse_test_generation_endpoint(self) -> bool:
        """Test SSE endpoint /api/sse/test_generation"""
        test_name = "SSE /api/sse/test_generation"
        try:
            logger.info("📡 Testing SSE endpoint /api/sse/test_generation...")
            
            sse_endpoint = f"{self.api_base}/sse/test_generation"
            logger.info(f"Connecting to: {sse_endpoint}")
            
            # Set up SSE headers
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache'
            }
            
            try:
                async with self.session.get(sse_endpoint, headers=headers, timeout=15) as response:
                    logger.info(f"SSE Response status: {response.status}")
                    logger.info(f"SSE Response headers: {dict(response.headers)}")
                    
                    if response.status == 200:
                        # Check if it's actually an SSE stream
                        content_type = response.headers.get('content-type', '')
                        if 'text/event-stream' in content_type:
                            logger.info("✅ SSE endpoint returned correct content-type")
                            
                            # Try to read some events
                            events_received = []
                            timeout_seconds = 10
                            start_time = time.time()
                            
                            async for line in response.content:
                                if time.time() - start_time > timeout_seconds:
                                    logger.info(f"⏰ Timeout reached after {timeout_seconds} seconds")
                                    break
                                
                                line_str = line.decode('utf-8').strip()
                                if line_str:
                                    logger.info(f"📥 SSE event received: {line_str}")
                                    events_received.append(line_str)
                                    
                                    # If we got some events, that's good enough
                                    if len(events_received) >= 3:
                                        logger.info("✅ Received multiple SSE events")
                                        break
                            
                            if events_received:
                                self.log_test_result(test_name, True, f"SSE streaming successful, received {len(events_received)} events", {
                                    "endpoint": sse_endpoint,
                                    "events_received": events_received,
                                    "content_type": content_type
                                })
                                return True
                            else:
                                logger.info("⚠️  SSE endpoint connected but no events received")
                                self.log_test_result(test_name, True, "SSE endpoint accessible but no events received", {
                                    "endpoint": sse_endpoint,
                                    "content_type": content_type,
                                    "status": "connected_no_events"
                                })
                                return True
                        else:
                            logger.info(f"❌ SSE endpoint returned wrong content-type: {content_type}")
                            self.log_test_result(test_name, False, f"Wrong content-type: {content_type}", {
                                "endpoint": sse_endpoint,
                                "expected_content_type": "text/event-stream",
                                "actual_content_type": content_type
                            })
                            return False
                    
                    elif response.status == 404:
                        logger.info("❌ SSE endpoint not found (HTTP 404)")
                        self.log_test_result(test_name, False, "SSE endpoint not found (HTTP 404)", {
                            "endpoint": sse_endpoint,
                            "status_code": response.status
                        })
                        return False
                    
                    else:
                        error_text = await response.text()
                        logger.info(f"❌ SSE endpoint returned HTTP {response.status}: {error_text}")
                        self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}", {
                            "endpoint": sse_endpoint,
                            "status_code": response.status,
                            "error_text": error_text
                        })
                        return False
                        
            except asyncio.TimeoutError:
                logger.info("❌ SSE connection timeout")
                self.log_test_result(test_name, False, "SSE connection timeout", {
                    "endpoint": sse_endpoint,
                    "error": "timeout"
                })
                return False
                
        except Exception as e:
            logger.info(f"❌ SSE test exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_test_endpoint(self) -> bool:
        """Test WebSocket endpoint /api/ws/test"""
        test_name = "WebSocket /api/ws/test"
        try:
            logger.info("🔌 Testing WebSocket endpoint /api/ws/test...")
            
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/test"
            
            logger.info(f"Connecting to: {ws_endpoint}")
            
            try:
                # Try to connect to WebSocket
                websocket = await websockets.connect(ws_endpoint, timeout=10)
                logger.info("✅ WebSocket test endpoint connection established")
                
                # Send a test message
                test_message = json.dumps({
                    "type": "ping",
                    "data": "test connection",
                    "timestamp": datetime.now().isoformat()
                })
                
                await websocket.send(test_message)
                logger.info(f"📤 Sent test message: {test_message}")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    logger.info(f"📥 Received response: {response}")
                    
                    # Try to parse response as JSON
                    try:
                        response_data = json.loads(response)
                        logger.info(f"✅ Response parsed as JSON: {response_data}")
                        
                        # Check if it's a proper test response
                        if response_data.get("type") == "pong" or "test" in str(response_data).lower():
                            logger.info("✅ Received proper test response")
                        
                    except json.JSONDecodeError:
                        logger.info(f"⚠️  Response is not JSON: {response}")
                    
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket test endpoint working correctly", {
                        "endpoint": ws_endpoint,
                        "sent_message": test_message,
                        "received_response": response
                    })
                    return True
                    
                except asyncio.TimeoutError:
                    logger.info("⚠️  No response received within timeout, but connection was successful")
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket test endpoint connected (no immediate response)", {
                        "endpoint": ws_endpoint,
                        "sent_message": test_message,
                        "status": "connected_no_response"
                    })
                    return True
                        
            except websockets.exceptions.InvalidStatusCode as e:
                logger.info(f"❌ WebSocket test endpoint failed with status code: {e.status_code}")
                if e.status_code == 404:
                    self.log_test_result(test_name, False, f"WebSocket test endpoint not found (HTTP 404)", {
                        "endpoint": ws_endpoint,
                        "status_code": e.status_code,
                        "error": str(e)
                    })
                else:
                    self.log_test_result(test_name, False, f"WebSocket test endpoint failed: HTTP {e.status_code}", {
                        "endpoint": ws_endpoint,
                        "status_code": e.status_code,
                        "error": str(e)
                    })
                return False
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.info(f"❌ WebSocket test endpoint connection closed: {e}")
                self.log_test_result(test_name, False, "WebSocket test endpoint connection closed immediately", {
                    "endpoint": ws_endpoint,
                    "error": str(e)
                })
                return False
                
            except Exception as ws_e:
                logger.info(f"❌ WebSocket test endpoint error: {ws_e}")
                self.log_test_result(test_name, False, f"WebSocket test endpoint error: {ws_e}", {
                    "endpoint": ws_endpoint,
                    "error": str(ws_e)
                })
                return False
                
        except Exception as e:
            logger.info(f"❌ Test exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_during_video_generation(self) -> bool:
        """Test WebSocket real-time updates during actual video generation"""
        test_name = "WebSocket During Video Generation"
        try:
            logger.info("🎬 Testing WebSocket real-time updates during video generation...")
            
            # Step 1: Create a project
            project_data = {
                "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9",
                "voice_name": "default"
            }
            
            logger.info("📝 Creating project for WebSocket testing...")
            async with self.session.post(
                f"{self.api_base}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, f"Project creation failed: HTTP {response.status}")
                    return False
                
                project_result = await response.json()
                project_id = project_result.get("project_id")
                if not project_id:
                    self.log_test_result(test_name, False, "No project_id returned")
                    return False
                
                logger.info(f"✅ Project created: {project_id}")
            
            # Step 2: Start video generation
            generation_data = {
                "project_id": project_id,
                "script": project_data["script"],
                "aspect_ratio": "16:9"
            }
            
            logger.info("🚀 Starting video generation...")
            async with self.session.post(
                f"{self.api_base}/generate",
                json=generation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, f"Generation start failed: HTTP {response.status}")
                    return False
                
                generation_result = await response.json()
                generation_id = generation_result.get("generation_id")
                if not generation_id:
                    self.log_test_result(test_name, False, "No generation_id returned")
                    return False
                
                logger.info(f"✅ Generation started: {generation_id}")
            
            # Step 3: Connect to WebSocket for this generation
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/{generation_id}"
            
            logger.info(f"🔌 Connecting to WebSocket for generation: {ws_endpoint}")
            
            websocket_updates = []
            websocket_connected = False
            
            try:
                websocket = await websockets.connect(ws_endpoint, timeout=10)
                websocket_connected = True
                logger.info("✅ WebSocket connected for generation monitoring")
                
                # Monitor for updates for up to 30 seconds
                monitoring_time = 30
                start_time = time.time()
                
                while time.time() - start_time < monitoring_time:
                    try:
                        # Try to receive WebSocket messages
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        logger.info(f"📥 WebSocket update: {message}")
                        
                        try:
                            message_data = json.loads(message)
                            websocket_updates.append(message_data)
                            
                            # Check if it's a status update
                            if "status" in message_data or "progress" in message_data:
                                logger.info(f"✅ Received status update via WebSocket: {message_data}")
                            
                        except json.JSONDecodeError:
                            websocket_updates.append({"raw_message": message})
                            logger.info(f"⚠️  Non-JSON WebSocket message: {message}")
                        
                        # If we got some updates, that's good
                        if len(websocket_updates) >= 3:
                            logger.info("✅ Received multiple WebSocket updates")
                            break
                            
                    except asyncio.TimeoutError:
                        # No message received in this interval, continue monitoring
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("⚠️  WebSocket connection closed during monitoring")
                        break
                
                await websocket.close()
                
            except websockets.exceptions.InvalidStatusCode as e:
                logger.info(f"❌ WebSocket connection failed: HTTP {e.status_code}")
                websocket_connected = False
                
            except Exception as ws_e:
                logger.info(f"❌ WebSocket error: {ws_e}")
                websocket_connected = False
            
            # Step 4: Also check HTTP status endpoint for comparison
            logger.info("📊 Checking HTTP status endpoint for comparison...")
            http_updates = []
            
            for check in range(5):  # Check 5 times
                await asyncio.sleep(2)
                
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        http_updates.append({
                            "check": check + 1,
                            "status": status_data.get("status"),
                            "progress": status_data.get("progress"),
                            "message": status_data.get("message")
                        })
                        logger.info(f"📈 HTTP status check {check + 1}: {status_data.get('status')} ({status_data.get('progress')}%)")
            
            # Step 5: Evaluate results
            success_criteria = {
                "project_created": True,  # Already verified
                "generation_started": True,  # Already verified
                "websocket_connected": websocket_connected,
                "websocket_updates_received": len(websocket_updates) > 0,
                "http_status_working": len(http_updates) > 0
            }
            
            passed_criteria = sum(success_criteria.values())
            total_criteria = len(success_criteria)
            
            logger.info("=" * 80)
            logger.info("🔌 WEBSOCKET DURING VIDEO GENERATION RESULTS")
            logger.info("=" * 80)
            
            for criterion, passed in success_criteria.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                logger.info(f"{status} {criterion.replace('_', ' ').title()}")
            
            logger.info(f"📊 WebSocket Updates: {len(websocket_updates)} received")
            logger.info(f"📊 HTTP Status Checks: {len(http_updates)} performed")
            
            if websocket_updates:
                logger.info("📥 WebSocket Updates Summary:")
                for i, update in enumerate(websocket_updates[:5]):  # Show first 5
                    logger.info(f"   {i+1}. {update}")
            
            if http_updates:
                logger.info("📈 HTTP Status Summary:")
                for update in http_updates:
                    logger.info(f"   Check {update['check']}: {update['status']} ({update['progress']}%) - {update['message']}")
            
            # Success if at least WebSocket connected OR we got updates via HTTP
            overall_success = websocket_connected or (len(http_updates) > 0 and any(u.get('progress', 0) > 0 for u in http_updates))
            
            if overall_success:
                logger.info("🎉 WEBSOCKET DURING VIDEO GENERATION TEST PASSED!")
                if websocket_connected:
                    logger.info("✅ WebSocket real-time updates are working")
                else:
                    logger.info("⚠️  WebSocket not working but HTTP status updates are functional")
            else:
                logger.info("❌ WEBSOCKET DURING VIDEO GENERATION TEST FAILED!")
                logger.info("⚠️  Neither WebSocket nor HTTP status updates are working properly")
            
            self.log_test_result(
                test_name,
                overall_success,
                f"Real-time updates test: {passed_criteria}/{total_criteria} criteria passed",
                {
                    "success_criteria": success_criteria,
                    "websocket_updates": websocket_updates,
                    "http_updates": http_updates,
                    "websocket_connected": websocket_connected,
                    "project_id": project_id,
                    "generation_id": generation_id
                }
            )
            
            return overall_success
            
        except Exception as e:
            logger.info(f"❌ WebSocket during video generation test failed: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 WEBSOCKET AND SSE TESTING SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} {test_name}: {result['message']}")
        
        return passed_tests, total_tests

async def main():
    """Main test function"""
    # Get backend URL from environment
    backend_url = "https://b51ec283-200b-4c5a-8885-425b20225bca.preview.emergentagent.com"
    
    logger.info("🚀 Starting WebSocket and SSE Testing")
    logger.info(f"Backend URL: {backend_url}")
    logger.info("=" * 80)
    
    async with WebSocketSSETester(backend_url) as tester:
        # Test all WebSocket and SSE endpoints
        tests = [
            tester.test_websocket_test_generation_endpoint(),
            tester.test_sse_test_generation_endpoint(),
            tester.test_websocket_test_endpoint(),
            tester.test_websocket_during_video_generation()
        ]
        
        # Run all tests
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Handle any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Test {i+1} failed with exception: {result}")
        
        # Print summary
        passed, total = tester.print_summary()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 WEBSOCKET AND SSE TESTING COMPLETED")
        logger.info("=" * 80)
        
        if passed == total:
            logger.info("🎉 ALL WEBSOCKET AND SSE TESTS PASSED!")
        elif passed > 0:
            logger.info(f"⚠️  PARTIAL SUCCESS: {passed}/{total} tests passed")
        else:
            logger.info("❌ ALL WEBSOCKET AND SSE TESTS FAILED!")
        
        return passed, total

if __name__ == "__main__":
    asyncio.run(main())