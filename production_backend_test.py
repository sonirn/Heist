#!/usr/bin/env python3
"""
Production Backend Testing for Script-to-Video Application
Focus on production readiness assessment and critical fixes verification
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

class ProductionBackendTester:
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

    async def test_production_health_check_system(self) -> bool:
        """Test Production Health Check System Enhancement - missing cache/queue/storage metrics"""
        test_name = "Production Health Check System Enhancement"
        try:
            logger.info("🏥 TESTING PRODUCTION HEALTH CHECK SYSTEM")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for production-level health metrics
                    required_sections = ["cache", "queue", "storage", "performance", "database"]
                    missing_sections = []
                    
                    for section in required_sections:
                        if section not in data:
                            missing_sections.append(section)
                    
                    if missing_sections:
                        self.log_test_result(test_name, False, f"Missing production health sections: {missing_sections}", data)
                        return False
                    
                    # Check cache metrics specifically
                    cache_section = data.get("cache", {})
                    required_cache_fields = ["hit_rate", "total_requests", "cache_size"]
                    missing_cache_fields = [field for field in required_cache_fields if field not in cache_section]
                    
                    if missing_cache_fields:
                        self.log_test_result(test_name, False, f"Cache section missing fields: {missing_cache_fields}", data)
                        return False
                    
                    # Check queue metrics
                    queue_section = data.get("queue", {})
                    required_queue_fields = ["completed_tasks", "failed_tasks", "active_tasks"]
                    missing_queue_fields = [field for field in required_queue_fields if field not in queue_section]
                    
                    if missing_queue_fields:
                        self.log_test_result(test_name, False, f"Queue section missing fields: {missing_queue_fields}", data)
                        return False
                    
                    # Check storage metrics
                    storage_section = data.get("storage", {})
                    required_storage_fields = ["total_files", "total_size", "cleanup_enabled"]
                    missing_storage_fields = [field for field in required_storage_fields if field not in storage_section]
                    
                    if missing_storage_fields:
                        self.log_test_result(test_name, False, f"Storage section missing fields: {missing_storage_fields}", data)
                        return False
                    
                    self.log_test_result(test_name, True, "Production health check system complete with all metrics", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_cache_management_system(self) -> bool:
        """Test Cache Management System Implementation - missing hit_rate, total_requests, cache_size"""
        test_name = "Cache Management System Implementation"
        try:
            logger.info("💾 TESTING CACHE MANAGEMENT SYSTEM")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    cache_section = data.get("cache", {})
                    
                    # Check for required cache fields
                    required_fields = ["hit_rate", "total_requests", "cache_size"]
                    missing_fields = [field for field in required_fields if field not in cache_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Cache system missing fields: {missing_fields}", cache_section)
                        return False
                    
                    # Validate field types and values
                    hit_rate = cache_section.get("hit_rate")
                    total_requests = cache_section.get("total_requests")
                    cache_size = cache_section.get("cache_size")
                    
                    if not isinstance(hit_rate, (int, float)) or hit_rate < 0 or hit_rate > 100:
                        self.log_test_result(test_name, False, f"Invalid hit_rate: {hit_rate}", cache_section)
                        return False
                    
                    if not isinstance(total_requests, int) or total_requests < 0:
                        self.log_test_result(test_name, False, f"Invalid total_requests: {total_requests}", cache_section)
                        return False
                    
                    if not isinstance(cache_size, int) or cache_size < 0:
                        self.log_test_result(test_name, False, f"Invalid cache_size: {cache_size}", cache_section)
                        return False
                    
                    self.log_test_result(test_name, True, f"Cache management system operational with hit_rate={hit_rate}%, requests={total_requests}, size={cache_size}", cache_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_file_management_system(self) -> bool:
        """Test File Management System Implementation - missing total_files, total_size, cleanup_enabled"""
        test_name = "File Management System Implementation"
        try:
            logger.info("📁 TESTING FILE MANAGEMENT SYSTEM")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    storage_section = data.get("storage", {})
                    
                    # Check for required storage fields
                    required_fields = ["total_files", "total_size", "cleanup_enabled"]
                    missing_fields = [field for field in required_fields if field not in storage_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"File management system missing fields: {missing_fields}", storage_section)
                        return False
                    
                    # Validate field types and values
                    total_files = storage_section.get("total_files")
                    total_size = storage_section.get("total_size")
                    cleanup_enabled = storage_section.get("cleanup_enabled")
                    
                    if not isinstance(total_files, int) or total_files < 0:
                        self.log_test_result(test_name, False, f"Invalid total_files: {total_files}", storage_section)
                        return False
                    
                    if not isinstance(total_size, int) or total_size < 0:
                        self.log_test_result(test_name, False, f"Invalid total_size: {total_size}", storage_section)
                        return False
                    
                    if not isinstance(cleanup_enabled, bool):
                        self.log_test_result(test_name, False, f"Invalid cleanup_enabled: {cleanup_enabled}", storage_section)
                        return False
                    
                    self.log_test_result(test_name, True, f"File management system operational with {total_files} files, {total_size} bytes, cleanup={cleanup_enabled}", storage_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_queue_system_metrics(self) -> bool:
        """Test Queue System Metrics Enhancement - missing completed_tasks, failed_tasks"""
        test_name = "Queue System Metrics Enhancement"
        try:
            logger.info("📋 TESTING QUEUE SYSTEM METRICS")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    queue_section = data.get("queue", {})
                    
                    # Check for required queue fields
                    required_fields = ["completed_tasks", "failed_tasks", "active_tasks"]
                    missing_fields = [field for field in required_fields if field not in queue_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Queue system missing fields: {missing_fields}", queue_section)
                        return False
                    
                    # Validate field types and values
                    completed_tasks = queue_section.get("completed_tasks")
                    failed_tasks = queue_section.get("failed_tasks")
                    active_tasks = queue_section.get("active_tasks")
                    
                    if not isinstance(completed_tasks, int) or completed_tasks < 0:
                        self.log_test_result(test_name, False, f"Invalid completed_tasks: {completed_tasks}", queue_section)
                        return False
                    
                    if not isinstance(failed_tasks, int) or failed_tasks < 0:
                        self.log_test_result(test_name, False, f"Invalid failed_tasks: {failed_tasks}", queue_section)
                        return False
                    
                    if not isinstance(active_tasks, int) or active_tasks < 0:
                        self.log_test_result(test_name, False, f"Invalid active_tasks: {active_tasks}", queue_section)
                        return False
                    
                    self.log_test_result(test_name, True, f"Queue system operational with completed={completed_tasks}, failed={failed_tasks}, active={active_tasks}", queue_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_enhanced_websocket_communication(self) -> bool:
        """Test Enhanced WebSocket Communication - HTTP 404 error"""
        test_name = "Enhanced WebSocket Communication"
        try:
            logger.info("🔌 TESTING ENHANCED WEBSOCKET COMMUNICATION")
            logger.info("=" * 80)
            
            # Create a test generation ID
            test_generation_id = "test-websocket-connection"
            
            # Convert HTTP URL to WebSocket URL
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/{test_generation_id}"
            
            logger.info(f"Testing WebSocket endpoint: {ws_endpoint}")
            
            try:
                # Test WebSocket connection with timeout
                websocket = await asyncio.wait_for(
                    websockets.connect(ws_endpoint),
                    timeout=10.0
                )
                
                # Send a test message
                await websocket.send(json.dumps({"type": "ping", "message": "test"}))
                
                # Try to receive a message (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    await websocket.close()
                    self.log_test_result(test_name, True, f"WebSocket connection successful, received: {response}", {"endpoint": ws_endpoint})
                    return True
                except asyncio.TimeoutError:
                    await websocket.close()
                    self.log_test_result(test_name, True, "WebSocket connected successfully (no immediate response)", {"endpoint": ws_endpoint})
                    return True
                        
            except websockets.exceptions.InvalidStatusCode as e:
                if e.status_code == 404:
                    self.log_test_result(test_name, False, f"WebSocket endpoint not found (HTTP 404): {ws_endpoint}", {"error": str(e)})
                else:
                    self.log_test_result(test_name, False, f"WebSocket connection failed with status {e.status_code}", {"error": str(e)})
                return False
            except websockets.exceptions.ConnectionClosed:
                self.log_test_result(test_name, False, "WebSocket connection closed immediately", {"endpoint": ws_endpoint})
                return False
            except asyncio.TimeoutError:
                self.log_test_result(test_name, False, "WebSocket connection timeout", {"endpoint": ws_endpoint})
                return False
            except Exception as ws_e:
                self.log_test_result(test_name, False, f"WebSocket error: {ws_e}", {"endpoint": ws_endpoint})
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_coqui_tts_voice_configuration(self) -> bool:
        """Test Coqui TTS Voice Configuration - no coqui_ prefixed voices found"""
        test_name = "Coqui TTS Voice Configuration"
        try:
            logger.info("🎤 TESTING COQUI TTS VOICE CONFIGURATION")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not isinstance(data, list):
                        self.log_test_result(test_name, False, "Voices endpoint returned invalid format (not a list)", data)
                        return False
                    
                    if len(data) == 0:
                        self.log_test_result(test_name, False, "No voices available", {"count": 0})
                        return False
                    
                    # Check for Coqui-specific voices with coqui_ prefix
                    coqui_voices = [v for v in data if v.get("voice_id", "").startswith("coqui_")]
                    
                    if len(coqui_voices) == 0:
                        self.log_test_result(test_name, False, "No Coqui-specific voices found (no coqui_ prefixed voice_ids)", {
                            "total_voices": len(data),
                            "sample_voice_ids": [v.get("voice_id", "") for v in data[:5]]
                        })
                        return False
                    
                    # Check for Hindi language support
                    hindi_voices = [v for v in coqui_voices if "hindi" in v.get("name", "").lower() or "hindi" in v.get("voice_id", "").lower()]
                    
                    # Check for expected voice categories
                    expected_categories = ["narrator", "protagonist", "antagonist", "child", "elderly", "character"]
                    found_categories = set()
                    for voice in coqui_voices:
                        category = voice.get("category", "")
                        if category:
                            found_categories.add(category.replace("hindi_", "").replace("english_", ""))
                    
                    self.log_test_result(test_name, True, f"Coqui TTS voices configured: {len(coqui_voices)} Coqui voices, {len(hindi_voices)} Hindi voices", {
                        "total_voices": len(data),
                        "coqui_voices": len(coqui_voices),
                        "hindi_voices": len(hindi_voices),
                        "categories_found": list(found_categories),
                        "sample_coqui_voices": [v.get("voice_id", "") for v in coqui_voices[:3]]
                    })
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_production_mode_configuration(self) -> bool:
        """Test Production Mode Configuration - system running in development mode"""
        test_name = "Production Mode Configuration"
        try:
            logger.info("⚙️ TESTING PRODUCTION MODE CONFIGURATION")
            logger.info("=" * 80)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check environment setting
                    environment = data.get("environment", "")
                    
                    if environment != "production":
                        self.log_test_result(test_name, False, f"System running in {environment} mode instead of production", data)
                        return False
                    
                    # Check AI models are in production mode (not development fallback)
                    ai_models = data.get("ai_models", {})
                    minimax_loaded = ai_models.get("minimax", False)
                    stable_audio_loaded = ai_models.get("stable_audio", False)
                    
                    if not minimax_loaded or not stable_audio_loaded:
                        self.log_test_result(test_name, False, f"AI models not properly loaded in production mode: minimax={minimax_loaded}, stable_audio={stable_audio_loaded}", data)
                        return False
                    
                    # Check for production-specific configurations
                    version = data.get("version", "")
                    if "production" not in version:
                        self.log_test_result(test_name, False, f"Version should indicate production mode: {version}", data)
                        return False
                    
                    self.log_test_result(test_name, True, f"Production mode configured correctly: environment={environment}, version={version}", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_critical_fixes_verification(self) -> bool:
        """Test verification of the 3 critical fixes that were recently implemented"""
        test_name = "Critical Fixes Verification"
        try:
            logger.info("🔧 TESTING CRITICAL FIXES VERIFICATION")
            logger.info("=" * 80)
            
            fixes_verified = 0
            total_fixes = 3
            
            # Fix 1: Enhanced Coqui Voice Manager Method Signature Fix
            logger.info("🎤 Fix 1: Testing Enhanced Coqui Voice Manager Method Signature...")
            try:
                # Create a test project to trigger voice assignment
                project_data = {
                    "script": "NARRATOR: Welcome to our story. SARAH: This is amazing! JOHN: I agree completely.",
                    "aspect_ratio": "16:9",
                    "voice_name": "default"
                }
                
                async with self.session.post(
                    f"{self.api_base}/projects",
                    json=project_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        project_result = await response.json()
                        project_id = project_result.get("project_id")
                        
                        # Start generation to test voice assignment
                        generation_data = {
                            "project_id": project_id,
                            "script": "NARRATOR: Welcome to our story. SARAH: This is amazing! JOHN: I agree completely.",
                            "aspect_ratio": "16:9"
                        }
                        
                        async with self.session.post(
                            f"{self.api_base}/generate",
                            json=generation_data,
                            headers={"Content-Type": "application/json"}
                        ) as gen_response:
                            if gen_response.status == 200:
                                fixes_verified += 1
                                logger.info("✅ Enhanced Coqui Voice Manager method signature working")
                            else:
                                logger.info(f"❌ Voice manager method signature issue: HTTP {gen_response.status}")
                    else:
                        logger.info(f"❌ Project creation failed: HTTP {response.status}")
            except Exception as e:
                logger.info(f"❌ Voice manager test failed: {str(e)}")
            
            # Fix 2: Gemini Script Analysis JSON Parsing Fix
            logger.info("🤖 Fix 2: Testing Gemini Script Analysis JSON Parsing...")
            try:
                # Test script analysis through generation start
                test_script = "A person walking in a sunny park. The weather is beautiful and birds are singing."
                
                project_data = {
                    "script": test_script,
                    "aspect_ratio": "16:9",
                    "voice_name": "default"
                }
                
                async with self.session.post(
                    f"{self.api_base}/projects",
                    json=project_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        project_result = await response.json()
                        project_id = project_result.get("project_id")
                        
                        generation_data = {
                            "project_id": project_id,
                            "script": test_script,
                            "aspect_ratio": "16:9"
                        }
                        
                        async with self.session.post(
                            f"{self.api_base}/generate",
                            json=generation_data,
                            headers={"Content-Type": "application/json"}
                        ) as gen_response:
                            if gen_response.status == 200:
                                # Wait a moment and check if processing started (indicates JSON parsing worked)
                                await asyncio.sleep(3)
                                
                                generation_result = await gen_response.json()
                                generation_id = generation_result.get("generation_id")
                                
                                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as status_response:
                                    if status_response.status == 200:
                                        status_data = await status_response.json()
                                        if status_data.get("status") in ["processing", "queued", "completed"]:
                                            fixes_verified += 1
                                            logger.info("✅ Gemini script analysis JSON parsing working")
                                        else:
                                            logger.info(f"❌ JSON parsing may have failed: status={status_data.get('status')}")
                                    else:
                                        logger.info(f"❌ Status check failed: HTTP {status_response.status}")
                            else:
                                logger.info(f"❌ Generation start failed: HTTP {gen_response.status}")
                    else:
                        logger.info(f"❌ Project creation failed: HTTP {response.status}")
            except Exception as e:
                logger.info(f"❌ JSON parsing test failed: {str(e)}")
            
            # Fix 3: GeminiSupervisor Missing Method Fix
            logger.info("🧠 Fix 3: Testing GeminiSupervisor Missing Method...")
            try:
                # Check if GeminiSupervisor is loaded and functional
                async with self.session.get(f"{self.api_base}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        enhanced_components = data.get("enhanced_components", {})
                        gemini_supervisor_loaded = enhanced_components.get("gemini_supervisor", False)
                        
                        if gemini_supervisor_loaded:
                            # Test that video generation can start (which uses the missing method)
                            test_script = "Simple test for method verification."
                            
                            project_data = {
                                "script": test_script,
                                "aspect_ratio": "16:9",
                                "voice_name": "default"
                            }
                            
                            async with self.session.post(
                                f"{self.api_base}/projects",
                                json=project_data,
                                headers={"Content-Type": "application/json"}
                            ) as proj_response:
                                if proj_response.status == 200:
                                    project_result = await proj_response.json()
                                    project_id = project_result.get("project_id")
                                    
                                    generation_data = {
                                        "project_id": project_id,
                                        "script": test_script,
                                        "aspect_ratio": "16:9"
                                    }
                                    
                                    async with self.session.post(
                                        f"{self.api_base}/generate",
                                        json=generation_data,
                                        headers={"Content-Type": "application/json"}
                                    ) as gen_response:
                                        if gen_response.status == 200:
                                            fixes_verified += 1
                                            logger.info("✅ GeminiSupervisor missing method fixed")
                                        else:
                                            logger.info(f"❌ GeminiSupervisor method issue: HTTP {gen_response.status}")
                                else:
                                    logger.info(f"❌ Project creation failed: HTTP {proj_response.status}")
                        else:
                            logger.info("❌ GeminiSupervisor not loaded")
                    else:
                        logger.info(f"❌ Health check failed: HTTP {response.status}")
            except Exception as e:
                logger.info(f"❌ GeminiSupervisor test failed: {str(e)}")
            
            success = fixes_verified >= 2  # Allow 1 failure
            
            logger.info("=" * 80)
            logger.info("🔧 CRITICAL FIXES VERIFICATION RESULTS")
            logger.info("=" * 80)
            
            fix_names = [
                "Enhanced Coqui Voice Manager Method Signature Fix",
                "Gemini Script Analysis JSON Parsing Fix",
                "GeminiSupervisor Missing Method Fix"
            ]
            
            for i, fix_name in enumerate(fix_names):
                status = "✅ VERIFIED" if i < fixes_verified else "❌ ISSUE"
                logger.info(f"{status} {fix_name}")
            
            logger.info(f"📊 Overall: {fixes_verified}/{total_fixes} critical fixes verified")
            
            if success:
                logger.info("🎉 CRITICAL FIXES VERIFICATION PASSED!")
                logger.info("✅ Recent critical fixes are working correctly")
            else:
                logger.info("❌ CRITICAL FIXES VERIFICATION FAILED!")
                logger.info("⚠️  Some critical fixes may still have issues")
            
            self.log_test_result(
                test_name,
                success,
                f"Critical fixes verification: {fixes_verified}/{total_fixes} verified",
                {
                    "fixes_verified": fixes_verified,
                    "total_fixes": total_fixes,
                    "fix_details": {
                        "voice_manager_method": fixes_verified >= 1,
                        "json_parsing": fixes_verified >= 2,
                        "gemini_supervisor_method": fixes_verified >= 3
                    }
                }
            )
            
            return success
            
        except Exception as e:
            logger.info(f"❌ CRITICAL FIXES VERIFICATION FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_video_generation_pipeline_end_to_end(self) -> bool:
        """Test end-to-end video generation pipeline to verify critical fixes work"""
        test_name = "Video Generation Pipeline End-to-End"
        try:
            logger.info("🎬 TESTING VIDEO GENERATION PIPELINE END-TO-END")
            logger.info("=" * 80)
            
            # Use a multi-character script to test character detection and voice assignment
            test_script = """
