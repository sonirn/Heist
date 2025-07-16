#!/usr/bin/env python3
"""
Focused Backend Testing for Production Issues
Tests the 9 specific issues identified in the review request
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

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
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: dict = None):
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
        """Test 1: Production Health Check System (missing cache/queue/storage metrics)"""
        test_name = "Production Health Check System"
        try:
            logger.info("🏥 Testing Production Health Check System...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for production-specific fields that were missing
                    required_production_fields = [
                        "cache", "queue", "storage"
                    ]
                    
                    missing_fields = [field for field in required_production_fields if field not in data]
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing production fields: {missing_fields}", data)
                        return False
                    
                    # Check cache metrics
                    cache = data.get("cache", {})
                    if "hit_rate" not in cache:
                        self.log_test_result(test_name, False, "Cache metrics missing hit_rate", data)
                        return False
                    
                    # Check queue metrics
                    queue = data.get("queue", {})
                    if "active_tasks" not in queue:
                        self.log_test_result(test_name, False, "Queue metrics missing active_tasks", data)
                        return False
                    
                    # Check storage metrics
                    storage = data.get("storage", {})
                    if "total_files" not in storage:
                        self.log_test_result(test_name, False, "Storage metrics missing total_files", data)
                        return False
                    
                    self.log_test_result(test_name, True, "All production metrics present", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_enhanced_health_check_version(self) -> bool:
        """Test 2: Enhanced Health Check (version mismatch: 2.0-production vs 2.0-enhanced)"""
        test_name = "Enhanced Health Check Version"
        try:
            logger.info("🔍 Testing Enhanced Health Check Version...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    version = data.get("version", "")
                    expected_version = "2.0-enhanced"  # Based on test_result.md
                    
                    if version != expected_version:
                        self.log_test_result(test_name, False, f"Version mismatch: expected '{expected_version}', got '{version}'", data)
                        return False
                    
                    self.log_test_result(test_name, True, f"Version correct: {version}", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_production_database_integration(self) -> bool:
        """Test 3: Production Database Integration (missing database fields)"""
        test_name = "Production Database Integration"
        try:
            logger.info("🗄️ Testing Production Database Integration...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    database = data.get("database", {})
                    if not database:
                        self.log_test_result(test_name, False, "Database section missing from health check", data)
                        return False
                    
                    # Check for production database fields
                    required_db_fields = ["connected", "collections"]
                    missing_fields = [field for field in required_db_fields if field not in database]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing database fields: {missing_fields}", data)
                        return False
                    
                    if not database.get("connected", False):
                        self.log_test_result(test_name, False, "Database not connected", data)
                        return False
                    
                    self.log_test_result(test_name, True, "Database integration working", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_cache_management_system(self) -> bool:
        """Test 4: Cache Management System (missing cache fields)"""
        test_name = "Cache Management System"
        try:
            logger.info("🗂️ Testing Cache Management System...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    cache = data.get("cache", {})
                    if not cache:
                        self.log_test_result(test_name, False, "Cache section missing from health check", data)
                        return False
                    
                    # Check for cache fields
                    required_cache_fields = ["hit_rate", "total_requests", "cache_size"]
                    missing_fields = [field for field in required_cache_fields if field not in cache]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing cache fields: {missing_fields}", data)
                        return False
                    
                    self.log_test_result(test_name, True, "Cache management working", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_file_management_system(self) -> bool:
        """Test 5: File Management System (missing storage fields)"""
        test_name = "File Management System"
        try:
            logger.info("📁 Testing File Management System...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    storage = data.get("storage", {})
                    if not storage:
                        self.log_test_result(test_name, False, "Storage section missing from health check", data)
                        return False
                    
                    # Check for storage fields
                    required_storage_fields = ["total_files", "total_size", "cleanup_enabled"]
                    missing_fields = [field for field in required_storage_fields if field not in storage]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing storage fields: {missing_fields}", data)
                        return False
                    
                    self.log_test_result(test_name, True, "File management working", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_queue_based_video_generation(self) -> bool:
        """Test 6: Queue-Based Video Generation System (missing queue metrics)"""
        test_name = "Queue-Based Video Generation System"
        try:
            logger.info("🔄 Testing Queue-Based Video Generation System...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    queue = data.get("queue", {})
                    if not queue:
                        self.log_test_result(test_name, False, "Queue section missing from health check", data)
                        return False
                    
                    # Check for queue fields
                    required_queue_fields = ["active_tasks", "completed_tasks", "failed_tasks"]
                    missing_fields = [field for field in required_queue_fields if field not in queue]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing queue fields: {missing_fields}", data)
                        return False
                    
                    self.log_test_result(test_name, True, "Queue system working", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_enhanced_websocket_communication(self) -> bool:
        """Test 7: Enhanced WebSocket Communication (HTTP 404 error)"""
        test_name = "Enhanced WebSocket Communication"
        try:
            logger.info("🔌 Testing Enhanced WebSocket Communication...")
            
            # First create a test generation to get a valid ID
            project_data = {
                "script": "Test WebSocket communication",
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
                    
                    if project_id:
                        generation_data = {
                            "project_id": project_id,
                            "script": "Test WebSocket communication",
                            "aspect_ratio": "16:9"
                        }
                        
                        async with self.session.post(
                            f"{self.api_base}/generate",
                            json=generation_data,
                            headers={"Content-Type": "application/json"}
                        ) as gen_response:
                            if gen_response.status == 200:
                                gen_result = await gen_response.json()
                                generation_id = gen_result.get("generation_id")
                                
                                if generation_id:
                                    # Test WebSocket endpoint
                                    ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
                                    ws_endpoint = f"{ws_url}/api/ws/{generation_id}"
                                    
                                    try:
                                        import websockets
                                        websocket = await asyncio.wait_for(
                                            websockets.connect(ws_endpoint), 
                                            timeout=5.0
                                        )
                                        await websocket.close()
                                        self.log_test_result(test_name, True, "WebSocket connection successful")
                                        return True
                                    except Exception as ws_e:
                                        if "404" in str(ws_e):
                                            self.log_test_result(test_name, False, f"WebSocket HTTP 404 error: {ws_e}")
                                        else:
                                            self.log_test_result(test_name, False, f"WebSocket error: {ws_e}")
                                        return False
                                else:
                                    self.log_test_result(test_name, False, "No generation_id for WebSocket test")
                                    return False
                            else:
                                self.log_test_result(test_name, False, f"Generation failed: HTTP {gen_response.status}")
                                return False
                    else:
                        self.log_test_result(test_name, False, "No project_id for WebSocket test")
                        return False
                else:
                    self.log_test_result(test_name, False, f"Project creation failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_coqui_tts_voices(self) -> bool:
        """Test 8: Coqui TTS Voices (no Coqui-specific voices found)"""
        test_name = "Coqui TTS Voices"
        try:
            logger.info("🎤 Testing Coqui TTS Voices...")
            
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Check for Coqui-specific voices
                        coqui_voices = [v for v in data if v.get("voice_id", "").startswith("coqui_")]
                        
                        if len(coqui_voices) == 0:
                            self.log_test_result(test_name, False, "No Coqui-specific voices found", {"total_voices": len(data), "sample": data[0] if data else None})
                            return False
                        
                        # Check for Hindi voices specifically
                        hindi_voices = [v for v in data if "hindi" in v.get("name", "").lower()]
                        
                        if len(hindi_voices) == 0:
                            self.log_test_result(test_name, False, "No Hindi voices found", {"coqui_voices": len(coqui_voices), "total_voices": len(data)})
                            return False
                        
                        self.log_test_result(test_name, True, f"Found {len(coqui_voices)} Coqui voices, {len(hindi_voices)} Hindi voices", {
                            "coqui_voices": len(coqui_voices),
                            "hindi_voices": len(hindi_voices),
                            "total_voices": len(data)
                        })
                        return True
                    else:
                        self.log_test_result(test_name, False, "No voices available", data)
                        return False
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_fallback_mechanisms(self) -> bool:
        """Test 9: Fallback Mechanisms (AI models not in development mode)"""
        test_name = "Fallback Mechanisms"
        try:
            logger.info("🔄 Testing Fallback Mechanisms...")
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    ai_models = data.get("ai_models", {})
                    if not ai_models:
                        self.log_test_result(test_name, False, "AI models section missing", data)
                        return False
                    
                    # Check if models are properly loaded (not in development mode)
                    minimax_loaded = ai_models.get("minimax", False)
                    stable_audio_loaded = ai_models.get("stable_audio", False)
                    
                    if not minimax_loaded:
                        self.log_test_result(test_name, False, "Minimax model not loaded", ai_models)
                        return False
                    
                    if not stable_audio_loaded:
                        self.log_test_result(test_name, False, "Stable Audio model not loaded", ai_models)
                        return False
                    
                    # Check environment to see if we're in development mode
                    environment = data.get("environment", "")
                    if environment == "development":
                        self.log_test_result(test_name, False, "System running in development mode", {"environment": environment, "ai_models": ai_models})
                        return False
                    
                    self.log_test_result(test_name, True, "AI models loaded in production mode", ai_models)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

async def run_focused_tests():
    """Run focused tests for the 9 specific production issues"""
    
    backend_url = "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com"
    
    logger.info("🎯 STARTING FOCUSED PRODUCTION ISSUE TESTING")
    logger.info("=" * 80)
    logger.info(f"Backend URL: {backend_url}")
    logger.info("Testing the 9 specific issues from the review request:")
    logger.info("1. Production Health Check System (missing cache/queue/storage metrics)")
    logger.info("2. Enhanced Health Check (version mismatch: 2.0-production vs 2.0-enhanced)")
    logger.info("3. Production Database Integration (missing database fields)")
    logger.info("4. Cache Management System (missing cache fields)")
    logger.info("5. File Management System (missing storage fields)")
    logger.info("6. Queue-Based Video Generation System (missing queue metrics)")
    logger.info("7. Enhanced WebSocket Communication (HTTP 404 error)")
    logger.info("8. Coqui TTS Voices (no Coqui-specific voices found)")
    logger.info("9. Fallback Mechanisms (AI models not in development mode)")
    logger.info("=" * 80)
    
    async with FocusedBackendTester(backend_url) as tester:
        test_results = []
        
        # Run the 9 specific tests
        tests = [
            ("Production Health Check System", tester.test_production_health_check_system),
            ("Enhanced Health Check Version", tester.test_enhanced_health_check_version),
            ("Production Database Integration", tester.test_production_database_integration),
            ("Cache Management System", tester.test_cache_management_system),
            ("File Management System", tester.test_file_management_system),
            ("Queue-Based Video Generation System", tester.test_queue_based_video_generation),
            ("Enhanced WebSocket Communication", tester.test_enhanced_websocket_communication),
            ("Coqui TTS Voices", tester.test_coqui_tts_voices),
            ("Fallback Mechanisms", tester.test_fallback_mechanisms)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running: {test_name}")
            result = await test_func()
            test_results.append((test_name, result))
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("🏁 FOCUSED PRODUCTION ISSUE TESTING COMPLETED")
        logger.info("=" * 80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        logger.info(f"📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        logger.info("")
        
        # Detailed results
        logger.info("📋 DETAILED TEST RESULTS:")
        logger.info("-" * 80)
        
        for test_name, result in test_results:
            status = "✅ WORKING" if result else "❌ ISSUE FOUND"
            logger.info(f"{status} {test_name}")
        
        logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL PRODUCTION ISSUES RESOLVED!")
            logger.info("✅ System is ready for 100% backend functionality")
        else:
            logger.info("⚠️ PRODUCTION ISSUES STILL EXIST")
            logger.info(f"❌ {total_tests - passed_tests} issues need to be fixed for 100% functionality")
        
        logger.info("=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate,
            "test_results": test_results,
            "all_issues_resolved": passed_tests == total_tests
        }

if __name__ == "__main__":
    import sys
    results = asyncio.run(run_focused_tests())
    sys.exit(0 if results["all_issues_resolved"] else 1)