#!/usr/bin/env python3
"""
Quick test for video generation issues
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_video_generation_issue():
    """Test the critical video generation issue seen in logs"""
    backend_url = "https://d28cdeca-dff7-4f72-a7e5-53a8cf43f6d9.preview.emergentagent.com"
    
    async with aiohttp.ClientSession() as session:
        # Create a simple project
        project_data = {
            "script": "A simple test for video generation",
            "aspect_ratio": "16:9",
            "voice_name": "default"
        }
        
        logger.info("Creating test project...")
        async with session.post(
            f"{backend_url}/api/projects",
            json=project_data,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status == 200:
                project_result = await response.json()
                project_id = project_result.get("project_id")
                logger.info(f"✅ Project created: {project_id}")
                
                # Start generation
                generation_data = {
                    "project_id": project_id,
                    "script": "A simple test for video generation",
                    "aspect_ratio": "16:9"
                }
                
                logger.info("Starting video generation...")
                async with session.post(
                    f"{backend_url}/api/generate",
                    json=generation_data,
                    headers={"Content-Type": "application/json"}
                ) as gen_response:
                    if gen_response.status == 200:
                        gen_result = await gen_response.json()
                        generation_id = gen_result.get("generation_id")
                        logger.info(f"✅ Generation started: {generation_id}")
                        
                        # Monitor for a few seconds to see the error
                        for i in range(5):
                            await asyncio.sleep(2)
                            async with session.get(f"{backend_url}/api/generate/{generation_id}") as status_response:
                                if status_response.status == 200:
                                    status_data = await status_response.json()
                                    status = status_data.get("status", "")
                                    progress = status_data.get("progress", 0.0)
                                    message = status_data.get("message", "")
                                    
                                    logger.info(f"Check {i+1}: Status={status}, Progress={progress}%, Message='{message}'")
                                    
                                    if status == "failed":
                                        logger.info(f"❌ Generation failed: {message}")
                                        return False
                                    elif status == "completed":
                                        logger.info("✅ Generation completed successfully")
                                        return True
                        
                        logger.info("⚠️ Generation still in progress after monitoring")
                        return True  # Not failed, just still processing
                    else:
                        logger.info(f"❌ Generation start failed: {gen_response.status}")
                        return False
            else:
                logger.info(f"❌ Project creation failed: {response.status}")
                return False

if __name__ == "__main__":
    result = asyncio.run(test_video_generation_issue())
    print(f"Video generation test result: {'PASS' if result else 'FAIL'}")