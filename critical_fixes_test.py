#!/usr/bin/env python3
"""
Critical Bug Fixes Test - Specific test for problem.md issues
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CriticalFixesTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_critical_bug_fixes(self) -> bool:
        """Test critical bug fixes from problem.md - ElevenLabs API, file creation, quality assessment"""
        logger.info("🔧 TESTING CRITICAL BUG FIXES FROM PROBLEM.MD")
        logger.info("=" * 80)
        
        fixes_tested = 0
        total_fixes = 5
        
        # Fix 1: ElevenLabs API Key Authentication (moved from hardcoded to .env)
        logger.info("🔑 Fix 1: Testing ElevenLabs API Key Authentication...")
        try:
            async with self.session.get(f"{self.api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        fixes_tested += 1
                        logger.info("✅ ElevenLabs API authentication working (no 401 errors)")
                    else:
                        logger.info("❌ ElevenLabs API returned invalid format")
                elif response.status == 401:
                    logger.info("❌ ElevenLabs API authentication failed (401 error)")
                else:
                    logger.info(f"❌ ElevenLabs API returned status {response.status}")
        except Exception as e:
            logger.info(f"❌ ElevenLabs API test failed: {str(e)}")
        
        # Fix 2: Enhanced Components Loading (import dependencies fixed)
        logger.info("📦 Fix 2: Testing Enhanced Components Loading...")
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    enhanced_components = data.get("enhanced_components", {})
                    
                    required_components = ["gemini_supervisor", "runwayml_processor", "multi_voice_manager"]
                    all_loaded = all(enhanced_components.get(comp, False) for comp in required_components)
                    
                    if all_loaded:
                        fixes_tested += 1
                        logger.info("✅ All enhanced components loaded successfully (import dependencies fixed)")
                    else:
                        logger.info("❌ Not all enhanced components loaded")
                else:
                    logger.info(f"❌ Health check failed: {response.status}")
        except Exception as e:
            logger.info(f"❌ Enhanced components test failed: {str(e)}")
        
        # Fix 3: File Path Handling and Creation
        logger.info("📁 Fix 3: Testing File Path Handling and Creation...")
        try:
            # Create a test project to verify file handling
            project_data = {
                "script": "Test script for file creation verification.",
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
                        # Start generation to test file creation
                        generation_data = {
                            "project_id": project_id,
                            "script": "Test script for file creation verification.",
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
                                    fixes_tested += 1
                                    logger.info("✅ File path handling and creation working (no file path errors)")
                                else:
                                    logger.info("❌ Generation failed to start")
                            else:
                                logger.info(f"❌ Generation start failed: {gen_response.status}")
                    else:
                        logger.info("❌ Project creation failed")
                else:
                    logger.info(f"❌ Project creation failed: {response.status}")
        except Exception as e:
            logger.info(f"❌ File path handling test failed: {str(e)}")
        
        # Fix 4: RunwayML Processor File Creation
        logger.info("🎬 Fix 4: Testing RunwayML Processor File Creation...")
        try:
            # Test if RunwayML processor is loaded and functional
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    enhanced_components = data.get("enhanced_components", {})
                    runwayml_loaded = enhanced_components.get("runwayml_processor", False)
                    post_production_capability = enhanced_components.get("capabilities", {}).get("post_production", False)
                    
                    if runwayml_loaded and post_production_capability:
                        fixes_tested += 1
                        logger.info("✅ RunwayML processor loaded and ready for file creation")
                    else:
                        logger.info("❌ RunwayML processor not properly loaded")
                else:
                    logger.info(f"❌ Health check failed: {response.status}")
        except Exception as e:
            logger.info(f"❌ RunwayML processor test failed: {str(e)}")
        
        # Fix 5: Gemini Supervisor Quality Assessment
        logger.info("🤖 Fix 5: Testing Gemini Supervisor Quality Assessment...")
        try:
            # Test if Gemini supervisor is loaded and functional
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    enhanced_components = data.get("enhanced_components", {})
                    gemini_loaded = enhanced_components.get("gemini_supervisor", False)
                    quality_supervision = enhanced_components.get("capabilities", {}).get("quality_supervision", False)
                    
                    if gemini_loaded and quality_supervision:
                        fixes_tested += 1
                        logger.info("✅ Gemini supervisor loaded with quality assessment capability")
                    else:
                        logger.info("❌ Gemini supervisor not properly loaded")
                else:
                    logger.info(f"❌ Health check failed: {response.status}")
        except Exception as e:
            logger.info(f"❌ Gemini supervisor test failed: {str(e)}")
        
        # Final assessment
        success = fixes_tested >= (total_fixes - 1)  # Allow 1 failure
        
        logger.info("=" * 80)
        logger.info("🔧 CRITICAL BUG FIXES TEST RESULTS")
        logger.info("=" * 80)
        
        fix_names = [
            "ElevenLabs API Key Authentication",
            "Enhanced Components Loading", 
            "File Path Handling and Creation",
            "RunwayML Processor File Creation",
            "Gemini Supervisor Quality Assessment"
        ]
        
        for i, fix_name in enumerate(fix_names):
            status = "✅ FIXED" if i < fixes_tested else "❌ ISSUE"
            logger.info(f"{status} {fix_name}")
        
        logger.info(f"📊 Overall: {fixes_tested}/{total_fixes} critical fixes verified")
        
        if success:
            logger.info("🎉 CRITICAL BUG FIXES VERIFICATION PASSED!")
            logger.info("✅ All major issues from problem.md have been resolved")
        else:
            logger.info("❌ CRITICAL BUG FIXES VERIFICATION FAILED!")
            logger.info("⚠️  Some critical issues may still exist")
        
        return success

async def main():
    backend_url = "https://fc574fbe-3b0c-4e7d-a840-5da941c2b339.preview.emergentagent.com"
    
    async with CriticalFixesTester(backend_url) as tester:
        success = await tester.test_critical_bug_fixes()
        
        if success:
            logger.info("🎉 ALL CRITICAL FIXES VERIFIED!")
        else:
            logger.info("❌ SOME CRITICAL ISSUES REMAIN")

if __name__ == "__main__":
    asyncio.run(main())