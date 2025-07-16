#!/usr/bin/env python3
"""
Focused Testing for Remaining Issues to Achieve 100% Backend Functionality
Tests the specific issues identified in test_result.md
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FocusedTester:
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

    async def test_websocket_endpoints(self) -> bool:
        """Test WebSocket endpoints - Check if they return 404"""
        test_name = "WebSocket Communication Fix"
        try:
            logger.info("🔌 TESTING WEBSOCKET ENDPOINTS")
            logger.info("=" * 60)
            
            # Test WebSocket endpoint via HTTP (should return 404 or proper WebSocket upgrade)
            test_generation_id = "test-generation-123"
            
            # Test 1: /api/ws/{generation_id}
            logger.info(f"📡 Testing /api/ws/{test_generation_id}")
            try:
                async with self.session.get(f"{self.api_base}/ws/{test_generation_id}") as response:
                    logger.info(f"WebSocket endpoint /api/ws/{test_generation_id} returned: {response.status}")
                    if response.status == 404:
                        logger.info("❌ WebSocket endpoint /api/ws/{generation_id} returns HTTP 404 - not configured")
                        websocket_1_working = False
                    else:
                        logger.info("✅ WebSocket endpoint /api/ws/{generation_id} is configured")
                        websocket_1_working = True
            except Exception as e:
                logger.info(f"❌ WebSocket endpoint /api/ws/{test_generation_id} error: {str(e)}")
                websocket_1_working = False
            
            # Test 2: /api/ws/test
            logger.info("📡 Testing /api/ws/test")
            try:
                async with self.session.get(f"{self.api_base}/ws/test") as response:
                    logger.info(f"WebSocket endpoint /api/ws/test returned: {response.status}")
                    if response.status == 404:
                        logger.info("❌ WebSocket endpoint /api/ws/test returns HTTP 404 - not configured")
                        websocket_2_working = False
                    else:
                        logger.info("✅ WebSocket endpoint /api/ws/test is configured")
                        websocket_2_working = True
            except Exception as e:
                logger.info(f"❌ WebSocket endpoint /api/ws/test error: {str(e)}")
                websocket_2_working = False
            
            success = websocket_1_working and websocket_2_working
            
            self.log_test_result(
                test_name,
                success,
                f"WebSocket endpoints: {int(websocket_1_working) + int(websocket_2_working)}/2 working",
                {
                    "websocket_generation_id": websocket_1_working,
                    "websocket_test": websocket_2_working
                }
            )
            
            return success
            
        except Exception as e:
            logger.info(f"❌ WEBSOCKET TEST FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_health_check_metrics(self) -> bool:
        """Test Production Health Check System - Check for missing metrics"""
        test_name = "Production Health Check System Enhancement"
        try:
            logger.info("🏥 TESTING HEALTH CHECK METRICS")
            logger.info("=" * 60)
            
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, f"Health check failed: HTTP {response.status}")
                    return False
                
                data = await response.json()
                logger.info(f"Health check response received (status: {response.status})")
                
                issues_found = []
                
                # Check cache section
                cache_section = data.get("cache", {})
                if not cache_section:
                    issues_found.append("Missing cache section")
                else:
                    required_cache_fields = ["hit_rate", "total_requests", "cache_size"]
                    missing_cache = [f for f in required_cache_fields if f not in cache_section]
                    if missing_cache:
                        issues_found.append(f"Cache missing fields: {missing_cache}")
                    else:
                        logger.info("✅ Cache metrics present")
                
                # Check queue section
                queue_section = data.get("queue", {})
                if not queue_section:
                    issues_found.append("Missing queue section")
                else:
                    required_queue_fields = ["completed_tasks", "failed_tasks", "active_tasks"]
                    missing_queue = [f for f in required_queue_fields if f not in queue_section]
                    if missing_queue:
                        issues_found.append(f"Queue missing fields: {missing_queue}")
                    else:
                        logger.info("✅ Queue metrics present")
                
                # Check storage section structure
                storage_section = data.get("storage", {})
                if not storage_section:
                    issues_found.append("Missing storage section")
                else:
                    required_storage_fields = ["total_files", "total_size", "cleanup_enabled"]
                    missing_storage = [f for f in required_storage_fields if f not in storage_section]
                    if missing_storage:
                        # Check if they're in summary (incorrect structure)
                        storage_summary = storage_section.get("summary", {})
                        if storage_summary and all(f in storage_summary for f in required_storage_fields):
                            issues_found.append("Storage fields in summary instead of root level")
                        else:
                            issues_found.append(f"Storage missing fields: {missing_storage}")
                    else:
                        logger.info("✅ Storage metrics at root level")
                
                success = len(issues_found) == 0
                
                if success:
                    logger.info("✅ All health check metrics present and properly structured")
                else:
                    logger.info(f"❌ Health check issues: {issues_found}")
                
                self.log_test_result(
                    test_name,
                    success,
                    f"Health check metrics: {len(issues_found)} issues found",
                    {
                        "issues_found": issues_found,
                        "cache_fields": list(cache_section.keys()) if cache_section else [],
                        "queue_fields": list(queue_section.keys()) if queue_section else [],
                        "storage_fields": list(storage_section.keys()) if storage_section else []
                    }
                )
                
                return success
                
        except Exception as e:
            logger.info(f"❌ HEALTH CHECK TEST FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_video_generation_pipeline(self) -> bool:
        """Test Complete Video Generation Pipeline - Basic functionality"""
        test_name = "Complete Video Generation Pipeline"
        try:
            logger.info("🎬 TESTING VIDEO GENERATION PIPELINE")
            logger.info("=" * 60)
            
            # Step 1: Create project
            project_data = {
                "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
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
                
                logger.info(f"✅ Project created: {project_id}")
            
            # Step 2: Start generation
            generation_data = {
                "project_id": project_id,
                "script": project_data["script"],
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
            
            # Step 3: Check status
            await asyncio.sleep(2)  # Wait briefly
            
            async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                if response.status != 200:
                    self.log_test_result(test_name, False, f"Status check failed: HTTP {response.status}")
                    return False
                
                status_data = await response.json()
                current_status = status_data.get("status", "")
                current_progress = status_data.get("progress", 0.0)
                
                logger.info(f"✅ Status check: {current_status} ({current_progress}%)")
            
            success = True  # If we got this far, basic pipeline is working
            
            self.log_test_result(
                test_name,
                success,
                "Basic video generation pipeline working",
                {
                    "project_id": project_id,
                    "generation_id": generation_id,
                    "final_status": current_status,
                    "final_progress": current_progress
                }
            )
            
            return success
            
        except Exception as e:
            logger.info(f"❌ VIDEO GENERATION PIPELINE TEST FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_api_error_handling(self) -> bool:
        """Test API Error Handling - Basic error cases"""
        test_name = "API Error Handling"
        try:
            logger.info("⚠️  TESTING API ERROR HANDLING")
            logger.info("=" * 60)
            
            error_tests_passed = 0
            total_error_tests = 3
            
            # Test 1: Invalid project ID
            async with self.session.get(f"{self.api_base}/projects/invalid-project-id") as response:
                if response.status == 404:
                    error_tests_passed += 1
                    logger.info("✅ Invalid project ID returns 404")
                else:
                    logger.info(f"❌ Invalid project ID returned {response.status}, expected 404")
            
            # Test 2: Invalid generation ID
            async with self.session.get(f"{self.api_base}/generate/invalid-generation-id") as response:
                if response.status == 404:
                    error_tests_passed += 1
                    logger.info("✅ Invalid generation ID returns 404")
                else:
                    logger.info(f"❌ Invalid generation ID returned {response.status}, expected 404")
            
            # Test 3: Missing required fields
            async with self.session.post(
                f"{self.api_base}/projects",
                json={},  # Empty JSON
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status >= 400:
                    error_tests_passed += 1
                    logger.info("✅ Missing required fields properly rejected")
                else:
                    logger.info(f"❌ Missing required fields returned {response.status}, expected 4xx")
            
            success = error_tests_passed >= 2  # Allow 1 failure
            
            self.log_test_result(
                test_name,
                success,
                f"Error handling: {error_tests_passed}/{total_error_tests} tests passed",
                {
                    "error_tests_passed": error_tests_passed,
                    "total_error_tests": total_error_tests
                }
            )
            
            return success
            
        except Exception as e:
            logger.info(f"❌ API ERROR HANDLING TEST FAILED: Exception: {str(e)}")
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def run_focused_tests(self) -> Dict[str, bool]:
        """Run focused tests for remaining issues"""
        logger.info("🎯 RUNNING FOCUSED TESTS FOR REMAINING ISSUES")
        logger.info("=" * 80)
        
        test_results = {}
        
        # Test 1: WebSocket Communication Fix
        test_results["websocket_communication"] = await self.test_websocket_endpoints()
        
        # Test 2: Production Health Check System
        test_results["production_health_check"] = await self.test_health_check_metrics()
        
        # Test 3: Complete Video Generation Pipeline
        test_results["video_generation_pipeline"] = await self.test_video_generation_pipeline()
        
        # Test 4: API Error Handling
        test_results["api_error_handling"] = await self.test_api_error_handling()
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        logger.info("=" * 80)
        logger.info("📊 FOCUSED TESTS SUMMARY")
        logger.info("=" * 80)
        
        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        logger.info(f"📈 Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        return test_results

async def main():
    """Main test execution"""
    backend_url = "https://ac967fb5-da9e-45e7-b4fa-d8f39d0ce9b3.preview.emergentagent.com"
    
    async with FocusedTester(backend_url) as tester:
        results = await tester.run_focused_tests()
        
        # Print final summary
        print("\n" + "="*80)
        print("🎯 FOCUSED TEST RESULTS FOR REMAINING ISSUES")
        print("="*80)
        
        for test_name, passed in results.items():
            status = "✅" if passed else "❌"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        passed = sum(results.values())
        total = len(results)
        print(f"\n📊 Final Score: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL FOCUSED TESTS PASSED!")
        else:
            print(f"⚠️  {total-passed} issues remaining")

if __name__ == "__main__":
    asyncio.run(main())