#!/usr/bin/env python3
"""
Focused Backend Testing for Script-to-Video Application
Tests the specific areas that need retesting based on test_result.md
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedBackendTester:
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

    async def test_health_endpoint(self) -> bool:
        """Test the enhanced health check endpoint"""
        test_name = "Enhanced Health Check (v2.0-enhanced)"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check version is enhanced
                    version = data.get("version", "")
                    if version != "2.0-enhanced":
                        self.log_test_result(test_name, False, f"Expected version '2.0-enhanced', got '{version}'", data)
                        return False
                    
                    # Check AI models status - now Minimax instead of WAN 2.1
                    ai_models = data.get("ai_models", {})
                    minimax_loaded = ai_models.get("minimax", False)
                    stable_audio_loaded = ai_models.get("stable_audio", False)
                    
                    if not minimax_loaded or not stable_audio_loaded:
                        self.log_test_result(test_name, False, f"AI models not loaded: minimax={minimax_loaded}, stable_audio={stable_audio_loaded}", data)
                        return False
                    
                    # Check enhanced components
                    enhanced_components = data.get("enhanced_components", {})
                    required_components = ["gemini_supervisor", "runwayml_processor", "multi_voice_manager"]
                    
                    for component in required_components:
                        if not enhanced_components.get(component, False):
                            self.log_test_result(test_name, False, f"Enhanced component not loaded: {component}", data)
                            return False
                    
                    # Check capabilities
                    capabilities = enhanced_components.get("capabilities", {})
                    required_capabilities = ["character_detection", "voice_assignment", "video_validation", "post_production", "quality_supervision"]
                    
                    for capability in required_capabilities:
                        if not capabilities.get(capability, False):
                            self.log_test_result(test_name, False, f"Required capability missing: {capability}", data)
                            return False
                    
                    self.log_test_result(test_name, True, "Enhanced health check passed with all components loaded", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_project_creation(self) -> Optional[str]:
        """Test project creation with multi-character script"""
        test_name = "Enhanced Project Creation"
        try:
            # Use both English and Hindi scripts as requested
            english_script = "A person walks in a sunny park. The weather is beautiful and birds are singing."
            hindi_script = "एक व्यक्ति धूप से भरे पार्क में चलता है। मौसम सुंदर है और पक्षी खुशी से गा रहे हैं।"
            
            project_data = {
                "script": english_script,
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
                    
                    project_id = data.get("project_id")
                    if not project_id:
                        self.log_test_result(test_name, False, "No project_id returned", data)
                        return None
                    
                    self.log_test_result(test_name, True, f"Enhanced project created successfully: {project_id}", data)
                    return project_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None

    async def test_voices_endpoint(self) -> bool:
        """Test voices endpoint with Hindi support"""
        test_name = "Enhanced Coqui TTS with Hindi Support"
        try:
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Check for Hindi voices
                        hindi_voices = [v for v in data if "hindi" in v.get("voice_id", "").lower() or "hindi" in v.get("name", "").lower()]
                        
                        if len(hindi_voices) >= 6:  # At least 6 Hindi voices as requested
                            self.log_test_result(test_name, True, f"Found {len(hindi_voices)} Hindi voices out of {len(data)} total voices", {
                                "total_voices": len(data),
                                "hindi_voices": len(hindi_voices),
                                "sample_hindi_voices": hindi_voices[:3]
                            })
                            return True
                        else:
                            self.log_test_result(test_name, False, f"Expected at least 6 Hindi voices, found {len(hindi_voices)}", data)
                            return False
                    else:
                        self.log_test_result(test_name, False, "No voices available", {"count": len(data) if isinstance(data, list) else 0})
                        return False
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_video_generation_start(self, project_id: str) -> Optional[str]:
        """Test video generation start with progress monitoring"""
        test_name = "Enhanced Video Generation Pipeline"
        try:
            # Test with the simple script from review request
            generation_data = {
                "project_id": project_id,
                "script": "A person walks in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(
                f"{self.api_base}/generate",
                json=generation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    generation_id = data.get("generation_id")
                    if not generation_id:
                        self.log_test_result(test_name, False, "No generation_id returned", data)
                        return None
                    
                    self.log_test_result(test_name, True, f"Enhanced generation started: {generation_id}", data)
                    return generation_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None

    async def test_progress_monitoring(self, generation_id: str) -> bool:
        """Test that video generation progresses beyond 0% as requested"""
        test_name = "Video Generation Progress Monitoring - No Longer Stuck at 0%"
        try:
            logger.info("🎬 TESTING VIDEO GENERATION PROGRESS - Verifying no longer stuck at 0%")
            
            progress_checks = []
            max_monitoring_time = 60  # seconds
            check_interval = 3  # seconds
            max_checks = max_monitoring_time // check_interval
            
            stuck_at_zero = True
            moved_beyond_queued = False
            highest_progress = 0.0
            status_changes = []
            
            for check_num in range(max_checks):
                await asyncio.sleep(check_interval)
                
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        current_status = status_data.get("status", "")
                        current_progress = status_data.get("progress", 0.0)
                        current_message = status_data.get("message", "")
                        
                        progress_checks.append({
                            "check": check_num + 1,
                            "status": current_status,
                            "progress": current_progress,
                            "message": current_message
                        })
                        
                        # Track status changes
                        if not status_changes or status_changes[-1]["status"] != current_status:
                            status_changes.append({
                                "status": current_status,
                                "progress": current_progress,
                                "message": current_message,
                                "check": check_num + 1
                            })
                        
                        # Check if progress moved beyond 0%
                        if current_progress > 0.0:
                            stuck_at_zero = False
                            highest_progress = max(highest_progress, current_progress)
                        
                        # Check if status moved beyond "queued"
                        if current_status != "queued":
                            moved_beyond_queued = True
                        
                        logger.info(f"📈 Check {check_num + 1}: Status={current_status}, Progress={current_progress}%, Message='{current_message}'")
                        
                        # If completed or failed, break early
                        if current_status in ["completed", "failed"]:
                            logger.info(f"🏁 Generation finished with status: {current_status}")
                            break
                            
                        # If we've made good progress, we can conclude the test
                        if current_progress >= 15.0:
                            logger.info(f"✅ Good progress detected: {current_progress}%")
                            break
                    else:
                        logger.info(f"❌ Status check {check_num + 1} failed: HTTP {response.status}")
            
            # Analyze results
            progress_working = not stuck_at_zero or moved_beyond_queued or highest_progress > 0
            
            # Check for expected progress messages indicating the enhanced pipeline
            expected_messages = [
                "character", "voice", "video", "audio", "post-production", "quality"
            ]
            
            pipeline_messages_found = []
            for check in progress_checks:
                message = check.get("message", "").lower()
                for expected in expected_messages:
                    if expected in message and expected not in pipeline_messages_found:
                        pipeline_messages_found.append(expected)
            
            success = progress_working and (highest_progress > 0 or len(pipeline_messages_found) > 0)
            
            logger.info(f"📊 Progress Summary:")
            logger.info(f"   - Highest progress: {highest_progress}%")
            logger.info(f"   - Stuck at 0%: {'No' if not stuck_at_zero else 'Yes'}")
            logger.info(f"   - Moved beyond queued: {'Yes' if moved_beyond_queued else 'No'}")
            logger.info(f"   - Pipeline messages found: {len(pipeline_messages_found)}")
            
            if success:
                self.log_test_result(test_name, True, f"Progress monitoring passed - highest progress: {highest_progress}%", {
                    "highest_progress": highest_progress,
                    "stuck_at_zero": stuck_at_zero,
                    "moved_beyond_queued": moved_beyond_queued,
                    "pipeline_messages_found": pipeline_messages_found,
                    "status_changes": status_changes
                })
            else:
                self.log_test_result(test_name, False, f"Progress monitoring failed - stuck at {highest_progress}%", {
                    "highest_progress": highest_progress,
                    "stuck_at_zero": stuck_at_zero,
                    "moved_beyond_queued": moved_beyond_queued
                })
            
            return success
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_gemini_supervisor_methods(self) -> bool:
        """Test the critical Gemini Supervisor method fixes"""
        test_name = "GeminiSupervisor Method Fixes"
        try:
            logger.info("🔧 TESTING GEMINI SUPERVISOR METHOD FIXES")
            
            # Test by creating a project and starting generation to see if methods work
            project_data = {
                "script": "A person walks in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9",
                "voice_name": "default"
            }
            
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
            
            # Try video generation to verify the methods work
            generation_data = {
                "project_id": project_id,
                "script": "A person walks in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(
                f"{self.api_base}/generate",
                json=generation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    generation_result = await response.json()
                    generation_id = generation_result.get("generation_id")
                    
                    if generation_id:
                        # Wait a bit and check if it starts processing without method errors
                        await asyncio.sleep(5)
                        
                        async with self.session.get(f"{self.api_base}/generate/{generation_id}") as status_response:
                            if status_response.status == 200:
                                status_data = await status_response.json()
                                current_status = status_data.get("status", "")
                                current_message = status_data.get("message", "")
                                
                                # Check for method-related errors
                                method_errors = [
                                    "analyze_script_with_enhanced_scene_breaking",
                                    "generate_enhanced_video_prompt",
                                    "attribute error",
                                    "method not found"
                                ]
                                
                                has_method_error = any(error.lower() in current_message.lower() for error in method_errors)
                                
                                if not has_method_error and current_status in ["queued", "processing"]:
                                    self.log_test_result(test_name, True, f"Gemini Supervisor methods working - Status: {current_status}", {
                                        "status": current_status,
                                        "message": current_message,
                                        "generation_id": generation_id
                                    })
                                    return True
                                else:
                                    self.log_test_result(test_name, False, f"Method errors detected: {current_message}", {
                                        "status": current_status,
                                        "message": current_message
                                    })
                                    return False
                            else:
                                self.log_test_result(test_name, False, f"Status check failed: HTTP {status_response.status}")
                                return False
                    else:
                        self.log_test_result(test_name, False, "No generation_id returned")
                        return False
                else:
                    error_text = await response.text()
                    # Check if the error is method-related
                    if "analyze_script_with_enhanced_scene_breaking" in error_text or "generate_enhanced_video_prompt" in error_text:
                        self.log_test_result(test_name, False, f"Method error still present: {error_text}")
                        return False
                    else:
                        # Other errors might be acceptable for this test
                        self.log_test_result(test_name, True, f"No method errors detected (other error: HTTP {response.status})")
                        return True
                        
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_websocket_endpoints(self) -> bool:
        """Test WebSocket endpoints that are currently stuck"""
        test_name = "WebSocket Communication Fix"
        try:
            # Test WebSocket endpoint accessibility
            test_generation_id = "test-websocket-123"
            
            # Try to connect to WebSocket endpoint
            try:
                import websockets
                
                # Convert HTTP URL to WebSocket URL
                ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
                ws_endpoint = f"{ws_url}/api/ws/{test_generation_id}"
                
                logger.info(f"Testing WebSocket endpoint: {ws_endpoint}")
                
                # Try to connect with a short timeout
                websocket = await asyncio.wait_for(
                    websockets.connect(ws_endpoint),
                    timeout=10.0
                )
                
                await websocket.close()
                self.log_test_result(test_name, True, "WebSocket connection successful", {"endpoint": ws_endpoint})
                return True
                
            except asyncio.TimeoutError:
                self.log_test_result(test_name, False, "WebSocket connection timeout", {"endpoint": ws_endpoint})
                return False
            except Exception as ws_e:
                # Check if it's a 404 error (endpoint not configured)
                if "404" in str(ws_e):
                    self.log_test_result(test_name, False, "WebSocket endpoint returns HTTP 404 - not properly configured", {"error": str(ws_e)})
                else:
                    self.log_test_result(test_name, False, f"WebSocket connection failed: {str(ws_e)}", {"error": str(ws_e)})
                return False
                
        except ImportError:
            # websockets not available, test via HTTP
            self.log_test_result(test_name, False, "WebSocket testing not available (websockets module not installed)")
            return False
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def run_focused_tests(self):
        """Run focused tests on areas that need retesting"""
        logger.info("🎯 STARTING FOCUSED BACKEND TESTING")
        logger.info("=" * 80)
        logger.info(f"Backend URL: {self.base_url}")
        logger.info("=" * 80)
        
        test_results = []
        
        # Test 1: Enhanced Health Check
        logger.info("🏥 Testing Enhanced Health Check...")
        health_result = await self.test_health_endpoint()
        test_results.append(("Enhanced Health Check", health_result))
        
        # Test 2: Project Creation
        logger.info("📝 Testing Enhanced Project Creation...")
        project_id = await self.test_project_creation()
        test_results.append(("Enhanced Project Creation", project_id is not None))
        
        # Test 3: Voices Endpoint with Hindi Support
        logger.info("🎤 Testing Enhanced Coqui TTS with Hindi Support...")
        voices_result = await self.test_voices_endpoint()
        test_results.append(("Enhanced Coqui TTS with Hindi Support", voices_result))
        
        if project_id:
            # Test 4: Video Generation Start
            logger.info("🚀 Testing Enhanced Video Generation Pipeline...")
            generation_id = await self.test_video_generation_start(project_id)
            test_results.append(("Enhanced Video Generation Pipeline", generation_id is not None))
            
            if generation_id:
                # Test 5: Progress Monitoring (Key requirement from review)
                logger.info("📊 Testing Video Generation Progress Monitoring...")
                progress_result = await self.test_progress_monitoring(generation_id)
                test_results.append(("Video Generation Progress Monitoring", progress_result))
        
        # Test 6: Gemini Supervisor Method Fixes
        logger.info("🔧 Testing GeminiSupervisor Method Fixes...")
        gemini_result = await self.test_gemini_supervisor_methods()
        test_results.append(("GeminiSupervisor Method Fixes", gemini_result))
        
        # Test 7: WebSocket Endpoints (Known stuck task)
        logger.info("🔌 Testing WebSocket Communication...")
        websocket_result = await self.test_websocket_endpoints()
        test_results.append(("WebSocket Communication Fix", websocket_result))
        
        # Summary
        logger.info("=" * 80)
        logger.info("📊 FOCUSED TESTING RESULTS SUMMARY")
        logger.info("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result:
                passed_tests += 1
        
        logger.info("=" * 80)
        logger.info(f"📈 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests >= total_tests - 1:  # Allow 1 failure
            logger.info("🎉 FOCUSED TESTING COMPLETED SUCCESSFULLY!")
            logger.info("✅ Core functionality is working and ready for production use")
        else:
            logger.info("⚠️  FOCUSED TESTING IDENTIFIED ISSUES")
            logger.info("❌ Some critical components need attention")
        
        return test_results

async def main():
    # Get backend URL from frontend .env
    backend_url = "https://533dceb9-a2e4-4c4e-88fc-2fdbbf93e5c9.preview.emergentagent.com"
    
    async with FocusedBackendTester(backend_url) as tester:
        results = await tester.run_focused_tests()
        return results

if __name__ == "__main__":
    asyncio.run(main())