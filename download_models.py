#!/usr/bin/env python3
"""
Model Download Script for WAN 2.1 and Stable Audio Open
Downloads and sets up the actual model weights for production use
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_directory(path: str) -> bool:
    """Create directory if it doesn't exist"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def download_wan21_model():
    """Download WAN 2.1 T2B 1.3B model from HuggingFace"""
    logger.info("Starting WAN 2.1 T2B 1.3B model download...")
    
    model_path = "/app/models/Wan2.1-T2V-1.3B"
    
    # Create models directory
    if not create_directory(model_path):
        return False
    
    try:
        # Use git to clone the repository
        logger.info(f"Cloning WAN 2.1 model to {model_path}")
        
        # Remove existing directory if it exists
        if os.path.exists(model_path):
            shutil.rmtree(model_path)
            
        # Clone the repository
        result = subprocess.run([
            "git", "clone", 
            "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B", 
            model_path
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info("WAN 2.1 T2B 1.3B model downloaded successfully!")
            
            # Check if essential files exist
            essential_files = [
                "config.json",
                "model_index.json",
                "scheduler/scheduler_config.json"
            ]
            
            for file in essential_files:
                file_path = os.path.join(model_path, file)
                if os.path.exists(file_path):
                    logger.info(f"✓ Found {file}")
                else:
                    logger.warning(f"✗ Missing {file}")
                    
            return True
        else:
            logger.error(f"Failed to download WAN 2.1 model: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("WAN 2.1 model download timed out")
        return False
    except Exception as e:
        logger.error(f"Error downloading WAN 2.1 model: {e}")
        return False

def download_stable_audio_model():
    """Download Stable Audio Open model from HuggingFace"""
    logger.info("Starting Stable Audio Open model download...")
    
    model_path = "/app/models/stable-audio-open-1.0"
    
    # Create models directory
    if not create_directory(model_path):
        return False
    
    try:
        # Use git to clone the repository
        logger.info(f"Cloning Stable Audio Open model to {model_path}")
        
        # Remove existing directory if it exists
        if os.path.exists(model_path):
            shutil.rmtree(model_path)
            
        # Clone the repository
        result = subprocess.run([
            "git", "clone", 
            "https://huggingface.co/stabilityai/stable-audio-open-1.0", 
            model_path
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info("Stable Audio Open model downloaded successfully!")
            
            # Check if essential files exist
            essential_files = [
                "config.json",
                "model.safetensors"
            ]
            
            for file in essential_files:
                file_path = os.path.join(model_path, file)
                if os.path.exists(file_path):
                    logger.info(f"✓ Found {file}")
                else:
                    logger.warning(f"✗ Missing {file}")
                    
            return True
        else:
            logger.error(f"Failed to download Stable Audio model: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("Stable Audio model download timed out")
        return False
    except Exception as e:
        logger.error(f"Error downloading Stable Audio model: {e}")
        return False

def setup_environment():
    """Set up the environment for model downloads"""
    logger.info("Setting up environment for model downloads...")
    
    # Install git-lfs if not available
    try:
        subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        logger.info("Git LFS is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Installing Git LFS...")
        try:
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "git-lfs"], check=True)
            subprocess.run(["git", "lfs", "install"], check=True)
            logger.info("Git LFS installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Git LFS: {e}")
            return False
    
    return True

def main():
    """Main function to download all models"""
    logger.info("Starting model download process...")
    
    # Setup environment
    if not setup_environment():
        logger.error("Failed to setup environment")
        return False
    
    # Create main models directory
    if not create_directory("/app/models"):
        logger.error("Failed to create models directory")
        return False
    
    # Download models
    wan21_success = download_wan21_model()
    stable_audio_success = download_stable_audio_model()
    
    # Summary
    logger.info("=" * 60)
    logger.info("MODEL DOWNLOAD SUMMARY")
    logger.info("=" * 60)
    logger.info(f"WAN 2.1 T2B 1.3B: {'✓ SUCCESS' if wan21_success else '✗ FAILED'}")
    logger.info(f"Stable Audio Open: {'✓ SUCCESS' if stable_audio_success else '✗ FAILED'}")
    logger.info("=" * 60)
    
    if wan21_success and stable_audio_success:
        logger.info("🎉 All models downloaded successfully!")
        logger.info("The application is now ready for production deployment with real models.")
        return True
    else:
        logger.warning("⚠️  Some models failed to download. The application will continue to work with fallback implementations.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)