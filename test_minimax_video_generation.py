#!/usr/bin/env python3
"""
Test script to verify Minimax API video generation
"""
import sys
import os
sys.path.append('/app')

from ai_models_real import MinimaxVideoGenerator
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv('/app/backend/.env')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minimax_video_generation():
    """Test Minimax API video generation"""
    print("Testing Minimax API video generation...")
    
    # Initialize the generator
    generator = MinimaxVideoGenerator()
    
    # Load the model
    success = generator.load_model()
    print(f"Model loading success: {success}")
    print(f"Development mode: {generator.development_mode}")
    
    if generator.development_mode:
        print("⚠️  Running in development mode - will generate synthetic video")
    else:
        print("✅ Running in production mode - will use real Minimax API")
    
    # Test video generation with a simple prompt
    print("\nTesting video generation with prompt: 'A sunset over mountains'")
    
    try:
        video_data = generator.generate_video(
            prompt="A sunset over mountains",
            aspect_ratio="16:9",
            duration=3.0
        )
        
        if video_data:
            print(f"✅ Video generation successful! Generated {len(video_data)} bytes")
            
            # Save the video for testing
            with open('/app/test_video.mp4', 'wb') as f:
                f.write(video_data)
            print("Video saved as test_video.mp4")
        else:
            print("❌ Video generation failed!")
            
    except Exception as e:
        print(f"❌ Video generation error: {e}")
        
    return video_data is not None

if __name__ == "__main__":
    test_minimax_video_generation()