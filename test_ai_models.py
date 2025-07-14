#!/usr/bin/env python3
"""
Test script for AI models deployed on server
"""
import os
import sys
import torch
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stable_audio():
    """Test Stable Audio Open model"""
    logger.info("Testing Stable Audio Open...")
    try:
        from stable_audio_tools import get_pretrained_model
        from stable_audio_tools.inference.generation import generate_diffusion_cond
        
        # Test with smaller model or CPU fallback
        logger.info("Device: %s", torch.device("cpu"))
        logger.info("Stable Audio Open: Available")
        return True
    except Exception as e:
        logger.error("Stable Audio Open error: %s", str(e))
        return False

def test_wan21():
    """Test Wan 2.1 model"""
    logger.info("Testing Wan 2.1...")
    try:
        import wan
        from wan import text2video
        
        logger.info("Wan 2.1: Available")
        return True
    except Exception as e:
        logger.error("Wan 2.1 error: %s", str(e))
        return False

def test_torch_capabilities():
    """Test PyTorch capabilities"""
    logger.info("Testing PyTorch capabilities...")
    
    # Check device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)
    
    # Check if we can create tensors
    try:
        x = torch.randn(2, 3)
        logger.info("CPU tensor creation: OK")
    except Exception as e:
        logger.error("CPU tensor creation failed: %s", str(e))
        return False
    
    # Check memory
    import psutil
    memory = psutil.virtual_memory()
    logger.info("Available memory: %.2f GB", memory.available / (1024**3))
    
    return True

def main():
    """Main test function"""
    logger.info("Starting AI models test...")
    
    # Test basic capabilities
    torch_ok = test_torch_capabilities()
    
    # Test models
    stable_audio_ok = test_stable_audio()
    wan21_ok = test_wan21()
    
    logger.info("\n=== Test Results ===")
    logger.info("PyTorch: %s", "OK" if torch_ok else "FAILED")
    logger.info("Stable Audio Open: %s", "OK" if stable_audio_ok else "FAILED")
    logger.info("Wan 2.1: %s", "OK" if wan21_ok else "FAILED")
    
    if torch_ok and stable_audio_ok and wan21_ok:
        logger.info("All tests passed! Ready for deployment.")
        return 0
    else:
        logger.error("Some tests failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())