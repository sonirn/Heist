#!/usr/bin/env python3
"""
AI Models Integration Module for Script-to-Video Website
Integrates Minimax API and Stable Audio Open models
"""
import os
import sys
import logging
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import base64
import io
from PIL import Image
import tempfile
import cv2
import json
from datetime import datetime
import subprocess

# Import real implementations
from ai_models_real import get_minimax_generator, get_stable_audio_generator, MinimaxVideoGenerator, RealStableAudioGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StableAudioWrapper:
    """Wrapper for Stable Audio Open model using real implementation"""
    
    def __init__(self):
        self.real_generator = get_stable_audio_generator()
        
    @property
    def loaded(self):
        """Get current loaded state from real generator"""
        return self.real_generator.loaded
        
    @property
    def development_mode(self):
        """Get current development mode from real generator"""
        return getattr(self.real_generator, 'development_mode', False)
    
    def load_model(self):
        """Load the Stable Audio model"""
        return self.real_generator.load_model()
    
    def generate_audio(self, prompt: str, duration: float = 10.0, 
                      steps: int = 100, cfg_scale: float = 7.0,
                      seed: Optional[int] = None) -> bytes:
        """Generate audio using real generator"""
        return self.real_generator.generate_audio(prompt, duration, steps, cfg_scale, seed)


class MinimaxVideoGeneratorWrapper:
    """
    Minimax Video Generation Model Wrapper using real implementation
    
    This class provides a complete interface for Minimax video generation.
    """
    
    def __init__(self, device="cpu", model_path=None):
        """
        Initialize Minimax video generator
        
        Args:
            device: Device to run the model on ('cpu' or 'cuda')
            model_path: Path to model weights directory (kept for compatibility)
        """
        self.real_generator = get_minimax_generator(device)
        self.device = device
        self.model_path = model_path
        
        # Minimax supported aspect ratios
        self.supported_aspect_ratios = self.real_generator.supported_aspect_ratios
        
        # Model specifications
        self.model_specs = self.real_generator.model_specs
        
        logger.info(f"Minimax video generator initialized for {device}")
        
    @property
    def loaded(self):
        """Get current loaded state from real generator"""
        return self.real_generator.loaded
        
    @property
    def development_mode(self):
        """Get current development mode from real generator"""
        return getattr(self.real_generator, 'development_mode', False)
        
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and specifications
        
        Returns:
            Dict containing model information
        """
        return self.real_generator.get_model_info()
    
    def load_model(self):
        """
        Load Minimax video generation model
        
        Returns:
            bool: True if model loaded successfully
        """
        return self.real_generator.load_model()
    
    def generate_video(self, prompt: str, aspect_ratio: str = "16:9", **kwargs) -> Optional[bytes]:
        """Generate video using real generator"""
        return self.real_generator.generate_video(prompt, aspect_ratio, **kwargs)
    
    def get_deployment_instructions(self) -> str:
        """Get deployment instructions"""
        return self.real_generator.get_deployment_guide()


class AIModelManager:
    """Manager class for all AI models"""
    
    def __init__(self):
        """Initialize AI model manager"""
        self.minimax_generator = MinimaxVideoGeneratorWrapper()
        self.stable_audio = StableAudioWrapper()
        self.loaded = False
        
        # Create aliases for backward compatibility
        self.wan21_generator = self.minimax_generator
        self.video_generator = self.minimax_generator
    
    def load_models(self):
        """Load all AI models"""
        try:
            logger.info("Loading AI models...")
            
            # Load Minimax model
            minimax_loaded = self.minimax_generator.load_model()
            
            # Load Stable Audio model
            stable_audio_loaded = self.stable_audio.load_model()
            
            self.loaded = minimax_loaded and stable_audio_loaded
            
            if self.loaded:
                logger.info("All AI models loaded successfully")
            else:
                logger.warning("Some AI models failed to load")
                
            return self.loaded
            
        except Exception as e:
            logger.error(f"Failed to load AI models: {str(e)}")
            return False
    
    def generate_video(self, prompt: str, aspect_ratio: str = "16:9", **kwargs) -> Optional[bytes]:
        """Generate video using Minimax model"""
        return self.minimax_generator.generate_video(prompt, aspect_ratio, **kwargs)
    
    def generate_audio(self, prompt: str, duration: int = 10) -> Optional[bytes]:
        """Generate audio using Stable Audio model"""
        return self.stable_audio.generate_audio(prompt, duration)
    
    def generate_content(self, prompt: str, content_type: str, **kwargs) -> Optional[bytes]:
        """
        Generate content using appropriate model
        
        Args:
            prompt: Text prompt for content generation
            content_type: Type of content to generate ('video' or 'audio')
            **kwargs: Additional parameters for generation
            
        Returns:
            bytes: Generated content data
        """
        try:
            if content_type.lower() == "video":
                return self.generate_video(prompt, **kwargs)
            elif content_type.lower() == "audio":
                duration = kwargs.get('duration', 10)
                return self.generate_audio(prompt, duration)
            else:
                logger.error(f"Unsupported content type: {content_type}")
                return None
                
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            "minimax": {
                "loaded": self.minimax_generator.loaded,
                "device": self.minimax_generator.device,
                "development_mode": self.minimax_generator.development_mode,
                "info": self.minimax_generator.get_model_info()
            },
            "stable_audio": {
                "loaded": self.stable_audio.loaded,
                "development_mode": self.stable_audio.development_mode,
                "info": self.stable_audio.real_generator.get_model_info()
            },
            "manager": {
                "loaded": self.loaded,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def get_deployment_guide(self) -> str:
        """Get comprehensive deployment guide"""
        return self.minimax_generator.get_deployment_instructions()


# Global AI model manager instance
ai_manager = AIModelManager()

# Initialize models on import
if not ai_manager.load_models():
    logger.warning("AI models initialization incomplete")
else:
    logger.info("AI models ready for use")

# Backward compatibility aliases
WAN21VideoGenerator = MinimaxVideoGeneratorWrapper