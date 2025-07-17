#!/usr/bin/env python3
"""
Robust Video Generation Test with Timeout Handling
"""
import requests
import json
import time
import base64
import os
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = "http://localhost:8001"

class RobustVideoTester:
    def __init__(self):
        self.results = []
        self.start_time = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_single_video_generation(self, script_name, script_content):
        """Test a single video generation with robust error handling"""
        self.log(f"\n🎬 TESTING: {script_name}")
        self.log(f"Script: {script_content[:100]}...")
        
        result = {
            "name": script_name,
            "script": script_content,
            "steps": {},
            "issues": [],
            "progress_updates": [],
            "final_status": "unknown"
        }
        
        try:
            # Step 1: Create project
            self.log("📝 Creating project...")
            payload = {"script": script_content, "aspect_ratio": "16:9"}
            response = requests.post(f"{BACKEND_URL}/api/projects", json=payload, timeout=30)
            
            if response.status_code != 200:
                result['issues'].append(f"Project creation failed: {response.status_code}")
                return result
                
            project_data = response.json()
            project_id = project_data.get('project_id')
            result['project_id'] = project_id
            result['steps']['project_creation'] = True
            self.log(f"✅ Project created: {project_id}")
            
            # Step 2: Start generation
            self.log("🚀 Starting video generation...")
            gen_payload = {
                "project_id": project_id,
                "script": script_content,
                "aspect_ratio": "16:9"
            }
            response = requests.post(f"{BACKEND_URL}/api/generate", json=gen_payload, timeout=30)
            
            if response.status_code != 200:
                result['issues'].append(f"Generation start failed: {response.status_code}")
                return result
                
            gen_data = response.json()
            generation_id = gen_data.get('generation_id')
            result['generation_id'] = generation_id
            result['steps']['generation_start'] = True
            self.log(f"✅ Generation started: {generation_id}")
            
            # Step 3: Monitor progress with robust timeout handling
            self.log("📊 Monitoring progress...")
            progress_success = self.monitor_progress_robust(generation_id, result)
            result['steps']['progress_monitoring'] = progress_success
            
            # Step 4: Test download
            self.log("⬇️ Testing download...")
            download_success, video_size = self.test_download(generation_id)
            result['steps']['download'] = download_success
            result['video_size'] = video_size
            
            if download_success:
                result['final_status'] = "success"
                self.log(f"✅ SUCCESS: Video generated and downloadable ({video_size} bytes)")
            else:
                result['final_status'] = "failed"
                self.log("❌ FAILED: Video not downloadable")
                
        except Exception as e:
            result['issues'].append(f"Test crashed: {str(e)}")
            result['final_status'] = "error"
            self.log(f"❌ ERROR: {str(e)}")
            
        return result
        
    def monitor_progress_robust(self, generation_id, result):
        """Monitor progress with robust timeout and error handling"""
        start_time = time.time()
        max_duration = 300  # 5 minutes max
        last_progress = -1
        timeout_count = 0
        max_timeouts = 5
        
        while time.time() - start_time < max_duration:
            try:
                response = requests.get(f"{BACKEND_URL}/api/generate/{generation_id}", timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    message = data.get('message', '')
                    
                    # Log progress updates
                    if progress != last_progress:
                        self.log(f"📊 {progress}% | {status} | {message}")
                        result['progress_updates'].append({
                            'progress': progress,
                            'status': status,
                            'message': message,
                            'timestamp': time.time() - start_time
                        })
                        last_progress = progress
                        timeout_count = 0  # Reset timeout count on successful update
                    
                    # Check completion
                    if status == 'completed' and progress == 100:
                        self.log("✅ Generation completed successfully!")
                        return True
                    elif status == 'failed':
                        self.log(f"❌ Generation failed: {message}")
                        return False
                    elif progress >= 95:
                        self.log(f"⚠️ Progress at {progress}% - checking for stuck progress...")
                        # Give it more time at 95%+ since this is a known issue
                        if time.time() - start_time > 120:  # If stuck for 2+ minutes
                            self.log("🚨 Progress appears stuck at 95%+, checking if video exists...")
                            return "stuck_but_checking"
                            
                else:
                    self.log(f"⚠️ Progress check failed: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                timeout_count += 1
                self.log(f"⏳ Timeout #{timeout_count} during progress check")
                if timeout_count >= max_timeouts:
                    self.log("🚨 Too many timeouts, but continuing to check download...")
                    return "timeout_but_continuing"
                    
            except Exception as e:
                self.log(f"⚠️ Progress check error: {str(e)}")
                
            time.sleep(8)  # Wait between checks
            
        self.log("⏰ Progress monitoring timed out")
        return False
        
    def test_download(self, generation_id):
        """Test video download with multiple attempts"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.log(f"⬇️ Download attempt {attempt + 1}/{max_attempts}")
                response = requests.get(f"{BACKEND_URL}/api/download/{generation_id}", timeout=30)
                
                if response.status_code == 200:
                    content_length = len(response.content)
                    if content_length > 1000:  # At least 1KB
                        # Save the video
                        video_path = f"/tmp/test_video_{generation_id}.mp4"
                        with open(video_path, 'wb') as f:
                            f.write(response.content)
                        return True, content_length
                    else:
                        self.log(f"⚠️ Video too small: {content_length} bytes")
                        
                else:
                    self.log(f"⚠️ Download failed: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Download error: {str(e)}")
                
            if attempt < max_attempts - 1:
                time.sleep(10)  # Wait before retry
                
        return False, 0
        
    def run_comprehensive_test(self):
        """Run comprehensive test with multiple scenarios"""
        self.log("🎯 STARTING COMPREHENSIVE VIDEO GENERATION TEST")
        self.log("=" * 60)
        
        # Test scripts
        test_scripts = [
            ("Simple Script", "A person walking in a sunny park. The weather is beautiful and birds are singing."),
            ("Multi-Character", "John: Hello, how are you? Mary: I'm doing great, thanks! Let's go for a walk."),
            ("Hindi Script", "राम: आज कैसा दिन है? सीता: बहुत अच्छा दिन है।")
        ]
        
        results = []
        
        for script_name, script_content in test_scripts:
            result = self.test_single_video_generation(script_name, script_content)
            results.append(result)
            
            # Summary for this test
            if result['final_status'] == 'success':
                self.log(f"✅ {script_name}: PASSED")
            else:
                self.log(f"❌ {script_name}: {result['final_status'].upper()}")
                
        # Final comprehensive report
        self.generate_comprehensive_report(results)
        
    def generate_comprehensive_report(self, results):
        """Generate final comprehensive report"""
        self.log("\n" + "=" * 80)
        self.log("📋 COMPREHENSIVE FINAL REPORT")
        self.log("=" * 80)
        
        # Statistics
        total_tests = len(results)
        successful = sum(1 for r in results if r['final_status'] == 'success')
        failed = sum(1 for r in results if r['final_status'] == 'failed')
        errors = sum(1 for r in results if r['final_status'] == 'error')
        
        self.log(f"📊 TEST STATISTICS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Successful: {successful}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Errors: {errors}")
        self.log(f"   Success Rate: {(successful/total_tests*100):.1f}%")
        
        # Detailed results
        self.log(f"\n📋 DETAILED RESULTS:")
        for result in results:
            self.log(f"\n--- {result['name']} ---")
            self.log(f"   Final Status: {result['final_status']}")
            self.log(f"   Project ID: {result.get('project_id', 'N/A')}")
            self.log(f"   Generation ID: {result.get('generation_id', 'N/A')}")
            self.log(f"   Video Size: {result.get('video_size', 0)} bytes")
            
            # Steps summary
            steps = result.get('steps', {})
            self.log(f"   Steps: Project Creation: {steps.get('project_creation', False)}, " +
                   f"Generation Start: {steps.get('generation_start', False)}, " +
                   f"Progress Monitoring: {steps.get('progress_monitoring', False)}, " +
                   f"Download: {steps.get('download', False)}")
            
            # Progress updates
            progress_updates = result.get('progress_updates', [])
            if progress_updates:
                self.log(f"   Progress Updates: {len(progress_updates)} updates")
                for update in progress_updates[-3:]:  # Show last 3 updates
                    self.log(f"      {update['progress']}% | {update['status']} | {update['message']}")
                    
            # Issues
            if result.get('issues'):
                self.log(f"   Issues: {', '.join(result['issues'])}")
                
        # Key findings
        self.log(f"\n🔍 KEY FINDINGS:")
        
        # Check for common issues
        progress_issues = [r for r in results if any('95%' in str(issue) for issue in r.get('issues', []))]
        if progress_issues:
            self.log(f"   - Progress stuck at 95%: {len(progress_issues)} tests affected")
            
        timeout_issues = [r for r in results if any('timeout' in str(issue).lower() for issue in r.get('issues', []))]
        if timeout_issues:
            self.log(f"   - Timeout issues: {len(timeout_issues)} tests affected")
            
        # Check success patterns
        if successful > 0:
            self.log(f"   - {successful} tests completed successfully with video generation")
            
        # System status
        if successful == total_tests:
            self.log(f"\n✅ SYSTEM STATUS: FULLY OPERATIONAL")
        elif successful > 0:
            self.log(f"\n⚠️ SYSTEM STATUS: PARTIALLY OPERATIONAL ({successful}/{total_tests} working)")
        else:
            self.log(f"\n❌ SYSTEM STATUS: NEEDS CRITICAL FIXES")
            
        self.log("=" * 80)

if __name__ == "__main__":
    tester = RobustVideoTester()
    tester.run_comprehensive_test()