#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Script-to-Video Application
Tests all major backend functionalities including AI models, database, and third-party integrations
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

class BackendTester:
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
    
    async def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        test_name = "Health Check"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    required_fields = ["status", "timestamp", "ai_models"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Check AI models status
                    ai_models = data.get("ai_models", {})
                    wan21_loaded = ai_models.get("wan21", False)
                    stable_audio_loaded = ai_models.get("stable_audio", False)
                    
                    if not wan21_loaded or not stable_audio_loaded:
                        self.log_test_result(test_name, False, f"AI models not loaded: wan21={wan21_loaded}, stable_audio={stable_audio_loaded}", data)
                        return False
                    
                    self.log_test_result(test_name, True, "Health check passed, all AI models loaded", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_project_creation(self) -> Optional[str]:
        """Test project creation endpoint"""
        test_name = "Project Creation"
        try:
            project_data = {
                "script": "A beautiful sunrise over mountains with birds flying in the sky. The scene is peaceful and serene.",
                "aspect_ratio": "16:9",
                "voice_name": "default"
            }
            
            async with self.session.post(
                f"{self.api_base}/projects",
                json=project_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    required_fields = ["project_id", "status", "created_at"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", data)
                        return None
                    
                    project_id = data.get("project_id")
                    if not project_id:
                        self.log_test_result(test_name, False, "No project_id returned", data)
                        return None
                    
                    self.log_test_result(test_name, True, f"Project created successfully: {project_id}", data)
                    return project_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_get_project(self, project_id: str) -> bool:
        """Test getting project details"""
        test_name = "Get Project"
        try:
            async with self.session.get(f"{self.api_base}/projects/{project_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if project data is returned
                    if "project_id" in data and data["project_id"] == project_id:
                        self.log_test_result(test_name, True, "Project retrieved successfully", data)
                        return True
                    else:
                        self.log_test_result(test_name, False, "Invalid project data returned", data)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_voices_endpoint(self) -> bool:
        """Test ElevenLabs voices integration"""
        test_name = "Voices Endpoint"
        try:
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if voices are returned
                    if isinstance(data, list):
                        if len(data) > 0:
                            # Check voice structure
                            voice = data[0]
                            required_fields = ["voice_id", "name"]
                            missing_fields = [field for field in required_fields if field not in voice]
                            
                            if missing_fields:
                                self.log_test_result(test_name, False, f"Voice missing fields: {missing_fields}", data)
                                return False
                            
                            self.log_test_result(test_name, True, f"Retrieved {len(data)} voices successfully", {"count": len(data), "sample": data[0]})
                            return True
                        else:
                            self.log_test_result(test_name, True, "No voices available (empty list)", {"count": 0})
                            return True
                    else:
                        self.log_test_result(test_name, False, "Invalid response format (not a list)", data)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_generation_start(self, project_id: str) -> Optional[str]:
        """Test starting video generation"""
        test_name = "Start Generation"
        try:
            generation_data = {
                "project_id": project_id,
                "script": "A peaceful mountain landscape at sunrise with gentle clouds.",
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(
                f"{self.api_base}/generate",
                json=generation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    required_fields = ["generation_id", "status", "progress"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", data)
                        return None
                    
                    generation_id = data.get("generation_id")
                    if not generation_id:
                        self.log_test_result(test_name, False, "No generation_id returned", data)
                        return None
                    
                    self.log_test_result(test_name, True, f"Generation started: {generation_id}", data)
                    return generation_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_generation_status(self, generation_id: str) -> bool:
        """Test getting generation status"""
        test_name = "Generation Status"
        try:
            async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if status data is returned
                    if "status" in data:
                        self.log_test_result(test_name, True, f"Status retrieved: {data.get('status')}", data)
                        return True
                    else:
                        self.log_test_result(test_name, False, "No status field in response", data)
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_websocket_connection(self, generation_id: str) -> bool:
        """Test WebSocket connection for real-time updates"""
        test_name = "WebSocket Connection"
        try:
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/{generation_id}"
            
            # Test WebSocket connection
            try:
                websocket = await websockets.connect(ws_endpoint)
                
                # Send a test message
                await websocket.send("ping")
                
                # Try to receive a message (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket connection successful", {"response": response})
                    return True
                except asyncio.TimeoutError:
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket connected (no immediate response)", {"status": "connected"})
                    return True
                        
            except websockets.exceptions.ConnectionClosed:
                self.log_test_result(test_name, False, "WebSocket connection closed immediately")
                return False
            except Exception as ws_e:
                self.log_test_result(test_name, False, f"WebSocket error: {ws_e}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling for invalid requests"""
        test_name = "Error Handling"
        error_tests_passed = 0
        total_error_tests = 4
        
        try:
            # Test 1: Invalid project creation
            async with self.session.post(
                f"{self.api_base}/projects",
                json={"invalid": "data"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status >= 400:
                    error_tests_passed += 1
                    logger.info("✅ Invalid project creation properly rejected")
                else:
                    logger.info("❌ Invalid project creation should have been rejected")
            
            # Test 2: Non-existent project
            async with self.session.get(f"{self.api_base}/projects/non-existent-id") as response:
                if response.status == 404:
                    error_tests_passed += 1
                    logger.info("✅ Non-existent project properly returns 404")
                else:
                    logger.info("❌ Non-existent project should return 404")
            
            # Test 3: Invalid generation request
            async with self.session.post(
                f"{self.api_base}/generate",
                json={"project_id": "invalid"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status >= 400:
                    error_tests_passed += 1
                    logger.info("✅ Invalid generation request properly rejected")
                else:
                    logger.info("❌ Invalid generation request should have been rejected")
            
            # Test 4: Non-existent generation status
            async with self.session.get(f"{self.api_base}/generate/non-existent-id") as response:
                if response.status == 404:
                    error_tests_passed += 1
                    logger.info("✅ Non-existent generation properly returns 404")
                else:
                    logger.info("❌ Non-existent generation should return 404")
            
            success = error_tests_passed == total_error_tests
            self.log_test_result(
                test_name, 
                success, 
                f"Error handling tests: {error_tests_passed}/{total_error_tests} passed",
                {"passed": error_tests_passed, "total": total_error_tests}
            )
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        logger.info("🚀 Starting comprehensive backend API testing...")
        logger.info(f"Testing backend at: {self.base_url}")
        
        start_time = time.time()
        
        # Test 1: Health Check
        health_ok = await self.test_health_check()
        
        # Test 2: Project Creation
        project_id = await self.test_project_creation()
        project_creation_ok = project_id is not None
        
        # Test 3: Get Project (only if creation succeeded)
        get_project_ok = False
        if project_creation_ok:
            get_project_ok = await self.test_get_project(project_id)
        
        # Test 4: Voices Endpoint
        voices_ok = await self.test_voices_endpoint()
        
        # Test 5: Start Generation (only if project creation succeeded)
        generation_id = None
        generation_start_ok = False
        if project_creation_ok:
            generation_id = await self.test_generation_start(project_id)
            generation_start_ok = generation_id is not None
        
        # Test 6: Generation Status (only if generation started)
        generation_status_ok = False
        if generation_start_ok:
            generation_status_ok = await self.test_generation_status(generation_id)
        
        # Test 7: WebSocket Connection (only if generation started)
        websocket_ok = False
        if generation_start_ok:
            websocket_ok = await self.test_websocket_connection(generation_id)
        
        # Test 8: Error Handling
        error_handling_ok = await self.test_error_handling()
        
        # Calculate results
        total_time = time.time() - start_time
        
        # Count tests
        tests_run = [
            ("Health Check", health_ok),
            ("Project Creation", project_creation_ok),
            ("Get Project", get_project_ok),
            ("Voices Endpoint", voices_ok),
            ("Start Generation", generation_start_ok),
            ("Generation Status", generation_status_ok),
            ("WebSocket Connection", websocket_ok),
            ("Error Handling", error_handling_ok)
        ]
        
        passed_tests = sum(1 for _, success in tests_run if success)
        total_tests = len(tests_run)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 BACKEND TESTING SUMMARY")
        logger.info("="*60)
        
        for test_name, success in tests_run:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        
        logger.info("-"*60)
        logger.info(f"📈 Results: {passed_tests}/{total_tests} tests passed")
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info(f"🎯 Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        overall_success = passed_tests == total_tests
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.info("⚠️  Some tests failed - check logs above for details")
        
        return {
            "overall_success": overall_success,
            "tests_passed": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "total_time": total_time,
            "individual_results": self.test_results,
            "critical_failures": [name for name, success in tests_run if not success]
        }

async def main():
    """Main test runner"""
    # Get backend URL from environment
    backend_url = "https://29fa5433-01eb-424d-b0c7-446ba0d581de.preview.emergentagent.com"
    
    async with BackendTester(backend_url) as tester:
        results = await tester.run_all_tests()
        
        # Return appropriate exit code
        return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)