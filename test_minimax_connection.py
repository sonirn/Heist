#!/usr/bin/env python3
"""
Test script to verify Minimax API connection
"""
import sys
import os
sys.path.append('/app')

from ai_models_real import MinimaxVideoGenerator
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_minimax_connection():
    """Test Minimax API connection"""
    print("Testing Minimax API connection...")
    
    # Initialize the generator
    generator = MinimaxVideoGenerator()
    
    # Load the model (test connection)
    success = generator.load_model()
    print(f"Model loading success: {success}")
    
    # Get model info
    info = generator.get_model_info()
    print(f"Model info: {info}")
    
    # Test API connection
    connection_test = generator._test_api_connection()
    print(f"API connection test: {connection_test}")
    
    if connection_test:
        print("✅ Minimax API connection successful!")
        print(f"Development mode: {generator.development_mode}")
        print(f"API key present: {bool(generator.api_key)}")
    else:
        print("❌ Minimax API connection failed!")
        print("Running in development mode")
        
    return connection_test

if __name__ == "__main__":
    test_minimax_connection()