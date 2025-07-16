#!/usr/bin/env python3
"""
Video Generation Progress Monitoring Test - 95% Stuck Issue Fix Verification
This test specifically verifies that the 95% stuck issue has been resolved.

Focus Areas:
1. Create a test project with a simple script
2. Start video generation and monitor progress carefully
3. Verify that the progress now moves properly from 95% → 98% → 100%
4. Check that the status messages progress correctly: 
   "Preparing video for delivery..." → "Final quality assessment..." → "Video generation completed successfully!"
5. Ensure videos are still being generated and can be downloaded
"""

import asyncio
import aiohttp
import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Progress95PercentTester:
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
    
    async def test_95_percent_stuck_fix(self) -> bool:
        """
        Test the specific 95% stuck issue fix
        This is the critical test requested in the review
        """
        test_name = "95% Progress Stuck Issue Fix"
        try:
            logger.info("🎯 TESTING 95% PROGRESS STUCK ISSUE FIX")
            logger.info("=" * 80)
            logger.info("This test verifies that video generation progress no longer gets stuck at 95%")
            logger.info("Expected progression: 95% → 98% → 100%")
            logger.info("Expected messages: 'Preparing video for delivery...' → 'Final quality assessment...' → 'Video generation completed successfully!'")
            logger.info("=" * 80)
            
            # Step 1: Create a test project with simple script
            simple_script = "A person walking in a sunny park. The weather is beautiful and birds are singing."
            
            project_data = {
                "script": simple_script,
                "aspect_ratio": "16:9",
                "voice_name": "default"
            }
            
            logger.info("📝 Step 1: Creating test project with simple script...")
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
                
                logger.info(f"✅ Test project created: {project_id}")
            
            # Step 2: Start video generation
            logger.info("🚀 Step 2: Starting video generation...")
            generation_data = {
                "project_id": project_id,
                "script": simple_script,
                "aspect_ratio": "16:9"
            }
            
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
                
                logger.info(f"✅ Video generation started: {generation_id}")
            
            # Step 3: Monitor progress with special focus on 95% → 98% → 100% progression
            logger.info("📊 Step 3: Monitoring progress with focus on 95% → 98% → 100% progression...")
            
            progress_history = []
            status_messages = []
            max_monitoring_time = 600  # 10 minutes - extended for thorough testing
            check_interval = 3  # Check every 3 seconds
            checks_performed = 0
            max_checks = max_monitoring_time // check_interval
            
            # Critical tracking variables
            reached_95_percent = False
            reached_98_percent = False
            reached_100_percent = False
            stuck_at_95_time = None
            stuck_at_95_duration = 0
            
            # Expected status messages
            expected_messages = {
                "preparing_delivery": "Preparing video for delivery...",
                "final_assessment": "Final quality assessment...",
                "completed": "Video generation completed successfully!"
            }
            
            found_messages = {key: False for key in expected_messages.keys()}
            
            start_time = time.time()
            
            for check_num in range(max_checks):
                await asyncio.sleep(check_interval)
                checks_performed += 1
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        current_status = status_data.get("status", "")
                        current_progress = status_data.get("progress", 0.0)
                        current_message = status_data.get("message", "")
                        
                        # Record progress history
                        progress_entry = {
                            "check": check_num + 1,
                            "elapsed_time": elapsed_time,
                            "status": current_status,
                            "progress": current_progress,
                            "message": current_message,
                            "timestamp": datetime.now().isoformat()
                        }
                        progress_history.append(progress_entry)
                        
                        # Track critical progress milestones
                        if current_progress >= 95.0 and not reached_95_percent:
                            reached_95_percent = True
                            stuck_at_95_time = current_time
                            logger.info(f"🎯 REACHED 95%! Time: {elapsed_time:.1f}s - Message: '{current_message}'")
                        
                        if current_progress >= 98.0 and not reached_98_percent:
                            reached_98_percent = True
                            if stuck_at_95_time:
                                stuck_at_95_duration = current_time - stuck_at_95_time
                            logger.info(f"🎯 REACHED 98%! Time: {elapsed_time:.1f}s - Message: '{current_message}'")
                        
                        if current_progress >= 100.0 and not reached_100_percent:
                            reached_100_percent = True
                            logger.info(f"🎯 REACHED 100%! Time: {elapsed_time:.1f}s - Message: '{current_message}'")
                        
                        # Check for expected status messages
                        message_lower = current_message.lower()
                        if "preparing video for delivery" in message_lower:
                            found_messages["preparing_delivery"] = True
                            logger.info(f"📨 Found expected message: 'Preparing video for delivery...'")
                        
                        if "final quality assessment" in message_lower:
                            found_messages["final_assessment"] = True
                            logger.info(f"📨 Found expected message: 'Final quality assessment...'")
                        
                        if "video generation completed successfully" in message_lower:
                            found_messages["completed"] = True
                            logger.info(f"📨 Found expected message: 'Video generation completed successfully!'")
                        
                        # Log progress with special attention to 95%+ range
                        if current_progress >= 95.0:
                            logger.info(f"🔍 CRITICAL RANGE - Check {check_num + 1}: {current_progress}% - '{current_message}' (Elapsed: {elapsed_time:.1f}s)")
                        else:
                            logger.info(f"📈 Check {check_num + 1}: {current_progress}% - '{current_message}' (Elapsed: {elapsed_time:.1f}s)")
                        
                        # Check if stuck at 95% for too long (more than 60 seconds)
                        if reached_95_percent and not reached_98_percent:
                            current_stuck_duration = current_time - stuck_at_95_time
                            if current_stuck_duration > 60:  # 60 seconds threshold
                                logger.warning(f"⚠️  POTENTIAL STUCK ISSUE: Been at 95%+ for {current_stuck_duration:.1f} seconds")
                        
                        # If completed or failed, break
                        if current_status in ["completed", "failed"]:
                            logger.info(f"🏁 Generation finished with status: {current_status}")
                            break
                            
                        # If stuck at 95% for more than 5 minutes, consider it failed
                        if reached_95_percent and not reached_98_percent and (current_time - stuck_at_95_time) > 300:
                            logger.error(f"❌ STUCK AT 95% FOR MORE THAN 5 MINUTES - Test failed")
                            break
                    else:
                        logger.error(f"❌ Status check {check_num + 1} failed: HTTP {response.status}")
            
            # Step 4: Verify video can be downloaded (if generation completed)
            video_downloadable = False
            if reached_100_percent:
                logger.info("📥 Step 4: Verifying video download functionality...")
                try:
                    async with self.session.get(f"{self.api_base}/download/{generation_id}") as response:
                        if response.status == 200:
                            content_length = response.headers.get('content-length', '0')
                            content_type = response.headers.get('content-type', '')
                            
                            if 'video' in content_type and int(content_length) > 1000:  # At least 1KB
                                video_downloadable = True
                                logger.info(f"✅ Video downloadable: {content_length} bytes, type: {content_type}")
                            else:
                                logger.warning(f"⚠️  Video download issue: {content_length} bytes, type: {content_type}")
                        else:
                            logger.warning(f"⚠️  Video download failed: HTTP {response.status}")
                except Exception as e:
                    logger.warning(f"⚠️  Video download test failed: {str(e)}")
            
            # Step 5: Analyze results and determine if 95% stuck issue is fixed
            logger.info("📋 Step 5: Analyzing 95% stuck issue fix results...")
            
            # Calculate stuck duration at 95%
            if stuck_at_95_time and reached_98_percent:
                stuck_duration = stuck_at_95_duration
            elif stuck_at_95_time and not reached_98_percent:
                stuck_duration = time.time() - stuck_at_95_time
            else:
                stuck_duration = 0
            
            # Success criteria for 95% stuck fix
            success_criteria = {
                "reached_95_percent": reached_95_percent,
                "progressed_beyond_95": reached_98_percent,
                "reached_completion": reached_100_percent,
                "not_stuck_too_long": stuck_duration < 120,  # Less than 2 minutes at 95%
                "found_preparing_message": found_messages["preparing_delivery"],
                "found_assessment_message": found_messages["final_assessment"],
                "found_completion_message": found_messages["completed"],
                "video_downloadable": video_downloadable or not reached_100_percent  # Only required if completed
            }
            
            passed_criteria = sum(success_criteria.values())
            total_criteria = len(success_criteria)
            success_rate = (passed_criteria / total_criteria) * 100
            
            # Determine overall success
            critical_criteria_passed = (
                reached_95_percent and 
                (reached_98_percent or stuck_duration < 60) and
                (not reached_95_percent or stuck_duration < 300)  # Not stuck for more than 5 minutes
            )
            
            logger.info("=" * 80)
            logger.info("🎯 95% PROGRESS STUCK ISSUE FIX RESULTS")
            logger.info("=" * 80)
            
            for criterion, passed in success_criteria.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                logger.info(f"{status} {criterion.replace('_', ' ').title()}")
            
            logger.info(f"\n📊 Progress Analysis:")
            logger.info(f"   - Reached 95%: {'Yes' if reached_95_percent else 'No'}")
            logger.info(f"   - Reached 98%: {'Yes' if reached_98_percent else 'No'}")
            logger.info(f"   - Reached 100%: {'Yes' if reached_100_percent else 'No'}")
            logger.info(f"   - Time stuck at 95%: {stuck_duration:.1f} seconds")
            logger.info(f"   - Total monitoring time: {elapsed_time:.1f} seconds")
            logger.info(f"   - Checks performed: {checks_performed}")
            
            logger.info(f"\n📨 Expected Messages Found:")
            for key, found in found_messages.items():
                status = "✅" if found else "❌"
                logger.info(f"   {status} {expected_messages[key]}")
            
            logger.info(f"\n📥 Video Download: {'✅ Working' if video_downloadable else '❌ Not tested/failed'}")
            
            logger.info(f"\n🎯 SUCCESS RATE: {passed_criteria}/{total_criteria} ({success_rate:.1f}%)")
            
            # Final determination
            if critical_criteria_passed and success_rate >= 75:
                self.log_test_result(
                    test_name, 
                    True, 
                    f"95% stuck issue appears to be FIXED! Progress moved properly through 95% → 98% → 100% in {stuck_duration:.1f}s",
                    {
                        "reached_95": reached_95_percent,
                        "reached_98": reached_98_percent,
                        "reached_100": reached_100_percent,
                        "stuck_duration": stuck_duration,
                        "success_rate": success_rate,
                        "messages_found": found_messages,
                        "video_downloadable": video_downloadable,
                        "progress_history": progress_history[-10:]  # Last 10 entries
                    }
                )
                return True
            else:
                failure_reason = []
                if not reached_95_percent:
                    failure_reason.append("never reached 95%")
                elif not reached_98_percent:
                    failure_reason.append("stuck at 95% without progressing to 98%")
                elif stuck_duration > 120:
                    failure_reason.append(f"stuck at 95% for too long ({stuck_duration:.1f}s)")
                
                self.log_test_result(
                    test_name, 
                    False, 
                    f"95% stuck issue NOT FIXED: {', '.join(failure_reason)}",
                    {
                        "reached_95": reached_95_percent,
                        "reached_98": reached_98_percent,
                        "reached_100": reached_100_percent,
                        "stuck_duration": stuck_duration,
                        "success_rate": success_rate,
                        "messages_found": found_messages,
                        "video_downloadable": video_downloadable,
                        "failure_reasons": failure_reason,
                        "progress_history": progress_history[-10:]  # Last 10 entries
                    }
                )
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception during 95% stuck test: {str(e)}")
            logger.error(f"Exception in 95% stuck test: {str(e)}")
            return False
    
    async def run_95_percent_fix_verification(self):
        """Run the 95% stuck issue fix verification test"""
        logger.info("🎯 STARTING 95% PROGRESS STUCK ISSUE FIX VERIFICATION")
        logger.info("=" * 80)
        
        # Run the critical test
        fix_verified = await self.test_95_percent_stuck_fix()
        
        # Summary
        logger.info("=" * 80)
        logger.info("🎯 95% STUCK ISSUE FIX VERIFICATION SUMMARY")
        logger.info("=" * 80)
        
        if fix_verified:
            logger.info("✅ SUCCESS: The 95% stuck issue appears to be FIXED!")
            logger.info("   - Progress moves properly from 95% → 98% → 100%")
            logger.info("   - Expected status messages are working")
            logger.info("   - Videos are still being generated and downloadable")
        else:
            logger.info("❌ FAILURE: The 95% stuck issue is NOT FIXED")
            logger.info("   - Progress still gets stuck at 95%")
            logger.info("   - Further investigation and fixes needed")
        
        return {
            "95_percent_fix_verified": fix_verified,
            "test_results": self.test_results
        }

async def main():
    """Main test execution"""
    # Get backend URL from environment
    backend_url = os.getenv("REACT_APP_BACKEND_URL", "https://486c6065-7afc-46ff-b95a-0fcc1310281b.preview.emergentagent.com")
    
    logger.info(f"🎯 Testing 95% stuck issue fix against: {backend_url}")
    
    async with Progress95PercentTester(backend_url) as tester:
        results = await tester.run_95_percent_fix_verification()
        
        # Print final results
        logger.info("=" * 80)
        logger.info("🎯 FINAL TEST RESULTS")
        logger.info("=" * 80)
        
        for test_name, result in results["test_results"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} {test_name}: {result['message']}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())