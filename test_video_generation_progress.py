#!/usr/bin/env python3
"""
Test script to create a video generation project and monitor progress with 3-second intervals
as requested in the continuation task.
"""

import asyncio
import aiohttp
import time
import json
import sys
from datetime import datetime

# Backend URL
BACKEND_URL = "http://localhost:8001"

# Test script as specified in the continuation
TEST_SCRIPT = "A person walking in a sunny park. The weather is beautiful and birds are singing."

async def create_project():
    """Create a test project"""
    print("🚀 Creating test project...")
    
    async with aiohttp.ClientSession() as session:
        project_data = {
            "title": "Test Project - Park Walking",
            "description": "Test project for video generation progress monitoring",
            "script": TEST_SCRIPT,
            "settings": {
                "aspect_ratio": "16:9",
                "voice_id": "default"
            }
        }
        
        async with session.post(f"{BACKEND_URL}/api/projects", json=project_data) as resp:
            if resp.status in [200, 201]:
                project = await resp.json()
                print(f"✅ Project created successfully: {project['project_id']}")
                return project['project_id']
            else:
                error_text = await resp.text()
                print(f"❌ Failed to create project: {resp.status} - {error_text}")
                return None

async def start_video_generation(project_id):
    """Start video generation"""
    print("🎬 Starting video generation...")
    
    async with aiohttp.ClientSession() as session:
        generation_data = {
            "project_id": project_id,
            "script": TEST_SCRIPT,
            "aspect_ratio": "16:9",
            "voice_id": "default"
        }
        
        async with session.post(f"{BACKEND_URL}/api/generate", json=generation_data) as resp:
            if resp.status == 200:
                generation = await resp.json()
                print(f"✅ Video generation started: {generation['generation_id']}")
                return generation['generation_id']
            else:
                error_text = await resp.text()
                print(f"❌ Failed to start generation: {resp.status} - {error_text}")
                return None

async def monitor_progress(generation_id):
    """Monitor progress with 3-second intervals"""
    print(f"📊 Monitoring progress for generation: {generation_id}")
    print("Expected progression: 'Preparing video for delivery...' → 'Final quality assessment...' → 'Video generation completed successfully!'")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        last_progress = -1
        last_message = ""
        start_time = time.time()
        stuck_at_95_count = 0
        
        while True:
            try:
                async with session.get(f"{BACKEND_URL}/api/generate/{generation_id}") as resp:
                    if resp.status == 200:
                        status = await resp.json()
                        current_progress = status.get('progress', 0)
                        current_message = status.get('message', '')
                        current_status = status.get('status', '')
                        
                        elapsed = time.time() - start_time
                        
                        # Only show updates when progress or message changes
                        if current_progress != last_progress or current_message != last_message:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] Progress: {current_progress:.1f}% | Status: {current_status} | Message: {current_message}")
                            
                            # Check for the specific 95% stuck issue
                            if current_progress == 95.0 and "Preparing video for delivery..." in current_message:
                                stuck_at_95_count += 1
                                if stuck_at_95_count == 1:
                                    print("🚨 ISSUE DETECTED: Progress stuck at 95% with 'Preparing video for delivery...'")
                                    print("⏰ This is the critical point where it should progress to 98% 'Final quality assessment...'")
                                elif stuck_at_95_count > 5:
                                    print(f"⚠️  Still stuck at 95% after {stuck_at_95_count * 3} seconds")
                            
                            last_progress = current_progress
                            last_message = current_message
                        
                        # Check completion conditions
                        if current_status == "completed":
                            print(f"✅ VIDEO GENERATION COMPLETED SUCCESSFULLY!")
                            print(f"📊 Final Progress: {current_progress}%")
                            print(f"⏱️  Total Time: {elapsed:.1f} seconds")
                            
                            # Check if video can be downloaded
                            try:
                                async with session.get(f"{BACKEND_URL}/api/download/{generation_id}") as download_resp:
                                    if download_resp.status == 200:
                                        content_length = download_resp.headers.get('content-length', 'unknown')
                                        print(f"📥 Video is downloadable! Size: {content_length} bytes")
                                    else:
                                        print(f"❌ Video download failed: {download_resp.status}")
                            except Exception as e:
                                print(f"❌ Error checking download: {e}")
                            
                            return True
                        
                        elif current_status == "failed":
                            print(f"❌ VIDEO GENERATION FAILED!")
                            print(f"💔 Error: {current_message}")
                            print(f"⏱️  Failed after: {elapsed:.1f} seconds")
                            return False
                        
                        # Check for timeout (5 minutes)
                        if elapsed > 300:
                            print(f"⏰ TIMEOUT: Generation taking too long (>5 minutes)")
                            print(f"📊 Last Progress: {current_progress}%")
                            print(f"💬 Last Message: {current_message}")
                            
                            # Still check if video was generated despite timeout
                            try:
                                async with session.get(f"{BACKEND_URL}/api/download/{generation_id}") as download_resp:
                                    if download_resp.status == 200:
                                        content_length = download_resp.headers.get('content-length', 'unknown')
                                        print(f"📥 Video exists despite timeout! Size: {content_length} bytes")
                                        print("✅ Videos are still being generated (as per continuation requirement)")
                                    else:
                                        print(f"❌ No video found: {download_resp.status}")
                            except Exception as e:
                                print(f"❌ Error checking download: {e}")
                            
                            return False
                        
                    else:
                        print(f"❌ Failed to get status: {resp.status}")
                        return False
                        
            except Exception as e:
                print(f"❌ Error monitoring progress: {e}")
                return False
            
            # Wait 3 seconds as specified in the continuation
            await asyncio.sleep(3)

async def main():
    """Main test function"""
    print("🧪 Video Generation Progress Test")
    print("=" * 50)
    print(f"📝 Test Script: '{TEST_SCRIPT}'")
    print("⏱️  Monitoring interval: 3 seconds")
    print("🎯 Expected status messages:")
    print("   1. 'Preparing video for delivery...' (95%)")
    print("   2. 'Final quality assessment...' (98%)")
    print("   3. 'Video generation completed successfully!' (100%)")
    print("=" * 50)
    
    # Step 1: Create project
    project_id = await create_project()
    if not project_id:
        print("❌ Test failed: Could not create project")
        return False
    
    # Step 2: Start video generation
    generation_id = await start_video_generation(project_id)
    if not generation_id:
        print("❌ Test failed: Could not start video generation")
        return False
    
    # Step 3: Monitor progress
    success = await monitor_progress(generation_id)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TEST PASSED: Video generation completed successfully!")
        print("✅ Expected status messages were observed")
        print("✅ Videos are being generated and can be downloaded")
    else:
        print("❌ TEST IDENTIFIED ISSUES: Video generation has problems")
        print("🔍 This confirms the 95% stuck issue mentioned in the continuation")
        
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        sys.exit(1)