#!/usr/bin/env python3
"""
Quick Production Backend Assessment
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def quick_assessment():
    backend_url = "https://e998c079-1531-47a1-827e-bbe508daab89.preview.emergentagent.com"
    api_base = f"{backend_url}/api"
    
    results = {}
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        
        # Test 1: Health Check
        logger.info("🏥 Testing Health Check...")
        try:
            async with session.get(f"{api_base}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check version
                    version = data.get("version", "")
                    logger.info(f"Version: {version}")
                    
                    # Check environment
                    environment = data.get("environment", "")
                    logger.info(f"Environment: {environment}")
                    
                    # Check AI models
                    ai_models = data.get("ai_models", {})
                    logger.info(f"AI Models: {ai_models}")
                    
                    # Check enhanced components
                    enhanced_components = data.get("enhanced_components", {})
                    logger.info(f"Enhanced Components: {enhanced_components}")
                    
                    # Check cache section
                    cache_section = data.get("cache", {})
                    logger.info(f"Cache Section: {cache_section}")
                    
                    # Check queue section
                    queue_section = data.get("queue", {})
                    logger.info(f"Queue Section: {queue_section}")
                    
                    # Check storage section
                    storage_section = data.get("storage", {})
                    logger.info(f"Storage Section: {storage_section}")
                    
                    results["health_check"] = {
                        "status": "PASS",
                        "version": version,
                        "environment": environment,
                        "has_cache_metrics": "hit_rate" in cache_section,
                        "has_queue_metrics": "completed_tasks" in queue_section,
                        "has_storage_metrics": "total_files" in storage_section
                    }
                else:
                    results["health_check"] = {"status": "FAIL", "http_status": response.status}
        except Exception as e:
            results["health_check"] = {"status": "ERROR", "error": str(e)}
        
        # Test 2: Voices Endpoint
        logger.info("🎤 Testing Voices Endpoint...")
        try:
            async with session.get(f"{api_base}/voices") as response:
                if response.status == 200:
                    data = await response.json()
                    coqui_voices = [v for v in data if v.get("voice_id", "").startswith("coqui_")]
                    results["voices"] = {
                        "status": "PASS",
                        "total_voices": len(data),
                        "coqui_voices": len(coqui_voices),
                        "has_coqui_voices": len(coqui_voices) > 0
                    }
                else:
                    results["voices"] = {"status": "FAIL", "http_status": response.status}
        except Exception as e:
            results["voices"] = {"status": "ERROR", "error": str(e)}
        
        # Test 3: WebSocket Endpoint
        logger.info("🔌 Testing WebSocket Endpoint...")
        try:
            # Just test if the endpoint exists (not actual WebSocket connection)
            ws_url = backend_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/test-connection"
            
            # Try to access the WebSocket endpoint via HTTP (should get 404 or upgrade error)
            async with session.get(f"{api_base}/ws/test-connection") as response:
                # WebSocket endpoints typically return 404 when accessed via HTTP
                if response.status == 404:
                    results["websocket"] = {"status": "FAIL", "error": "WebSocket endpoint not found (HTTP 404)"}
                else:
                    results["websocket"] = {"status": "UNKNOWN", "http_status": response.status}
        except Exception as e:
            results["websocket"] = {"status": "ERROR", "error": str(e)}
        
        # Test 4: Project Creation and Generation
        logger.info("🎬 Testing Video Generation Pipeline...")
        try:
            # Create project
            project_data = {
                "script": "A simple test for pipeline verification.",
                "aspect_ratio": "16:9",
                "voice_name": "default"
            }
            
            async with session.post(f"{api_base}/projects", json=project_data) as response:
                if response.status == 200:
                    project_result = await response.json()
                    project_id = project_result.get("project_id")
                    
                    if project_id:
                        # Start generation
                        generation_data = {
                            "project_id": project_id,
                            "script": "A simple test for pipeline verification.",
                            "aspect_ratio": "16:9"
                        }
                        
                        async with session.post(f"{api_base}/generate", json=generation_data) as gen_response:
                            if gen_response.status == 200:
                                gen_result = await gen_response.json()
                                generation_id = gen_result.get("generation_id")
                                
                                if generation_id:
                                    # Wait and check status
                                    await asyncio.sleep(5)
                                    
                                    async with session.get(f"{api_base}/generate/{generation_id}") as status_response:
                                        if status_response.status == 200:
                                            status_data = await status_response.json()
                                            results["pipeline"] = {
                                                "status": "PASS",
                                                "generation_started": True,
                                                "current_status": status_data.get("status", ""),
                                                "progress": status_data.get("progress", 0.0)
                                            }
                                        else:
                                            results["pipeline"] = {"status": "FAIL", "error": "Status check failed"}
                                else:
                                    results["pipeline"] = {"status": "FAIL", "error": "No generation_id returned"}
                            else:
                                error_text = await gen_response.text()
                                results["pipeline"] = {"status": "FAIL", "error": f"Generation failed: {error_text}"}
                    else:
                        results["pipeline"] = {"status": "FAIL", "error": "No project_id returned"}
                else:
                    results["pipeline"] = {"status": "FAIL", "error": "Project creation failed"}
        except Exception as e:
            results["pipeline"] = {"status": "ERROR", "error": str(e)}
    
    # Print Summary
    logger.info("\n" + "=" * 80)
    logger.info("🏭 QUICK PRODUCTION ASSESSMENT RESULTS")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = result.get("status", "UNKNOWN")
        if status == "PASS":
            logger.info(f"✅ {test_name.upper()}: {status}")
        elif status == "FAIL":
            logger.info(f"❌ {test_name.upper()}: {status} - {result.get('error', 'Unknown error')}")
        else:
            logger.info(f"⚠️  {test_name.upper()}: {status} - {result.get('error', 'Unknown issue')}")
    
    logger.info("\n📊 DETAILED FINDINGS:")
    
    # Health Check Details
    if "health_check" in results and results["health_check"]["status"] == "PASS":
        hc = results["health_check"]
        logger.info(f"   Version: {hc.get('version', 'Unknown')}")
        logger.info(f"   Environment: {hc.get('environment', 'Unknown')}")
        logger.info(f"   Cache Metrics Present: {hc.get('has_cache_metrics', False)}")
        logger.info(f"   Queue Metrics Present: {hc.get('has_queue_metrics', False)}")
        logger.info(f"   Storage Metrics Present: {hc.get('has_storage_metrics', False)}")
    
    # Voices Details
    if "voices" in results and results["voices"]["status"] == "PASS":
        v = results["voices"]
        logger.info(f"   Total Voices: {v.get('total_voices', 0)}")
        logger.info(f"   Coqui Voices: {v.get('coqui_voices', 0)}")
        logger.info(f"   Has Coqui Voices: {v.get('has_coqui_voices', False)}")
    
    # Pipeline Details
    if "pipeline" in results and results["pipeline"]["status"] == "PASS":
        p = results["pipeline"]
        logger.info(f"   Generation Started: {p.get('generation_started', False)}")
        logger.info(f"   Current Status: {p.get('current_status', 'Unknown')}")
        logger.info(f"   Progress: {p.get('progress', 0.0)}%")
    
    logger.info("=" * 80)
    
    return results

if __name__ == "__main__":
    asyncio.run(quick_assessment())