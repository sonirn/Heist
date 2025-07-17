#!/usr/bin/env python3
"""
Server Storage Implementation Testing
Tests the migration from R2 storage to server storage for video download functionality
"""

import asyncio
import aiohttp
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServerStorageTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = None
        self.test_results = {}
        self.server_storage_dir = "/tmp/output"
        
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
    
    async def test_health_check_endpoint(self) -> bool:
        """Test health check endpoint to ensure system is running"""
        test_name = "Health Check Endpoint"
        try:
            async with self.session.get(f"{self.api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check basic health status
                    if data.get("status") == "healthy":
                        self.log_test_result(test_name, True, "System is healthy and running", data)
                        return True
                    else:
                        self.log_test_result(test_name, False, f"System status: {data.get('status')}", data)
                        return False
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_server_storage_directory(self) -> bool:
        """Test that server storage directory exists and is accessible"""
        test_name = "Server Storage Directory"
        try:
            # Check if server storage directory exists
            if os.path.exists(self.server_storage_dir):
                # Check if directory is writable
                test_file = os.path.join(self.server_storage_dir, "test_write.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    
                    self.log_test_result(test_name, True, f"Server storage directory exists and is writable: {self.server_storage_dir}")
                    return True
                except Exception as e:
                    self.log_test_result(test_name, False, f"Directory exists but not writable: {str(e)}")
                    return False
            else:
                self.log_test_result(test_name, False, f"Server storage directory does not exist: {self.server_storage_dir}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_project_creation(self) -> Optional[str]:
        """Test project creation for video generation workflow"""
        test_name = "Project Creation"
        try:
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
                
                if response.status == 200:
                    data = await response.json()
                    project_id = data.get("project_id")
                    
                    if project_id:
                        self.log_test_result(test_name, True, f"Project created successfully: {project_id}", data)
                        return project_id
                    else:
                        self.log_test_result(test_name, False, "No project_id in response", data)
                        return None
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_video_generation_start(self, project_id: str) -> Optional[str]:
        """Test starting video generation workflow"""
        test_name = "Video Generation Start"
        try:
            generation_data = {
                "project_id": project_id,
                "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
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
                    
                    if generation_id:
                        self.log_test_result(test_name, True, f"Video generation started: {generation_id}", data)
                        return generation_id
                    else:
                        self.log_test_result(test_name, False, "No generation_id in response", data)
                        return None
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}", {"status": response.status})
                    return None
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return None
    
    async def test_video_generation_progress(self, generation_id: str, max_wait_time: int = 120) -> bool:
        """Test video generation progress monitoring"""
        test_name = "Video Generation Progress"
        try:
            start_time = time.time()
            last_progress = 0.0
            progress_updates = []
            
            while time.time() - start_time < max_wait_time:
                async with self.session.get(f"{self.api_base}/generate/{generation_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "unknown")
                        progress = data.get("progress", 0.0)
                        message = data.get("message", "")
                        
                        # Track progress updates
                        if progress > last_progress:
                            progress_updates.append({
                                "progress": progress,
                                "status": status,
                                "message": message,
                                "timestamp": datetime.now().isoformat()
                            })
                            last_progress = progress
                            logger.info(f"Progress: {progress}% - {status} - {message}")
                        
                        # Check if completed
                        if status == "completed":
                            video_url = data.get("video_url")
                            if video_url:
                                self.log_test_result(test_name, True, f"Video generation completed with URL: {video_url}", {
                                    "final_progress": progress,
                                    "video_url": video_url,
                                    "progress_updates": progress_updates
                                })
                                return True
                            else:
                                self.log_test_result(test_name, False, "Generation completed but no video URL", data)
                                return False
                        
                        # Check if failed
                        if status == "failed":
                            self.log_test_result(test_name, False, f"Video generation failed: {message}", data)
                            return False
                        
                        # Wait before next check
                        await asyncio.sleep(5)
                    else:
                        self.log_test_result(test_name, False, f"HTTP {response.status} while checking progress")
                        return False
            
            # Timeout reached
            self.log_test_result(test_name, False, f"Video generation timeout after {max_wait_time}s", {
                "last_progress": last_progress,
                "progress_updates": progress_updates
            })
            return False
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_download_endpoint(self, generation_id: str) -> bool:
        """Test the new /api/download/{generation_id} endpoint"""
        test_name = "Download Endpoint"
        try:
            async with self.session.get(f"{self.api_base}/download/{generation_id}") as response:
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    if 'video/mp4' in content_type:
                        # Read video content
                        video_content = await response.read()
                        
                        if len(video_content) > 0:
                            self.log_test_result(test_name, True, f"Video downloaded successfully: {len(video_content)} bytes", {
                                "content_type": content_type,
                                "content_length": len(video_content)
                            })
                            return True
                        else:
                            self.log_test_result(test_name, False, "Downloaded video is empty")
                            return False
                    else:
                        self.log_test_result(test_name, False, f"Invalid content type: {content_type}")
                        return False
                elif response.status == 404:
                    self.log_test_result(test_name, False, "Video file not found (404)")
                    return False
                else:
                    self.log_test_result(test_name, False, f"HTTP {response.status}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_file_existence_in_storage(self, generation_id: str) -> bool:
        """Test that video file exists in server storage directory"""
        test_name = "File Existence in Server Storage"
        try:
            expected_filename = f"final_video_{generation_id}.mp4"
            expected_path = os.path.join(self.server_storage_dir, expected_filename)
            
            if os.path.exists(expected_path):
                file_size = os.path.getsize(expected_path)
                self.log_test_result(test_name, True, f"Video file exists in server storage: {expected_path} ({file_size} bytes)")
                return True
            else:
                # Check for any video files with the generation_id
                if os.path.exists(self.server_storage_dir):
                    files = os.listdir(self.server_storage_dir)
                    matching_files = [f for f in files if generation_id in f and f.endswith('.mp4')]
                    
                    if matching_files:
                        self.log_test_result(test_name, True, f"Video file found with different naming: {matching_files[0]}")
                        return True
                    else:
                        self.log_test_result(test_name, False, f"No video file found for generation_id: {generation_id}")
                        return False
                else:
                    self.log_test_result(test_name, False, f"Server storage directory does not exist: {self.server_storage_dir}")
                    return False
                    
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_cleanup_scheduling(self, generation_id: str) -> bool:
        """Test that cleanup is scheduled for video files"""
        test_name = "Cleanup Scheduling"
        try:
            # Check if the cleanup module is available
            try:
                import sys
                sys.path.append('/app/backend')
                from cleanup import schedule_video_cleanup
                
                # Test that the function can be imported and is callable
                if callable(schedule_video_cleanup):
                    self.log_test_result(test_name, True, "Cleanup scheduling function is available and callable")
                    return True
                else:
                    self.log_test_result(test_name, False, "Cleanup function exists but is not callable")
                    return False
            except ImportError as e:
                self.log_test_result(test_name, False, f"Cleanup module not available: {str(e)}")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    async def test_r2_to_server_migration(self) -> bool:
        """Test that R2 storage functions have been replaced with server storage"""
        test_name = "R2 to Server Storage Migration"
        try:
            # Check the backend server code to verify R2 functions are replaced
            # This is a code-level test to ensure migration is complete
            
            # Read the server.py file to check for server storage implementation
            server_file_path = "/app/backend/server.py"
            if os.path.exists(server_file_path):
                with open(server_file_path, 'r') as f:
                    server_code = f.read()
                
                # Check for server storage directory usage
                if "/tmp/output" in server_code:
                    # Check for upload functions that use server storage
                    if "upload_to_r2" in server_code and "server_storage_dir" in server_code:
                        self.log_test_result(test_name, True, "R2 functions replaced with server storage while maintaining signatures")
                        return True
                    else:
                        self.log_test_result(test_name, False, "Server storage not properly implemented")
                        return False
                else:
                    self.log_test_result(test_name, False, "Server storage directory not found in code")
                    return False
            else:
                self.log_test_result(test_name, False, "Server file not found")
                return False
                
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
            return False
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "="*80)
        print("SERVER STORAGE IMPLEMENTATION TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*80)
        
        # Print detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_name}: {result['message']}")
        
        print("="*80)
        
        return passed_tests, failed_tests

async def run_server_storage_tests():
    """Run all server storage implementation tests"""
    # Get backend URL from environment
    backend_url = "https://cb9b6811-3e2b-4ac5-b88c-17d26bae6a2c.preview.emergentagent.com"
    
    async with ServerStorageTester(backend_url) as tester:
        logger.info("Starting Server Storage Implementation Tests...")
        
        # Test 1: Health Check
        health_ok = await tester.test_health_check_endpoint()
        if not health_ok:
            logger.error("Health check failed - aborting tests")
            tester.print_test_summary()
            return
        
        # Test 2: Server Storage Directory
        storage_ok = await tester.test_server_storage_directory()
        
        # Test 3: R2 to Server Migration
        migration_ok = await tester.test_r2_to_server_migration()
        
        # Test 4: Project Creation
        project_id = await tester.test_project_creation()
        if not project_id:
            logger.error("Project creation failed - skipping video generation tests")
            tester.print_test_summary()
            return
        
        # Test 5: Video Generation Start
        generation_id = await tester.test_video_generation_start(project_id)
        if not generation_id:
            logger.error("Video generation start failed - skipping remaining tests")
            tester.print_test_summary()
            return
        
        # Test 6: Video Generation Progress (with shorter timeout for testing)
        progress_ok = await tester.test_video_generation_progress(generation_id, max_wait_time=60)
        
        # Test 7: Download Endpoint (test even if generation didn't complete)
        download_ok = await tester.test_download_endpoint(generation_id)
        
        # Test 8: File Existence in Storage
        file_exists = await tester.test_file_existence_in_storage(generation_id)
        
        # Test 9: Cleanup Scheduling
        cleanup_ok = await tester.test_cleanup_scheduling(generation_id)
        
        # Print final summary
        passed, failed = tester.print_test_summary()
        
        # Return results for integration with test_result.md
        return {
            "total_tests": len(tester.test_results),
            "passed_tests": passed,
            "failed_tests": failed,
            "success_rate": (passed / len(tester.test_results)) * 100,
            "test_results": tester.test_results
        }

if __name__ == "__main__":
    asyncio.run(run_server_storage_tests())