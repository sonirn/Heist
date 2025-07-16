#!/usr/bin/env python3
"""
Focused Issue Testing - Two Specific Issues for 100% Functionality
Testing the exact two issues identified for achieving 100% backend functionality
"""

import asyncio
import aiohttp
import json
import websockets
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from frontend .env
BACKEND_URL = "https://ac967fb5-da9e-45e7-b4fa-d8f39d0ce9b3.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FocusedIssueTester:
    def __init__(self):
        self.results = {
            "storage_metrics_structure": {"passed": False, "details": ""},
            "websocket_connection": {"passed": False, "details": ""}
        }
    
    async def test_storage_metrics_structure(self):
        """
        Test Issue 1: Storage metrics should be available at storage.total_files, 
        storage.total_size, storage.cleanup_enabled (not nested in storage.summary)
        """
        logger.info("🔍 Testing Issue 1: Storage Metrics Structure in Health Check")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_BASE}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check if storage section exists
                        if "storage" not in data:
                            self.results["storage_metrics_structure"]["details"] = "❌ No 'storage' section found in health check response"
                            return False
                        
                        storage = data["storage"]
                        
                        # Check for required fields at root level of storage
                        required_fields = ["total_files", "total_size", "cleanup_enabled"]
                        missing_fields = []
                        nested_fields = []
                        
                        logger.info(f"📋 Storage section structure: {json.dumps(storage, indent=2)}")
                        
                        for field in required_fields:
                            if field not in storage:
                                missing_fields.append(field)
                            else:
                                logger.info(f"✅ Found {field} at storage.{field}")
                        
                        # Check if fields are incorrectly nested in storage.summary
                        if "summary" in storage:
                            logger.info(f"📋 Found storage.summary section: {json.dumps(storage['summary'], indent=2)}")
                            for field in required_fields:
                                if field in storage["summary"]:
                                    nested_fields.append(field)
                                    logger.info(f"⚠️  Found {field} in storage.summary.{field} (should be at storage.{field})")
                        
                        if missing_fields:
                            self.results["storage_metrics_structure"]["details"] = f"❌ Missing required fields at storage root level: {missing_fields}"
                            return False
                        
                        # Check if fields exist at root level (this is what we want)
                        if not missing_fields:
                            # All required fields are present at root level - this is correct!
                            details = f"✅ All required storage fields found at correct root level: {required_fields}"
                            if nested_fields:
                                details += f" (Note: Fields also exist in storage.summary for backward compatibility)"
                            self.results["storage_metrics_structure"]["details"] = details
                            self.results["storage_metrics_structure"]["passed"] = True
                            return True
                    
                    else:
                        self.results["storage_metrics_structure"]["details"] = f"❌ Health check endpoint returned status {response.status}"
                        return False
                        
        except Exception as e:
            self.results["storage_metrics_structure"]["details"] = f"❌ Error testing storage metrics: {str(e)}"
            return False
    
    async def test_websocket_connection(self):
        """
        Test Issue 2: WebSocket endpoint at /api/ws/{generation_id} should accept connections
        """
        logger.info("🔍 Testing Issue 2: WebSocket Connection at /api/ws/{generation_id}")
        
        test_generation_id = "test-generation-12345"
        websocket_url = f"{BACKEND_URL.replace('https://', 'wss://')}/api/ws/{test_generation_id}"
        
        try:
            # First, let's test if the WebSocket endpoint exists by making an HTTP request
            logger.info("First checking if WebSocket endpoint exists via HTTP...")
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{API_BASE}/ws/{test_generation_id}") as response:
                        logger.info(f"HTTP GET to WebSocket endpoint returned: {response.status}")
                        if response.status == 404:
                            self.results["websocket_connection"]["details"] = "❌ WebSocket endpoint returns HTTP 404 - endpoint not properly configured"
                            return False
                except Exception as http_e:
                    logger.info(f"HTTP test failed (expected): {http_e}")
            
            # Test WebSocket connection
            logger.info(f"Attempting WebSocket connection to: {websocket_url}")
            
            async with websockets.connect(websocket_url) as websocket:
                logger.info("✅ WebSocket connection established successfully")
                
                # Send a test message
                test_message = {"type": "test", "message": "connection test"}
                await websocket.send(json.dumps(test_message))
                logger.info("✅ Test message sent successfully")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"✅ Received response: {response}")
                    self.results["websocket_connection"]["details"] = "✅ WebSocket connection successful, can send/receive messages"
                except asyncio.TimeoutError:
                    logger.info("⚠️ No immediate response received, but connection is working")
                    self.results["websocket_connection"]["details"] = "✅ WebSocket connection successful, can send messages (no immediate response expected)"
                
                self.results["websocket_connection"]["passed"] = True
                return True
                
        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 404:
                self.results["websocket_connection"]["details"] = f"❌ WebSocket endpoint returns HTTP 404 - endpoint not properly configured"
            else:
                self.results["websocket_connection"]["details"] = f"❌ WebSocket connection failed with status {e.status_code}: {str(e)}"
            return False
            
        except websockets.exceptions.ConnectionClosed as e:
            self.results["websocket_connection"]["details"] = f"❌ WebSocket connection closed unexpectedly: {str(e)}"
            return False
            
        except Exception as e:
            self.results["websocket_connection"]["details"] = f"❌ WebSocket connection error: {str(e)}"
            return False
    
    async def run_focused_tests(self):
        """Run the two focused tests for 100% functionality"""
        logger.info("🎯 STARTING FOCUSED ISSUE TESTING FOR 100% FUNCTIONALITY")
        logger.info("=" * 70)
        
        # Test Issue 1: Storage Metrics Structure
        logger.info("\n📋 ISSUE 1: Production Health Check System Enhancement / File Management System")
        issue1_result = await self.test_storage_metrics_structure()
        
        # Test Issue 2: WebSocket Communication
        logger.info("\n📋 ISSUE 2: WebSocket Communication Fix")
        issue2_result = await self.test_websocket_connection()
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("🎯 FOCUSED TESTING RESULTS SUMMARY")
        logger.info("=" * 70)
        
        total_tests = 2
        passed_tests = sum([issue1_result, issue2_result])
        
        logger.info(f"\n📊 OVERALL RESULTS: {passed_tests}/{total_tests} issues resolved ({passed_tests/total_tests*100:.1f}%)")
        
        # Detailed results
        logger.info("\n📋 DETAILED RESULTS:")
        
        logger.info(f"\n1. Storage Metrics Structure: {'✅ RESOLVED' if issue1_result else '❌ NOT RESOLVED'}")
        logger.info(f"   {self.results['storage_metrics_structure']['details']}")
        
        logger.info(f"\n2. WebSocket Communication: {'✅ RESOLVED' if issue2_result else '❌ NOT RESOLVED'}")
        logger.info(f"   {self.results['websocket_connection']['details']}")
        
        # Final assessment
        if passed_tests == total_tests:
            logger.info("\n🎉 SUCCESS: Both critical issues have been resolved!")
            logger.info("✅ System should now be at 100% functionality")
        else:
            logger.info(f"\n⚠️  INCOMPLETE: {total_tests - passed_tests} issue(s) still need to be fixed for 100% functionality")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests/total_tests*100,
            "all_resolved": passed_tests == total_tests,
            "results": self.results
        }

async def main():
    """Main test execution"""
    tester = FocusedIssueTester()
    results = await tester.run_focused_tests()
    return results

if __name__ == "__main__":
    asyncio.run(main())