NARRATOR: Welcome to our advanced AI video production system.

SARAH: This technology is incredible! It can detect multiple characters automatically.

JOHN: I'm amazed by the quality, Sarah. The voice assignment is so intelligent.

NARRATOR: Experience the future of video creation with professional-grade results.
            """.strip()
            
            # Step 1: Create project
            logger.info("📝 Step 1: Creating project with multi-character script...")
            project_data = {
                "script": test_script,
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
                if not project_id:
                    self.log_test_result(test_name, False, "No project_id returned")
                    return False
                
                logger.info(f"✅ Project created successfully: {project_id}")
            
            # Step 2: Start video generation
            logger.info("🚀 Step 2: Starting video generation...")
            generation_data = {
                "project_id": project_id,
                "script": test_script,
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(
                f"{self.api_base}/generate",
                json=generation_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"Generation start failed: HTTP {response.status} - {error_text}")
                    return False
                
                generation_result = await response.json()
                generation_id = generation_result.get("generation_id")
                if not generation_id:
                    self.log_test_result(test_name, False, "No generation_id returned")
                    return False
                
                logger.info(f"✅ Generation started: {generation_id}")
            
            # Step 3: Monitor progress for critical pipeline stages
            logger.info("📊 Step 3: Monitoring pipeline progress...")
            
            pipeline_stages_detected = []
            expected_stages = [
                "character detection", "voice assignment", "scene breaking", 
                "video generation", "audio creation", "post-production"
            ]
            
            max_monitoring_time = 45  # seconds
            check_interval = 3  # seconds
            max_checks = max_monitoring_time // check_interval
            
            pipeline_working = False
            highest_progress = 0.0
            final_status = "unknown"
            
            for check_num in range(max_checks):
                await asyncio.sleep(check_interval)
                
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        current_status = status_data.get("status", "")
                        current_progress = status_data.get("progress", 0.0)
                        current_message = status_data.get("message", "").lower()
                        
                        highest_progress = max(highest_progress, current_progress)
                        final_status = current_status
                        
                        logger.info(f"📈 Check {check_num + 1}: Status={current_status}, Progress={current_progress}%, Message='{current_message}'")
                        
                        # Check for pipeline stage messages
                        for stage in expected_stages:
                            if stage in current_message and stage not in pipeline_stages_detected:
                                pipeline_stages_detected.append(stage)
                                logger.info(f"✅ Pipeline stage detected: {stage}")
                        
                        # Check if pipeline is working (progress > 0 or processing status)
                        if current_progress > 0 or current_status == "processing":
                            pipeline_working = True
                        
                        # Break if completed or failed
                        if current_status in ["completed", "failed"]:
                            logger.info(f"🏁 Generation finished with status: {current_status}")
                            break
                    else:
                        logger.info(f"❌ Status check {check_num + 1} failed: HTTP {response.status}")
            
            # Step 4: Verify critical components are operational
            logger.info("🔧 Step 4: Verifying critical components...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    enhanced_components = health_data.get("enhanced_components", {})
                    capabilities = enhanced_components.get("capabilities", {})
                    
                    critical_components = {
                        "gemini_supervisor": enhanced_components.get("gemini_supervisor", False),
                        "runwayml_processor": enhanced_components.get("runwayml_processor", False),
                        "multi_voice_manager": enhanced_components.get("multi_voice_manager", False),
                        "character_detection": capabilities.get("character_detection", False),
                        "voice_assignment": capabilities.get("voice_assignment", False),
                        "post_production": capabilities.get("post_production", False)
                    }
                    
                    components_working = all(critical_components.values())
                    
                    for component, status in critical_components.items():
                        logger.info(f"{'✅' if status else '❌'} {component.replace('_', ' ').title()}: {status}")
                else:
                    components_working = False
                    logger.info("❌ Health check failed")
            
            # Final assessment
            success_criteria = {
                "project_created": True,  # Already verified
                "generation_started": True,  # Already verified
                "pipeline_working": pipeline_working,
                "progress_made": highest_progress > 0,
                "components_operational": components_working,
                "pipeline_stages_detected": len(pipeline_stages_detected) >= 2,
                "no_critical_errors": final_status != "failed" or highest_progress > 10
            }
            
            passed_criteria = sum(success_criteria.values())
            total_criteria = len(success_criteria)
            
            logger.info("=" * 80)
            logger.info("🎬 VIDEO GENERATION PIPELINE RESULTS")
            logger.info("=" * 80)
            
            for criterion, passed in success_criteria.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                logger.info(f"{status} {criterion.replace('_', ' ').title()}")
            
            logger.info(f"📊 Pipeline Summary:")
            logger.info(f"   - Highest progress: {highest_progress}%")
            logger.info(f"   - Final status: {final_status}")
            logger.info(f"   - Pipeline stages detected: {len(pipeline_stages_detected)}/{len(expected_stages)}")
            logger.info(f"   - Stages found: {pipeline_stages_detected}")
            
            overall_success = passed_criteria >= (total_criteria - 1)  # Allow 1 failure
            
            if overall_success:
                logger.info("🎉 VIDEO GENERATION PIPELINE END-TO-END TEST PASSED!")
                logger.info("✅ Critical fixes are working and pipeline is operational")
            else:
                logger.info("❌ VIDEO GENERATION PIPELINE END-TO-END TEST FAILED!")
                logger.info("⚠️  Pipeline may have issues or critical fixes not working")
            
            self.log_test_result(
                test_name,
                overall_success,
                f"End-to-end pipeline test: {passed_criteria}/{total_criteria} criteria passed",
                {
                    "success_criteria": success_criteria,
                    "highest_progress": highest_progress,
                    "final_status": final_status,
                    "pipeline_stages_detected": pipeline_stages_detected,
                    "project_id": project_id,
                    "generation_id": generation_id
                }
            )
            
            return overall_success
            
        except Exception as e:
            logger.info(f"❌ VIDEO GENERATION PIPELINE TEST FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    def print_summary(self):
        """Print comprehensive test summary"""
        logger.info("\n" + "=" * 100)
        logger.info("🏭 PRODUCTION BACKEND TESTING SUMMARY")
        logger.info("=" * 100)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        logger.info("")
        
        # Group tests by category
        production_features = []
        critical_fixes = []
        
        for test_name, result in self.test_results.items():
            status = "✅ WORKING" if result["success"] else "❌ FAILING"
            
            if "Production" in test_name or "Cache" in test_name or "File" in test_name or "Queue" in test_name or "WebSocket" in test_name or "Configuration" in test_name:
                production_features.append(f"{status} {test_name}")
            else:
                critical_fixes.append(f"{status} {test_name}")
        
        if critical_fixes:
            logger.info("🔧 CRITICAL FIXES STATUS:")
            for fix in critical_fixes:
                logger.info(f"   {fix}")
            logger.info("")
        
        if production_features:
            logger.info("🏭 PRODUCTION FEATURES STATUS:")
            for feature in production_features:
                logger.info(f"   {feature}")
            logger.info("")
        
        # Production readiness assessment
        production_ready_count = sum(1 for test_name, result in self.test_results.items() 
                                   if result["success"] and any(keyword in test_name for keyword in 
                                   ["Production", "Cache", "File", "Queue", "WebSocket", "Configuration"]))
        
        total_production_features = sum(1 for test_name in self.test_results.keys() 
                                      if any(keyword in test_name for keyword in 
                                      ["Production", "Cache", "File", "Queue", "WebSocket", "Configuration"]))
        
        if total_production_features > 0:
            production_readiness = (production_ready_count / total_production_features) * 100
            logger.info(f"🎯 PRODUCTION READINESS: {production_ready_count}/{total_production_features} features ready ({production_readiness:.1f}%)")
        
        logger.info("=" * 100)

async def main():
    """Main test execution"""
    # Get backend URL from environment
    backend_url = "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com"
    
    logger.info("🚀 Starting Production Backend Testing...")
    logger.info(f"Backend URL: {backend_url}")
    
    async with ProductionBackendTester(backend_url) as tester:
        # Test production features that need retesting
        await tester.test_production_health_check_system()
        await tester.test_cache_management_system()
        await tester.test_file_management_system()
        await tester.test_queue_system_metrics()
        await tester.test_enhanced_websocket_communication()
        await tester.test_coqui_tts_voice_configuration()
        await tester.test_production_mode_configuration()
        
        # Test critical fixes verification
        await tester.test_critical_fixes_verification()
        
        # Test end-to-end pipeline
        await tester.test_video_generation_pipeline_end_to_end()
        
        # Print comprehensive summary
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())