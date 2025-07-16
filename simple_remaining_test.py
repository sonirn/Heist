#!/usr/bin/env python3
"""
Simple test for remaining issues
"""

import requests
import json

def test_health_endpoint():
    """Test health endpoint for missing metrics"""
    print("🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get(
            "https://b51ec283-200b-4c5a-8885-425b20225bca.preview.emergentagent.com/api/health",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint responded: {response.status_code}")
            
            # Check for required sections
            sections = ["cache", "queue", "storage"]
            for section in sections:
                if section in data:
                    print(f"✅ {section} section present: {list(data[section].keys())}")
                else:
                    print(f"❌ {section} section missing")
            
            # Check storage structure specifically
            if "storage" in data:
                storage = data["storage"]
                required_fields = ["total_files", "total_size", "cleanup_enabled"]
                
                for field in required_fields:
                    if field in storage:
                        print(f"✅ storage.{field} present: {storage[field]}")
                    else:
                        print(f"❌ storage.{field} missing")
                        
                        # Check if in summary
                        if "summary" in storage and field in storage["summary"]:
                            print(f"⚠️  storage.{field} found in summary: {storage['summary'][field]}")
            
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint error: {str(e)}")
        return False

def test_websocket_endpoints():
    """Test WebSocket endpoints via HTTP"""
    print("\n🔌 Testing WebSocket Endpoints...")
    
    endpoints = [
        "/api/ws/test-generation-123",
        "/api/ws/test"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            url = f"https://b51ec283-200b-4c5a-8885-425b20225bca.preview.emergentagent.com{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 404:
                print(f"❌ {endpoint} returns 404 - not configured")
                results.append(False)
            else:
                print(f"✅ {endpoint} configured (status: {response.status_code})")
                results.append(True)
                
        except Exception as e:
            print(f"❌ {endpoint} error: {str(e)}")
            results.append(False)
    
    return all(results)

def test_basic_api():
    """Test basic API functionality"""
    print("\n🎬 Testing Basic API...")
    
    try:
        # Test project creation
        project_data = {
            "script": "A simple test script for API testing.",
            "aspect_ratio": "16:9",
            "voice_name": "default"
        }
        
        response = requests.post(
            "https://b51ec283-200b-4c5a-8885-425b20225bca.preview.emergentagent.com/api/projects",
            json=project_data,
            timeout=10
        )
        
        if response.status_code == 200:
            project_result = response.json()
            project_id = project_result.get("project_id")
            print(f"✅ Project creation successful: {project_id}")
            
            # Test generation start
            generation_data = {
                "project_id": project_id,
                "script": project_data["script"],
                "aspect_ratio": "16:9"
            }
            
            response = requests.post(
                "https://b51ec283-200b-4c5a-8885-425b20225bca.preview.emergentagent.com/api/generate",
                json=generation_data,
                timeout=10
            )
            
            if response.status_code == 200:
                generation_result = response.json()
                generation_id = generation_result.get("generation_id")
                print(f"✅ Generation start successful: {generation_id}")
                return True
            else:
                print(f"❌ Generation start failed: {response.status_code}")
                return False
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Basic API error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🎯 RUNNING SIMPLE TESTS FOR REMAINING ISSUES")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health endpoint metrics
    results["health_metrics"] = test_health_endpoint()
    
    # Test 2: WebSocket endpoints
    results["websocket_endpoints"] = test_websocket_endpoints()
    
    # Test 3: Basic API functionality
    results["basic_api"] = test_basic_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    passed = sum(results.values())
    total = len(results)
    print(f"\n📈 Final Score: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total-passed} issues remaining")

if __name__ == "__main__":
    main()