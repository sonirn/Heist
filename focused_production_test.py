#!/usr/bin/env python3
"""
Focused Backend Testing for Production-Level Features
Testing specific issues identified in test_result.md
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
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
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
        """Test Production Health Check System Enhancement - missing cache/queue/storage metrics"""
        test_name = "Production Health Check System Enhancement"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for production-level metrics
                    cache_section = data.get("cache", {})
                    queue_section = data.get("queue", {})
                    storage_section = data.get("storage", {})
                    
                    missing_metrics = []
                    
                    # Check cache metrics
                    if "hit_rate" not in cache_section:
                        missing_metrics.append("cache.hit_rate")
                    if "total_requests" not in cache_section:
                        missing_metrics.append("cache.total_requests")
                    if "cache_size" not in cache_section:
                        missing_metrics.append("cache.cache_size")
                    
                    # Check queue metrics
                    if "completed_tasks" not in queue_section:
                        missing_metrics.append("queue.completed_tasks")
                    if "failed_tasks" not in queue_section:
                        missing_metrics.append("queue.failed_tasks")
                    
                    # Check storage metrics
                    if "total_files" not in storage_section:
                        missing_metrics.append("storage.total_files")
                    if "total_size" not in storage_section:
                        missing_metrics.append("storage.total_size")
                    if "cleanup_enabled" not in storage_section:
                        missing_metrics.append("storage.cleanup_enabled")
                    
                    if missing_metrics:
                        self.log_test_result(test_name, False, f"Missing production metrics: {missing_metrics}", {
                            "missing_metrics": missing_metrics,
                            "cache_section": cache_section,
                            "queue_section": queue_section,
                            "storage_section": storage_section
                        })
                        return False
                    
                    self.log_test_result(test_name, True, "All production health check metrics present", data)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_cache_management_system(self) -> bool:
        """Test Cache Management System Implementation - missing cache fields"""
        test_name = "Cache Management System Implementation"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    cache_section = data.get("cache", {})
                    
                    required_fields = ["hit_rate", "total_requests", "cache_size"]
                    missing_fields = [field for field in required_fields if field not in cache_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing cache fields: {missing_fields}", {
                            "missing_fields": missing_fields,
                            "cache_section": cache_section
                        })
                        return False
                    
                    self.log_test_result(test_name, True, "Cache management system properly implemented", cache_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_file_management_system(self) -> bool:
        """Test File Management System Implementation - missing storage fields"""
        test_name = "File Management System Implementation"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    storage_section = data.get("storage", {})
                    
                    required_fields = ["total_files", "total_size", "cleanup_enabled"]
                    missing_fields = [field for field in required_fields if field not in storage_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing storage fields: {missing_fields}", {
                            "missing_fields": missing_fields,
                            "storage_section": storage_section
                        })
                        return False
                    
                    self.log_test_result(test_name, True, "File management system properly implemented", storage_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_queue_system_metrics(self) -> bool:
        """Test Queue System Metrics Enhancement - missing queue metrics"""
        test_name = "Queue System Metrics Enhancement"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    queue_section = data.get("queue", {})
                    
                    required_fields = ["completed_tasks", "failed_tasks"]
                    missing_fields = [field for field in required_fields if field not in queue_section]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing queue fields: {missing_fields}", {
                            "missing_fields": missing_fields,
                            "queue_section": queue_section
                        })
                        return False
                    
                    self.log_test_result(test_name, True, "Queue system metrics properly implemented", queue_section)
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_websocket_communication(self) -> bool:
        """Test Enhanced WebSocket Communication - WebSocket connection errors"""
        test_name = "Enhanced WebSocket Communication"
        try:
            # Test WebSocket endpoint availability
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            test_generation_id = "test123"
            ws_endpoint = f"{ws_url}/api/ws/{test_generation_id}"
            
            # Try to connect to WebSocket endpoint (just test if it's available)
            try:
                async with self.session.head(f"{self.api_base}/ws/{test_generation_id}") as response:
                    # WebSocket endpoints typically return 404 for HEAD requests, but should not return 500
                    if response.status == 404:
                        self.log_test_result(test_name, False, "WebSocket endpoint not found (HTTP 404)", {
                            "status": response.status,
                            "endpoint": f"/api/ws/{test_generation_id}"
                        })
                        return False
                    elif response.status < 500:
                        self.log_test_result(test_name, True, "WebSocket endpoint accessible", {
                            "status": response.status,
                            "endpoint": f"/api/ws/{test_generation_id}"
                        })
                        return True
                    else:
                        self.log_test_result(test_name, False, f"WebSocket endpoint error: HTTP {response.status}", {
                            "status": response.status
                        })
                        return False
            except Exception as ws_e:
                self.log_test_result(test_name, False, f"WebSocket connection error: {ws_e}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_coqui_tts_voice_configuration(self) -> bool:
        """Test Coqui TTS Voice Configuration - Coqui voices not configured"""
        test_name = "Coqui TTS Voice Configuration"
        try:
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not isinstance(data, list):
                        self.log_test_result(test_name, False, "Voices endpoint returned invalid format", data)
                        return False
                    
                    if len(data) == 0:
                        self.log_test_result(test_name, False, "No voices available", {"count": 0})
                        return False
                    
                    # Check for Coqui-specific voices
                    coqui_voices = [v for v in data if v.get("voice_id", "").startswith("coqui_")]
                    
                    if len(coqui_voices) == 0:
                        self.log_test_result(test_name, False, "No Coqui-specific voices found (no coqui_ prefixed voice_ids)", {
                            "total_voices": len(data),
                            "coqui_voices": len(coqui_voices),
                            "sample_voices": [v.get("voice_id", "") for v in data[:5]]
                        })
                        return False
                    
                    self.log_test_result(test_name, True, f"Coqui TTS voices properly configured with {len(coqui_voices)} Coqui voices", {
                        "total_voices": len(data),
                        "coqui_voices": len(coqui_voices),
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
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    environment = data.get("environment", "")
                    
                    if environment != "production":
                        self.log_test_result(test_name, False, f"System running in {environment} mode instead of production", {
                            "current_environment": environment,
                            "expected_environment": "production"
                        })
                        return False
                    
                    self.log_test_result(test_name, True, "System properly configured for production mode", {
                        "environment": environment
                    })
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def run_focused_tests(self):
        """Run focused tests on production-level features"""
        logger.info("🎯 STARTING FOCUSED BACKEND TESTING - PRODUCTION FEATURES")
        logger.info("=" * 80)
        
        tests = [
            ("Production Health Check System Enhancement", self.test_production_health_check_system),
            ("Cache Management System Implementation", self.test_cache_management_system),
            ("File Management System Implementation", self.test_file_management_system),
            ("Queue System Metrics Enhancement", self.test_queue_system_metrics),
            ("Enhanced WebSocket Communication", self.test_websocket_communication),
            ("Coqui TTS Voice Configuration", self.test_coqui_tts_voice_configuration),
            ("Production Mode Configuration", self.test_production_mode_configuration),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n🧪 Running: {test_name}")
            logger.info("-" * 60)
            
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.info(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: EXCEPTION - {str(e)}")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎯 FOCUSED BACKEND TESTING RESULTS")
        logger.info("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        # Detailed results
        logger.info("\n📋 Detailed Test Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"   {status} {test_name}: {result['message']}")
        
        return passed_tests, total_tests, self.test_results

async def main():
    """Main test execution"""
    # Get backend URL from environment
    import os
    backend_url = os.getenv("REACT_APP_BACKEND_URL", "https://ac967fb5-da9e-45e7-b4fa-d8f39d0ce9b3.preview.emergentagent.com")
    
    logger.info(f"🎯 Testing backend at: {backend_url}")
    
    async with FocusedBackendTester(backend_url) as tester:
        passed, total, results = await tester.run_focused_tests()
        
        return {
            "passed": passed,
            "total": total,
            "success_rate": (passed / total) * 100,
            "results": results
        }

if __name__ == "__main__":
    asyncio.run(main())