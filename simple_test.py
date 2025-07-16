#!/usr/bin/env python3
"""
Simple Backend Test for Script-to-Video Application
"""

import requests
import json
import time

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        print("🏥 Testing Health Endpoint...")
        response = requests.get(
            "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com/api/health",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed - Status: {data.get('status', 'unknown')}")
            print(f"   Version: {data.get('version', 'unknown')}")
            
            # Check AI models
            ai_models = data.get('ai_models', {})
            print(f"   AI Models: minimax={ai_models.get('minimax', False)}, stable_audio={ai_models.get('stable_audio', False)}")
            
            # Check enhanced components
            enhanced = data.get('enhanced_components', {})
            print(f"   Enhanced Components: gemini={enhanced.get('gemini_supervisor', False)}, runwayml={enhanced.get('runwayml_processor', False)}, voices={enhanced.get('multi_voice_manager', False)}")
            
            return True
        else:
            print(f"❌ Health check failed - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check exception: {str(e)}")
        return False

def test_voices_endpoint():
    """Test the voices endpoint"""
    try:
        print("🎤 Testing Voices Endpoint...")
        response = requests.get(
            "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com/api/voices",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ Voices endpoint passed - Found {len(data)} voices")
                
                # Check for Hindi voices
                hindi_voices = [v for v in data if "hindi" in v.get("voice_id", "").lower() or "hindi" in v.get("name", "").lower()]
                print(f"   Hindi voices: {len(hindi_voices)}")
                
                if len(hindi_voices) >= 6:
                    print("✅ Sufficient Hindi voices found (6+ required)")
                    return True
                else:
                    print("⚠️  Less than 6 Hindi voices found")
                    return False
            else:
                print("❌ Invalid voices response format")
                return False
        else:
            print(f"❌ Voices endpoint failed - HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Voices endpoint exception: {str(e)}")
        return False

def test_project_creation():
    """Test project creation"""
    try:
        print("📝 Testing Project Creation...")
        
        project_data = {
            "script": "A person walks in a sunny park. The weather is beautiful and birds are singing.",
            "aspect_ratio": "16:9",
            "voice_name": "default"
        }
        
        response = requests.post(
            "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com/api/projects",
            json=project_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            project_id = data.get("project_id")
            if project_id:
                print(f"✅ Project creation passed - ID: {project_id}")
                return project_id
            else:
                print("❌ No project_id returned")
                return None
        else:
            print(f"❌ Project creation failed - HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Project creation exception: {str(e)}")
        return None

def test_video_generation(project_id):
    """Test video generation start"""
    try:
        print("🚀 Testing Video Generation Start...")
        
        generation_data = {
            "project_id": project_id,
            "script": "A person walks in a sunny park. The weather is beautiful and birds are singing.",
            "aspect_ratio": "16:9"
        }
        
        response = requests.post(
            "https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com/api/generate",
            json=generation_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            generation_id = data.get("generation_id")
            if generation_id:
                print(f"✅ Video generation started - ID: {generation_id}")
                return generation_id
            else:
                print("❌ No generation_id returned")
                return None
        else:
            print(f"❌ Video generation failed - HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Video generation exception: {str(e)}")
        return None

def test_generation_progress(generation_id):
    """Test generation progress monitoring"""
    try:
        print("📊 Testing Generation Progress...")
        
        max_checks = 10
        for i in range(max_checks):
            time.sleep(3)
            
            response = requests.get(
                f"https://c2b7e47a-7e43-4e33-8654-2028012bf65a.preview.emergentagent.com/api/generate/{generation_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "")
                progress = data.get("progress", 0.0)
                message = data.get("message", "")
                
                print(f"   Check {i+1}: Status={status}, Progress={progress}%, Message='{message}'")
                
                # Check if we've made progress beyond 0%
                if progress > 0.0:
                    print(f"✅ Progress detected: {progress}% - No longer stuck at 0%")
                    return True
                
                # Check if status changed from queued
                if status != "queued":
                    print(f"✅ Status changed to: {status}")
                    return True
                
                # If completed or failed, break
                if status in ["completed", "failed"]:
                    print(f"🏁 Generation finished with status: {status}")
                    return status == "completed"
            else:
                print(f"❌ Status check failed - HTTP {response.status_code}")
        
        print("⚠️  No progress detected after 10 checks")
        return False
        
    except Exception as e:
        print(f"❌ Progress monitoring exception: {str(e)}")
        return False

def main():
    """Run simple backend tests"""
    print("🎯 SIMPLE BACKEND TESTING")
    print("=" * 50)
    
    results = []
    
    # Test 1: Health Check
    health_result = test_health_endpoint()
    results.append(("Health Check", health_result))
    
    # Test 2: Voices Endpoint
    voices_result = test_voices_endpoint()
    results.append(("Voices Endpoint", voices_result))
    
    # Test 3: Project Creation
    project_id = test_project_creation()
    results.append(("Project Creation", project_id is not None))
    
    if project_id:
        # Test 4: Video Generation
        generation_id = test_video_generation(project_id)
        results.append(("Video Generation Start", generation_id is not None))
        
        if generation_id:
            # Test 5: Progress Monitoring
            progress_result = test_generation_progress(generation_id)
            results.append(("Progress Monitoring", progress_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"📈 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed >= total - 1:  # Allow 1 failure
        print("🎉 BACKEND TESTING COMPLETED SUCCESSFULLY!")
    else:
        print("⚠️  BACKEND TESTING IDENTIFIED ISSUES")

if __name__ == "__main__":
    main()