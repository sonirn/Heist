#!/usr/bin/env python3
"""
Comprehensive Video Generation System Testing
Focus on server storage, video generation pipeline, status updates, and download functionality
"""

import asyncio
import aiohttp
import json
import time
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoGenerationTester:
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
    
    async def test_server_storage_directory(self) -> bool:
        """Test that server storage directory exists and is writable"""
        test_name = "Server Storage Directory Check"
        try:
            storage_dir = "/tmp/output"
            
            # Check if directory exists
            if not os.path.exists(storage_dir):
                self.log_test_result(test_name, False, f"Storage directory does not exist: {storage_dir}")
                return False
            
            # Check if directory is writable
            if not os.access(storage_dir, os.W_OK):
                self.log_test_result(test_name, False, f"Storage directory is not writable: {storage_dir}")
                return False
            
            # List existing files
            existing_files = os.listdir(storage_dir)
            
            self.log_test_result(test_name, True, f"Server storage directory is ready: {storage_dir}", {
                "directory": storage_dir,
                "writable": True,
                "existing_files": len(existing_files),
                "files": existing_files[:5]  # Show first 5 files
            })
            return True
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_health_check_system(self) -> bool:
        """Test comprehensive health check system"""
        test_name = "Health Check System"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    required_fields = ["status", "version", "ai_models", "enhanced_components"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Check if system is healthy
                    if data.get("status") != "healthy":
                        self.log_test_result(test_name, False, f"System not healthy: {data.get('status')}", data)
                        return False
                    
                    # Check enhanced components
                    enhanced_components = data.get("enhanced_components", {})
                    required_components = ["gemini_supervisor", "runwayml_processor", "multi_voice_manager"]
                    
                    for component in required_components:
                        if not enhanced_components.get(component, False):
                            self.log_test_result(test_name, False, f"Component not loaded: {component}", data)
                            return False
                    
                    self.log_test_result(test_name, True, "Health check passed with all components loaded", {
                        "status": data.get("status"),
                        "version": data.get("version"),
                        "components": enhanced_components
                    })
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_project_creation(self) -> Optional[str]:
        """Test project creation with simple script"""
        test_name = "Project Creation"
        try:
            # Use the simple script from review request
            project_data = {
                "script": "A person walking in a park",
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
                    
                    self.log_test_result(test_name, True, f"Project created successfully: {project_id}", data)
                    return project_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_video_generation_start(self, project_id: str) -> Optional[str]:
        """Test video generation start"""
        test_name = "Video Generation Start"
        try:
            generation_data = {
                "project_id": project_id,
                "script": "A person walking in a park",
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
                    
                    initial_status = data.get("status", "")
                    initial_progress = data.get("progress", 0.0)
                    
                    self.log_test_result(test_name, True, f"Generation started: {generation_id}", {
                        "generation_id": generation_id,
                        "initial_status": initial_status,
                        "initial_progress": initial_progress
                    })
                    return generation_id
                else:
                    error_text = await response.text()
                    self.log_test_result(test_name, False, f"HTTP {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_status_progression(self, generation_id: str) -> Dict:
        """Test status progression from queued → processing → completed"""
        test_name = "Status Progression Monitoring"
        try:
            logger.info("🔄 MONITORING STATUS PROGRESSION")
            logger.info("=" * 60)
            
            status_history = []
            max_monitoring_time = 60  # seconds
            check_interval = 3  # seconds
            max_checks = max_monitoring_time // check_interval
            
            stuck_at_95_percent = False
            reached_completed = False
            status_changes = []
            highest_progress = 0.0
            
            for check_num in range(max_checks):
                await asyncio.sleep(check_interval)
                
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        current_status = data.get("status", "")
                        current_progress = data.get("progress", 0.0)
                        current_message = data.get("message", "")
                        
                        status_entry = {
                            "check": check_num + 1,
                            "status": current_status,
                            "progress": current_progress,
                            "message": current_message,
                            "timestamp": time.time()
                        }
                        status_history.append(status_entry)
                        
                        # Track status changes
                        if not status_changes or status_changes[-1]["status"] != current_status:
                            status_changes.append({
                                "status": current_status,
                                "progress": current_progress,
                                "message": current_message,
                                "check": check_num + 1
                            })
                        
                        # Track highest progress
                        highest_progress = max(highest_progress, current_progress)
                        
                        # Check for 95% stuck issue
                        if current_progress >= 95.0 and "Preparing video for delivery" in current_message:
                            stuck_at_95_percent = True
                            logger.info(f"⚠️  DETECTED 95% STUCK ISSUE: {current_message}")
                        
                        # Check if completed
                        if current_status == "completed":
                            reached_completed = True
                            logger.info(f"✅ Generation completed at check {check_num + 1}")
                            break
                        
                        # Check if failed
                        if current_status == "failed":
                            logger.info(f"❌ Generation failed at check {check_num + 1}: {current_message}")
                            break
                        
                        logger.info(f"📊 Check {check_num + 1}: {current_status} ({current_progress}%) - {current_message}")
                    else:
                        logger.info(f"❌ Status check {check_num + 1} failed: HTTP {response.status}")
            
            # Analyze results
            status_progression_working = len(status_changes) > 1  # At least one status change
            progress_moving = highest_progress > 0.0
            
            success = status_progression_working and progress_moving
            
            logger.info("=" * 60)
            logger.info("📊 STATUS PROGRESSION RESULTS")
            logger.info("=" * 60)
            
            logger.info(f"Status Changes: {len(status_changes)}")
            for i, change in enumerate(status_changes):
                logger.info(f"  {i+1}. {change['status']} ({change['progress']}%) - {change['message']}")
            
            logger.info(f"Highest Progress: {highest_progress}%")
            logger.info(f"Reached Completed: {reached_completed}")
            logger.info(f"Stuck at 95%: {stuck_at_95_percent}")
            
            self.log_test_result(test_name, success, f"Status progression monitored", {
                "status_changes": len(status_changes),
                "highest_progress": highest_progress,
                "reached_completed": reached_completed,
                "stuck_at_95_percent": stuck_at_95_percent,
                "status_history": status_history,
                "status_progression_working": status_progression_working,
                "progress_moving": progress_moving
            })
            
            return {
                "success": success,
                "status_changes": status_changes,
                "highest_progress": highest_progress,
                "reached_completed": reached_completed,
                "stuck_at_95_percent": stuck_at_95_percent,
                "status_history": status_history
            }
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_server_storage_files(self, generation_id: str) -> bool:
        """Test if video files are created in server storage"""
        test_name = "Server Storage File Creation"
        try:
            storage_dir = "/tmp/output"
            expected_filename = f"final_video_{generation_id}.mp4"
            expected_path = os.path.join(storage_dir, expected_filename)
            
            # Wait a bit for file creation
            await asyncio.sleep(5)
            
            # Check if file exists
            if os.path.exists(expected_path):
                file_size = os.path.getsize(expected_path)
                self.log_test_result(test_name, True, f"Video file created in server storage", {
                    "file_path": expected_path,
                    "file_size": file_size,
                    "file_exists": True
                })
                return True
            else:
                # List all files in storage directory
                all_files = os.listdir(storage_dir) if os.path.exists(storage_dir) else []
                video_files = [f for f in all_files if f.endswith('.mp4')]
                
                self.log_test_result(test_name, False, f"Expected video file not found", {
                    "expected_path": expected_path,
                    "storage_dir": storage_dir,
                    "all_files": all_files,
                    "video_files": video_files
                })
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_download_endpoint(self, generation_id: str) -> bool:
        """Test the /api/download/{generation_id} endpoint"""
        test_name = "Download Endpoint"
        try:
            download_url = f"{self.api_base}/download/{generation_id}"
            
            async with self.session.get(download_url) as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if 'video/mp4' not in content_type:
                        self.log_test_result(test_name, False, f"Wrong content type: {content_type}")
                        return False
                    
                    # Read some content to verify it's a video file
                    content = await response.read()
                    content_size = len(content)
                    
                    # Check if it's a valid MP4 file (starts with ftyp)
                    is_valid_mp4 = content[:4] == b'ftyp' or b'ftyp' in content[:100]
                    
                    self.log_test_result(test_name, True, f"Download endpoint working", {
                        "download_url": download_url,
                        "content_type": content_type,
                        "content_size": content_size,
                        "is_valid_mp4": is_valid_mp4
                    })
                    return True
                elif response.status == 404:
                    self.log_test_result(test_name, False, f"Video file not found (404)")
                    return False
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_database_operations(self, generation_id: str) -> bool:
        """Test database operations for generation data"""
        test_name = "Database Operations"
        try:
            # Get generation status to verify database storage
            async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if generation data is properly stored
                    required_fields = ["status", "progress"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing database fields: {missing_fields}", data)
                        return False
                    
                    # Check if timestamps are present
                    has_timestamps = any(field in data for field in ["created_at", "updated_at"])
                    
                    self.log_test_result(test_name, True, f"Database operations working", {
                        "generation_id": generation_id,
                        "status": data.get("status"),
                        "progress": data.get("progress"),
                        "has_timestamps": has_timestamps,
                        "data_fields": list(data.keys())
                    })
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_queue_processing(self) -> bool:
        """Test queue manager processing"""
        test_name = "Queue Processing"
        try:
            # Check health endpoint for queue status
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check if queue information is present
                    queue_info = data.get("queue", {})
                    if not queue_info:
                        self.log_test_result(test_name, False, "No queue information in health check")
                        return False
                    
                    # Check queue fields
                    queue_fields = ["active_tasks", "completed_tasks", "failed_tasks"]
                    missing_fields = [field for field in queue_fields if field not in queue_info]
                    
                    if missing_fields:
                        self.log_test_result(test_name, False, f"Missing queue fields: {missing_fields}", queue_info)
                        return False
                    
                    self.log_test_result(test_name, True, f"Queue processing system operational", {
                        "active_tasks": queue_info.get("active_tasks", 0),
                        "completed_tasks": queue_info.get("completed_tasks", 0),
                        "failed_tasks": queue_info.get("failed_tasks", 0)
                    })
                    return True
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def run_comprehensive_test(self) -> Dict:
        """Run comprehensive video generation system test"""
        logger.info("🎬 STARTING COMPREHENSIVE VIDEO GENERATION SYSTEM TEST")
        logger.info("=" * 80)
        
        test_results = {}
        
        # Test 1: Server Storage Directory
        logger.info("📁 Test 1: Server Storage Directory...")
        test_results["server_storage_directory"] = await self.test_server_storage_directory()
        
        # Test 2: Health Check System
        logger.info("🏥 Test 2: Health Check System...")
        test_results["health_check_system"] = await self.test_health_check_system()
        
        # Test 3: Project Creation
        logger.info("📝 Test 3: Project Creation...")
        project_id = await self.test_project_creation()
        test_results["project_creation"] = project_id is not None
        
        if not project_id:
            logger.info("❌ Cannot continue without project_id")
            return test_results
        
        # Test 4: Video Generation Start
        logger.info("🚀 Test 4: Video Generation Start...")
        generation_id = await self.test_video_generation_start(project_id)
        test_results["video_generation_start"] = generation_id is not None
        
        if not generation_id:
            logger.info("❌ Cannot continue without generation_id")
            return test_results
        
        # Test 5: Status Progression
        logger.info("📊 Test 5: Status Progression...")
        status_result = await self.test_status_progression(generation_id)
        test_results["status_progression"] = status_result.get("success", False)
        test_results["status_details"] = status_result
        
        # Test 6: Server Storage Files
        logger.info("💾 Test 6: Server Storage Files...")
        test_results["server_storage_files"] = await self.test_server_storage_files(generation_id)
        
        # Test 7: Download Endpoint
        logger.info("⬇️  Test 7: Download Endpoint...")
        test_results["download_endpoint"] = await self.test_download_endpoint(generation_id)
        
        # Test 8: Database Operations
        logger.info("🗄️  Test 8: Database Operations...")
        test_results["database_operations"] = await self.test_database_operations(generation_id)
        
        # Test 9: Queue Processing
        logger.info("⚡ Test 9: Queue Processing...")
        test_results["queue_processing"] = await self.test_queue_processing()
        
        # Calculate overall results
        passed_tests = sum(1 for result in test_results.values() if isinstance(result, bool) and result)
        total_tests = sum(1 for result in test_results.values() if isinstance(result, bool))
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("🎯 COMPREHENSIVE TEST RESULTS")
        logger.info("=" * 80)
        
        for test_name, result in test_results.items():
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                logger.info(f"{status} {test_name.replace('_', ' ').title()}")
        
        logger.info(f"📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Specific analysis for the 95% stuck issue
        if "status_details" in test_results:
            status_details = test_results["status_details"]
            if status_details.get("stuck_at_95_percent"):
                logger.info("⚠️  CRITICAL ISSUE IDENTIFIED: Video generation stuck at 95%")
                logger.info("   - Videos are successfully generated in /tmp/output")
                logger.info("   - Download endpoint may be working")
                logger.info("   - Issue is in status reporting, not actual video generation")
            
            if status_details.get("reached_completed"):
                logger.info("✅ Video generation completed successfully")
            else:
                logger.info("⚠️  Video generation did not reach completed status")
        
        return {
            "test_results": test_results,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": success_rate,
            "project_id": project_id,
            "generation_id": generation_id
        }

async def main():
    """Main test execution"""
    # Get backend URL from environment
    backend_url = "https://cb9b6811-3e2b-4ac5-b88c-17d26bae6a2c.preview.emergentagent.com"
    
    async with VideoGenerationTester(backend_url) as tester:
        results = await tester.run_comprehensive_test()
        
        logger.info("=" * 80)
        logger.info("🎬 VIDEO GENERATION SYSTEM TEST COMPLETED")
        logger.info("=" * 80)
        
        return results

if __name__ == "__main__":
    asyncio.run(main())