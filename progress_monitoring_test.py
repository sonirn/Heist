#!/usr/bin/env python3
"""
Video Generation Progress Monitoring Test
Specifically tests the 95% stuck issue resolution and complete progress flow
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

class ProgressMonitoringTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60))
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
        """Test basic health check"""
        test_name = "Health Check"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_test_result(test_name, True, f"Health check passed - Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    self.log_test_result(test_name, False, f"Health check failed with status {response.status}")
                    return False
        except Exception as e:
            self.log_test_result(test_name, False, f"Health check error: {str(e)}")
            return False
    
    async def test_create_project(self) -> Optional[str]:
        """Create a test project with simple script"""
        test_name = "Create Test Project"
        try:
            project_data = {
                "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(f"{self.api_base}/projects", json=project_data) as response:
                if response.status == 200:
                    data = await response.json()
                    project_id = data.get("project_id")
                    self.log_test_result(test_name, True, f"Project created successfully: {project_id}")
                    return project_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"Project creation failed with status {response.status}: {error_text}")
                    return None
        except Exception as e:
            self.log_test_result(test_name, False, f"Project creation error: {str(e)}")
            return None
    
    async def test_start_video_generation(self, project_id: str) -> Optional[str]:
        """Start video generation and return generation_id"""
        test_name = "Start Video Generation"
        try:
            generation_data = {
                "project_id": project_id,
                "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
                "aspect_ratio": "16:9"
            }
            
            async with self.session.post(f"{self.api_base}/generate", json=generation_data) as response:
                if response.status == 200:
                    data = await response.json()
                    generation_id = data.get("generation_id")
                    self.log_test_result(test_name, True, f"Video generation started: {generation_id}")
                    return generation_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"Generation start failed with status {response.status}: {error_text}")
                    return None
        except Exception as e:
            self.log_test_result(test_name, False, f"Generation start error: {str(e)}")
            return None
    
    async def monitor_progress_detailed(self, generation_id: str, max_duration: int = 300) -> Dict:
        """Monitor video generation progress with detailed tracking"""
        test_name = "Detailed Progress Monitoring"
        
        progress_history = []
        start_time = time.time()
        last_progress = -1
        stuck_at_95_time = None
        reached_98 = False
        reached_100 = False
        
        logger.info(f"🎬 Starting detailed progress monitoring for generation: {generation_id}")
        
        try:
            while time.time() - start_time < max_duration:
                try:
                    async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                        if response.status == 200:
                            data = await response.json()
                            current_progress = data.get("progress", 0)
                            status = data.get("status", "unknown")
                            message = data.get("message", "")
                            
                            # Log progress changes
                            if current_progress != last_progress:
                                elapsed = time.time() - start_time
                                progress_entry = {
                                    "timestamp": datetime.now().isoformat(),
                                    "elapsed_seconds": round(elapsed, 2),
                                    "progress": current_progress,
                                    "status": status,
                                    "message": message
                                }
                                progress_history.append(progress_entry)
                                
                                logger.info(f"📊 Progress Update: {current_progress}% - Status: {status} - Message: {message}")
                                last_progress = current_progress
                            
                            # Track specific milestones
                            if current_progress >= 95 and current_progress < 98 and stuck_at_95_time is None:
                                stuck_at_95_time = time.time()
                                logger.info(f"🚨 CRITICAL CHECKPOINT: Reached 95% at {elapsed:.2f}s - Monitoring for stuck issue...")
                            
                            if current_progress >= 98 and not reached_98:
                                reached_98 = True
                                if stuck_at_95_time:
                                    time_at_95 = time.time() - stuck_at_95_time
                                    logger.info(f"✅ PROGRESS MILESTONE: Moved from 95% to 98% in {time_at_95:.2f}s")
                                else:
                                    logger.info(f"✅ PROGRESS MILESTONE: Reached 98% - Final quality assessment")
                            
                            if current_progress >= 100 and not reached_100:
                                reached_100 = True
                                total_time = time.time() - start_time
                                logger.info(f"🎉 COMPLETION: Reached 100% in {total_time:.2f}s total")
                            
                            # Check for completion
                            if status in ["completed", "failed"]:
                                total_time = time.time() - start_time
                                
                                # Analyze the progress flow
                                analysis = self.analyze_progress_flow(progress_history, stuck_at_95_time, reached_98, reached_100)
                                
                                if status == "completed" and reached_100:
                                    self.log_test_result(test_name, True, 
                                        f"Progress monitoring completed successfully in {total_time:.2f}s. "
                                        f"Reached 98%: {reached_98}, Reached 100%: {reached_100}", 
                                        {
                                            "total_duration": total_time,
                                            "progress_history": progress_history,
                                            "analysis": analysis,
                                            "final_status": status,
                                            "video_url": data.get("video_url")
                                        })
                                    return {
                                        "success": True,
                                        "progress_history": progress_history,
                                        "analysis": analysis,
                                        "total_duration": total_time,
                                        "final_status": status,
                                        "video_url": data.get("video_url")
                                    }
                                else:
                                    self.log_test_result(test_name, False, 
                                        f"Progress monitoring failed - Status: {status}, Reached 100%: {reached_100}", 
                                        {
                                            "total_duration": total_time,
                                            "progress_history": progress_history,
                                            "analysis": analysis,
                                            "final_status": status
                                        })
                                    return {
                                        "success": False,
                                        "progress_history": progress_history,
                                        "analysis": analysis,
                                        "total_duration": total_time,
                                        "final_status": status
                                    }
                        else:
                            logger.warning(f"⚠️ Status check failed with HTTP {response.status}")
                
                except Exception as e:
                    logger.warning(f"⚠️ Progress check error: {str(e)}")
                
                # Wait before next check
                await asyncio.sleep(2)
            
            # Timeout reached
            total_time = time.time() - start_time
            analysis = self.analyze_progress_flow(progress_history, stuck_at_95_time, reached_98, reached_100)
            
            self.log_test_result(test_name, False, 
                f"Progress monitoring timed out after {total_time:.2f}s. Last progress: {last_progress}%", 
                {
                    "total_duration": total_time,
                    "progress_history": progress_history,
                    "analysis": analysis,
                    "timeout": True
                })
            
            return {
                "success": False,
                "progress_history": progress_history,
                "analysis": analysis,
                "total_duration": total_time,
                "timeout": True
            }
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Progress monitoring error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_progress_flow(self, progress_history: List[Dict], stuck_at_95_time: Optional[float], reached_98: bool, reached_100: bool) -> Dict:
        """Analyze the progress flow for issues"""
        analysis = {
            "total_progress_updates": len(progress_history),
            "stuck_at_95_detected": stuck_at_95_time is not None,
            "reached_98_percent": reached_98,
            "reached_100_percent": reached_100,
            "progress_milestones": [],
            "potential_issues": []
        }
        
        # Extract key milestones
        for entry in progress_history:
            progress = entry["progress"]
            if progress in [0, 15, 25, 60, 70, 80, 90, 95, 98, 100]:
                analysis["progress_milestones"].append({
                    "progress": progress,
                    "timestamp": entry["timestamp"],
                    "elapsed": entry["elapsed_seconds"],
                    "message": entry["message"]
                })
        
        # Check for issues
        if stuck_at_95_time and not reached_98:
            analysis["potential_issues"].append("Progress stuck at 95% without reaching 98%")
        
        if reached_98 and not reached_100:
            analysis["potential_issues"].append("Reached 98% but never completed to 100%")
        
        # Check for long gaps in progress
        if len(progress_history) > 1:
            for i in range(1, len(progress_history)):
                time_gap = progress_history[i]["elapsed_seconds"] - progress_history[i-1]["elapsed_seconds"]
                if time_gap > 30:  # More than 30 seconds between updates
                    analysis["potential_issues"].append(f"Long gap ({time_gap:.1f}s) between {progress_history[i-1]['progress']}% and {progress_history[i]['progress']}%")
        
        return analysis
    
    async def test_video_download(self, generation_id: str, video_url: Optional[str]) -> bool:
        """Test video download functionality"""
        test_name = "Video Download Test"
        
        if not video_url:
            self.log_test_result(test_name, False, "No video URL provided for download test")
            return False
        
        try:
            # Extract generation_id from URL if it's a download URL
            if "/api/download/" in video_url:
                download_url = f"{self.base_url}{video_url}"
            else:
                download_url = video_url
            
            async with self.session.get(download_url) as response:
                if response.status == 200:
                    content = await response.read()
                    content_length = len(content)
                    content_type = response.headers.get('content-type', 'unknown')
                    
                    self.log_test_result(test_name, True, 
                        f"Video downloaded successfully - Size: {content_length} bytes, Type: {content_type}",
                        {
                            "content_length": content_length,
                            "content_type": content_type,
                            "download_url": download_url
                        })
                    return True
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, 
                        f"Video download failed with status {response.status}: {error_text}")
                    return False
        except Exception as e:
            self.log_test_result(test_name, False, f"Video download error: {str(e)}")
            return False
    
    async def run_complete_progress_test(self) -> Dict:
        """Run the complete progress monitoring test"""
        logger.info("🎬 STARTING COMPREHENSIVE VIDEO GENERATION PROGRESS MONITORING TEST")
        logger.info("=" * 80)
        
        # Step 1: Health Check
        health_ok = await self.test_health_check()
        if not health_ok:
            return {"success": False, "error": "Health check failed"}
        
        # Step 2: Create Project
        project_id = await self.test_create_project()
        if not project_id:
            return {"success": False, "error": "Project creation failed"}
        
        # Step 3: Start Generation
        generation_id = await self.test_start_video_generation(project_id)
        if not generation_id:
            return {"success": False, "error": "Generation start failed"}
        
        # Step 4: Monitor Progress (Main Test)
        progress_result = await self.monitor_progress_detailed(generation_id)
        
        # Step 5: Test Download if video was generated
        if progress_result.get("success") and progress_result.get("video_url"):
            download_ok = await self.test_video_download(generation_id, progress_result["video_url"])
            progress_result["download_test"] = download_ok
        
        return progress_result
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "=" * 80)
        logger.info("🎯 VIDEO GENERATION PROGRESS MONITORING TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        logger.info(f"📊 Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {total_tests - passed_tests}")
        logger.info(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            logger.info(f"{status} - {test_name}: {result['message']}")
        
        logger.info("=" * 80)

async def main():
    """Main test execution"""
    # Get backend URL from environment
    import os
    backend_url = os.getenv("REACT_APP_BACKEND_URL", "https://533dceb9-a2e4-4c4e-88fc-2fdbbf93e5c9.preview.emergentagent.com")
    
    logger.info(f"🎯 Testing backend at: {backend_url}")
    
    async with ProgressMonitoringTester(backend_url) as tester:
        # Run the complete test
        result = await tester.run_complete_progress_test()
        
        # Print summary
        tester.print_summary()
        
        # Print final result
        if result.get("success"):
            logger.info("🎉 OVERALL RESULT: VIDEO GENERATION PROGRESS MONITORING TEST PASSED!")
            if result.get("analysis"):
                analysis = result["analysis"]
                logger.info(f"📊 Key Findings:")
                logger.info(f"   - Progress updates: {analysis['total_progress_updates']}")
                logger.info(f"   - Reached 98%: {analysis['reached_98_percent']}")
                logger.info(f"   - Reached 100%: {analysis['reached_100_percent']}")
                logger.info(f"   - Issues detected: {len(analysis['potential_issues'])}")
                if analysis['potential_issues']:
                    for issue in analysis['potential_issues']:
                        logger.info(f"     ⚠️ {issue}")
        else:
            logger.info("❌ OVERALL RESULT: VIDEO GENERATION PROGRESS MONITORING TEST FAILED!")
            if result.get("error"):
                logger.info(f"💥 Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())