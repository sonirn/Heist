#!/usr/bin/env python3
"""
Complete Video Generation Pipeline Test
Tests the entire script-to-video process from start to finish
"""
import requests
import json
import time
import base64
import os
from datetime import datetime
import traceback

# Configuration
BACKEND_URL = "https://cb9b6811-3e2b-4ac5-b88c-17d26bae6a2c.preview.emergentagent.com"
TEST_SCRIPTS = [
    {
        "name": "Simple Script Test",
        "script": "A person walking in a sunny park. The weather is beautiful and birds are singing.",
        "expected_scenes": 1,
        "expected_duration": 10
    },
    {
        "name": "Multi-Character Script Test", 
        "script": "John: Hello, how are you today? Mary: I'm doing great, thanks for asking! The sun is shining and it's a beautiful day. John: That's wonderful to hear. Let's go for a walk in the park.",
        "expected_scenes": 2,
        "expected_duration": 20
    },
    {
        "name": "Hindi Script Test",
        "script": "राम: आज कैसा दिन है? सीता: बहुत अच्छा दिन है। सूरज चमक रहा है और पक्षी गा रहे हैं। राम: चलो पार्क में सैर करते हैं।",
        "expected_scenes": 2,
        "expected_duration": 15
    }
]

class VideoGenerationTester:
    def __init__(self):
        self.results = []
        self.current_test = None
        self.start_time = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_health_check(self):
        """Test backend health and component status"""
        self.log("Testing backend health check...")
        try:
            response = requests.get(f"{BACKEND_URL}/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"✅ Backend healthy - Version: {health_data.get('version', 'unknown')}")
                
                # Check enhanced components
                enhanced_components = [
                    'gemini_supervisor', 'runwayml_processor', 'multi_voice_manager'
                ]
                for component in enhanced_components:
                    status = health_data.get(component, False)
                    if status:
                        self.log(f"✅ {component}: operational")
                    else:
                        self.log(f"❌ {component}: not operational", "ERROR")
                        
                # Check AI models
                ai_models = health_data.get('ai_models', {})
                for model, status in ai_models.items():
                    self.log(f"🤖 {model}: {status}")
                    
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {str(e)}", "ERROR")
            return False
            
    def test_voices_endpoint(self):
        """Test enhanced voice system"""
        self.log("Testing enhanced voice system...")
        try:
            response = requests.get(f"{BACKEND_URL}/api/voices", timeout=10)
            if response.status_code == 200:
                voices = response.json()
                total_voices = len(voices)
                hindi_voices = [v for v in voices if 'hindi' in v.get('voice_id', '').lower()]
                coqui_voices = [v for v in voices if 'coqui' in v.get('voice_id', '').lower()]
                
                self.log(f"✅ Total voices available: {total_voices}")
                self.log(f"✅ Hindi voices: {len(hindi_voices)}")
                self.log(f"✅ Coqui voices: {len(coqui_voices)}")
                
                # Check for minimum required Hindi voices
                if len(hindi_voices) >= 6:
                    self.log("✅ Hindi voice requirement met (6+ voices)")
                else:
                    self.log(f"❌ Hindi voice requirement not met ({len(hindi_voices)} < 6)", "ERROR")
                    
                return True
            else:
                self.log(f"❌ Voices endpoint failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Voices endpoint error: {str(e)}", "ERROR")
            return False
            
    def create_project(self, script_name, script_content):
        """Create a new video generation project"""
        self.log(f"Creating project for '{script_name}'...")
        try:
            payload = {
                "script": script_content,
                "aspect_ratio": "16:9"
            }
            
            response = requests.post(f"{BACKEND_URL}/api/projects", 
                                   json=payload, 
                                   timeout=30)
            
            if response.status_code == 200:
                project_data = response.json()
                generation_id = project_data.get('generation_id') or project_data.get('project_id')
                self.log(f"✅ Project created: {generation_id}")
                return generation_id
            else:
                self.log(f"❌ Project creation failed: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"❌ Project creation error: {str(e)}", "ERROR")
            return None
            
    def start_generation(self, generation_id):
        """Start video generation process"""
        self.log(f"Starting video generation for {generation_id}...")
        try:
            response = requests.post(f"{BACKEND_URL}/api/generate/{generation_id}", 
                                   timeout=30)
            
            if response.status_code == 200:
                self.log("✅ Video generation started successfully")
                return True
            else:
                self.log(f"❌ Generation start failed: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Generation start error: {str(e)}", "ERROR")
            return False
            
    def monitor_progress(self, generation_id, max_wait_seconds=600):
        """Monitor video generation progress"""
        self.log(f"Monitoring progress for {generation_id}...")
        start_time = time.time()
        last_progress = -1
        stuck_count = 0
        max_stuck_count = 10
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = requests.get(f"{BACKEND_URL}/api/generate/{generation_id}", 
                                      timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    progress = data.get('progress', 0)
                    status = data.get('status', 'unknown')
                    message = data.get('message', '')
                    
                    # Check for progress updates
                    if progress != last_progress:
                        self.log(f"📊 Progress: {progress}% | Status: {status} | {message}")
                        last_progress = progress
                        stuck_count = 0
                    else:
                        stuck_count += 1
                        if stuck_count >= max_stuck_count:
                            self.log(f"⚠️ Progress stuck at {progress}% for {stuck_count} checks", "WARNING")
                    
                    # Check completion
                    if status == 'completed' and progress == 100:
                        self.log("✅ Video generation completed successfully!")
                        return True, data
                    elif status == 'failed':
                        self.log(f"❌ Video generation failed: {message}", "ERROR")
                        return False, data
                    elif progress >= 95 and stuck_count >= max_stuck_count:
                        self.log(f"🚨 CRITICAL: Progress stuck at {progress}% - this is the known issue!", "ERROR")
                        # Check if video was actually generated despite stuck progress
                        return "stuck_at_95", data
                        
                else:
                    self.log(f"❌ Progress check failed: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Progress monitoring error: {str(e)}", "ERROR")
                
            time.sleep(5)  # Wait 5 seconds between checks
            
        self.log(f"⏰ Timeout after {max_wait_seconds} seconds", "ERROR")
        return False, None
        
    def test_download(self, generation_id):
        """Test video download functionality"""
        self.log(f"Testing video download for {generation_id}...")
        try:
            response = requests.get(f"{BACKEND_URL}/api/download/{generation_id}", 
                                  timeout=30)
            
            if response.status_code == 200:
                content_length = len(response.content)
                self.log(f"✅ Video downloaded successfully: {content_length} bytes")
                
                # Save the video for inspection
                video_path = f"/tmp/test_video_{generation_id}.mp4"
                with open(video_path, 'wb') as f:
                    f.write(response.content)
                self.log(f"✅ Video saved to: {video_path}")
                
                return True, content_length
            else:
                self.log(f"❌ Download failed: {response.status_code}", "ERROR")
                return False, 0
        except Exception as e:
            self.log(f"❌ Download error: {str(e)}", "ERROR")
            return False, 0
            
    def test_complete_pipeline(self, test_script):
        """Test complete video generation pipeline"""
        self.log(f"\n{'='*60}")
        self.log(f"TESTING: {test_script['name']}")
        self.log(f"Script: {test_script['script'][:100]}...")
        self.log(f"{'='*60}")
        
        test_result = {
            "name": test_script['name'],
            "script": test_script['script'],
            "success": False,
            "steps": {},
            "issues": [],
            "video_generated": False,
            "downloadable": False,
            "progress_stuck": False,
            "final_progress": 0
        }
        
        # Step 1: Create project
        generation_id = self.create_project(test_script['name'], test_script['script'])
        test_result['steps']['project_creation'] = generation_id is not None
        
        if not generation_id:
            test_result['issues'].append("Project creation failed")
            return test_result
            
        test_result['generation_id'] = generation_id
        
        # Step 2: Start generation
        generation_started = self.start_generation(generation_id)
        test_result['steps']['generation_start'] = generation_started
        
        if not generation_started:
            test_result['issues'].append("Generation start failed")
            return test_result
            
        # Step 3: Monitor progress
        progress_result, final_data = self.monitor_progress(generation_id)
        test_result['steps']['progress_monitoring'] = progress_result
        
        if final_data:
            test_result['final_progress'] = final_data.get('progress', 0)
            test_result['final_status'] = final_data.get('status', 'unknown')
            test_result['final_message'] = final_data.get('message', '')
            
        if progress_result == "stuck_at_95":
            test_result['progress_stuck'] = True
            test_result['issues'].append("Progress stuck at 95% - known critical issue")
            # Still try to download as videos might be generated
            
        elif not progress_result:
            test_result['issues'].append("Progress monitoring failed or timed out")
            
        # Step 4: Test download (always try, even if progress stuck)
        download_success, video_size = self.test_download(generation_id)
        test_result['steps']['download'] = download_success
        test_result['video_size'] = video_size
        
        if download_success:
            test_result['video_generated'] = True
            test_result['downloadable'] = True
            if video_size > 50000:  # At least 50KB indicates real video
                self.log("✅ Video appears to be substantial (>50KB)")
            else:
                self.log("⚠️ Video file is very small, might be placeholder", "WARNING")
                
        # Overall success determination
        if test_result['video_generated'] and test_result['downloadable']:
            if test_result['progress_stuck']:
                self.log("⚠️ PARTIAL SUCCESS: Video generated but progress monitoring stuck", "WARNING")
                test_result['success'] = "partial"
            else:
                self.log("✅ COMPLETE SUCCESS: Full pipeline working")
                test_result['success'] = True
        else:
            self.log("❌ FAILED: No video generated or downloadable", "ERROR")
            test_result['success'] = False
            
        return test_result
        
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        self.log("Starting comprehensive video generation pipeline test")
        self.log(f"Backend URL: {BACKEND_URL}")
        self.log(f"Test Scripts: {len(TEST_SCRIPTS)}")
        
        self.start_time = time.time()
        
        # Prerequisites
        self.log("\n🔧 TESTING PREREQUISITES")
        health_ok = self.test_health_check()
        voices_ok = self.test_voices_endpoint()
        
        if not health_ok or not voices_ok:
            self.log("❌ Prerequisites failed - aborting tests", "ERROR")
            return
            
        # Pipeline tests
        self.log("\n🎬 TESTING VIDEO GENERATION PIPELINE")
        
        for test_script in TEST_SCRIPTS:
            try:
                result = self.test_complete_pipeline(test_script)
                self.results.append(result)
                
                # Brief summary
                if result['success'] == True:
                    self.log(f"✅ {result['name']}: PASSED")
                elif result['success'] == "partial":
                    self.log(f"⚠️ {result['name']}: PARTIAL (video generated but progress stuck)")
                else:
                    self.log(f"❌ {result['name']}: FAILED")
                    
            except Exception as e:
                self.log(f"❌ Test '{test_script['name']}' crashed: {str(e)}", "ERROR")
                self.log(traceback.format_exc(), "DEBUG")
                
        # Generate final report
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate comprehensive final report"""
        total_time = time.time() - self.start_time
        
        self.log("\n" + "="*80)
        self.log("FINAL COMPREHENSIVE REPORT")
        self.log("="*80)
        
        # Summary statistics
        total_tests = len(self.results)
        full_success = sum(1 for r in self.results if r['success'] == True)
        partial_success = sum(1 for r in self.results if r['success'] == "partial")
        failed = sum(1 for r in self.results if r['success'] == False)
        
        self.log(f"📊 STATISTICS:")
        self.log(f"   Total Tests: {total_tests}")
        self.log(f"   Full Success: {full_success}")
        self.log(f"   Partial Success: {partial_success}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Total Time: {total_time:.1f} seconds")
        
        # Success rate
        success_rate = ((full_success + partial_success) / total_tests * 100) if total_tests > 0 else 0
        self.log(f"   Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        self.log(f"\n📋 DETAILED RESULTS:")
        for result in self.results:
            self.log(f"\n--- {result['name']} ---")
            self.log(f"   Status: {result['success']}")
            self.log(f"   Generation ID: {result.get('generation_id', 'N/A')}")
            self.log(f"   Video Generated: {result['video_generated']}")
            self.log(f"   Downloadable: {result['downloadable']}")
            self.log(f"   Final Progress: {result['final_progress']}%")
            self.log(f"   Video Size: {result.get('video_size', 0)} bytes")
            
            if result['progress_stuck']:
                self.log(f"   ⚠️ Progress Stuck: YES")
                
            if result['issues']:
                self.log(f"   Issues: {', '.join(result['issues'])}")
                
        # Critical issues summary
        all_issues = []
        for result in self.results:
            all_issues.extend(result['issues'])
            
        unique_issues = list(set(all_issues))
        
        self.log(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
        if unique_issues:
            for issue in unique_issues:
                count = all_issues.count(issue)
                self.log(f"   - {issue} ({count} occurrences)")
        else:
            self.log("   No critical issues found!")
            
        # Recommendations
        self.log(f"\n💡 RECOMMENDATIONS:")
        
        stuck_count = sum(1 for r in self.results if r['progress_stuck'])
        if stuck_count > 0:
            self.log(f"   1. FIX CRITICAL: Progress monitoring stuck at 95% affects {stuck_count} tests")
            self.log(f"      - Videos are being generated but progress doesn't complete")
            self.log(f"      - Check Minimax API balance and error handling")
            self.log(f"      - Review progress tracking logic in backend/server.py")
            
        if partial_success > 0:
            self.log(f"   2. IMPROVE: {partial_success} tests show partial success")
            self.log(f"      - Core functionality works but has monitoring issues")
            
        if failed > 0:
            self.log(f"   3. URGENT: {failed} tests completely failed")
            self.log(f"      - Investigate root causes in backend logs")
            
        self.log(f"\n✨ SYSTEM STATUS: {'PRODUCTION READY' if success_rate >= 80 else 'NEEDS FIXES'}")
        
if __name__ == "__main__":
    tester = VideoGenerationTester()
    tester.run_all_tests()