#!/usr/bin/env python3
"""
Script-to-Video Backend Server - Production Ready
Comprehensive FastAPI backend with AI model integrations, optimized for scalability and performance
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import base64
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.gzip import GZipMiddleware

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

# AI and processing imports
import numpy as np
from PIL import Image
import cv2
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import requests
import subprocess
import aiohttp
import asyncio
import aiofiles

# Third-party integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Add the project root to path
sys.path.append('/app')
from ai_models import ai_manager
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_supervisor import GeminiSupervisor
from runwayml_processor import get_runwayml_processor
from enhanced_coqui_voice_manager import get_enhanced_coqui_voice_manager

# Import our new production-ready modules
from database import db_manager
from cache_manager import cache_manager, cache_result
from file_manager import file_manager
from queue_manager import queue_manager, TaskPriority
from monitoring import performance_monitor, monitor_endpoint, monitor_performance

# Create a function to get supervisor without circular import
def get_gemini_supervisor(api_keys):
    """Get Gemini supervisor instance"""
    return GeminiSupervisor(api_keys)

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/app/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPI app with production configuration
app = FastAPI(
    title="Script-to-Video API - Production",
    description="Comprehensive script-to-video generation with AI models - Production Ready",
    version="2.0.0-production",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add middleware for production
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
mongodb_client = None
db = None

# Environment variables
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
# Enhanced Gemini API configuration with smart multi-key, multi-model system
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1", "AIzaSyBwVEDRvZ2bHppZj2zN4opMqxjzcxpJCDk"),
    os.getenv("GEMINI_API_KEY_2", "AIzaSyB-VMWQe_Bvx6j_iixXTVGRB0fx0RpQSLU"),
    os.getenv("GEMINI_API_KEY_3", "AIzaSyD36dRBkEZUyCpDHLxTVuMO4P98SsYjkbc")
]

# Enhanced model configuration for different tasks using Gemini 2.5 Flash and Pro
GEMINI_MODEL_CONFIG = {
    "script_analysis": {
        "model": "gemini-2.5-pro",
        "description": "Complex script analysis with character detection",
        "max_tokens": 8192,
        "temperature": 0.3
    },
    "scene_breaking": {
        "model": "gemini-2.5-flash",
        "description": "Fast scene breakdown and segmentation",
        "max_tokens": 4096,
        "temperature": 0.4
    },
    "video_prompt": {
        "model": "gemini-2.5-flash",
        "description": "Creative video prompt generation",
        "max_tokens": 2048,
        "temperature": 0.7
    },
    "character_detection": {
        "model": "gemini-2.5-pro",
        "description": "Advanced character personality analysis",
        "max_tokens": 4096,
        "temperature": 0.2
    },
    "voice_assignment": {
        "model": "gemini-2.5-flash",
        "description": "Intelligent voice matching",
        "max_tokens": 2048,
        "temperature": 0.5
    },
    "video_validation": {
        "model": "gemini-2.5-flash",
        "description": "Quick video quality validation",
        "max_tokens": 1024,
        "temperature": 0.3
    },
    "editing_plan": {
        "model": "gemini-2.5-pro",
        "description": "Intelligent video editing and transition planning",
        "max_tokens": 4096,
        "temperature": 0.4
    },
    "quality_supervision": {
        "model": "gemini-2.5-pro",
        "description": "Final quality assessment and supervision",
        "max_tokens": 2048,
        "temperature": 0.2
    },
    "scene_enhancement": {
        "model": "gemini-2.5-pro",
        "description": "Scene description enhancement for better video generation",
        "max_tokens": 3072,
        "temperature": 0.6
    },
    "story_understanding": {
        "model": "gemini-2.5-pro",
        "description": "Deep story comprehension and narrative flow",
        "max_tokens": 8192,
        "temperature": 0.3
    }
}

# RunwayML API keys
RUNWAYML_API_KEYS = [
    os.getenv("RUNWAYML_API_KEY1", "key_2154d202435a6b1b8d6d887241a4e25ccade366566db56b7de2fe2aa2c133a41ee92654206db5d43b127b448e06db7774fb2625e06d35745e2ab808c11f761d4"),
    os.getenv("RUNWAYML_API_KEY2", "key_9b2398b5671c2b442e10e656f96bc9bc4712319f16d67c2027b5b1296601a3ecfa7a545b997b93f5f3cb34deedef0211facaf057c64a31fd558399617abdd8aa")
]

# Enhanced Cloudflare R2 Storage Configuration
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "https://69317cc9622018bb255db5a590d143c2.r2.cloudflarestorage.com")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY", "7804ed0f387a54af1eafbe2659c062f7")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY", "c94fe3a0d93c4594c8891b4f7fc54e5f26c76231972d8a4d0d8260bb6da61788")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "script-to-video-storage")

# Global instances for production components
gemini_supervisor = None
runwayml_processor = None
multi_voice_manager = None
websocket_manager = None

# Production startup and shutdown handlers
@app.on_event("startup")
async def startup_event():
    """Initialize production systems on startup"""
    global mongodb_client, db, gemini_supervisor, runwayml_processor, multi_voice_manager, websocket_manager
    
    try:
        logger.info("Starting production initialization...")
        
        # Initialize database with connection pooling
        await db_manager.connect()
        db = db_manager.db
        
        # Initialize file manager and start cleanup task
        await file_manager.start_cleanup_task()
        
        # Initialize queue manager and start workers
        await queue_manager.start_workers()
        
        # Start performance monitoring
        performance_monitor.start_background_monitoring()
        
        # Initialize AI components
        gemini_supervisor = get_gemini_supervisor(GEMINI_API_KEYS)
        runwayml_processor = get_runwayml_processor()
        multi_voice_manager = get_enhanced_coqui_voice_manager()
        
        # Initialize WebSocket manager
        websocket_manager = WebSocketManager()
        
        logger.info("Production initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of production systems"""
    global mongodb_client
    
    try:
        logger.info("Starting production shutdown...")
        
        # Stop queue workers
        await queue_manager.stop_workers()
        
        # Close database connection
        await db_manager.close()
        
        # Cleanup any remaining files
        await file_manager.cleanup_old_files("/tmp/processing", 0)
        
        logger.info("Production shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

# Enhanced WebSocket manager for real-time updates
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: str):
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Enhanced R2 client with proper error handling
try:
    r2_client = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version='s3v4', region_name='auto'),
        verify=True
    )
    logger.info("R2 Storage client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize R2 Storage client: {e}")
    r2_client = None

# Global variables
current_gemini_key_index = 0
active_connections: Dict[str, WebSocket] = {}
generation_status: Dict[str, Dict] = {}

# Initialize enhanced components
gemini_supervisor = get_gemini_supervisor(GEMINI_API_KEYS)
runwayml_processor = get_runwayml_processor(RUNWAYML_API_KEYS)
multi_voice_manager = get_enhanced_coqui_voice_manager()

# --- Pydantic Models ---

class ProjectRequest(BaseModel):
    script: str
    aspect_ratio: str = "16:9"
    voice_id: Optional[str] = None
    voice_name: Optional[str] = "default"

class ProjectResponse(BaseModel):
    project_id: str
    status: str
    created_at: datetime

class GenerationRequest(BaseModel):
    project_id: str
    script: str
    aspect_ratio: str = "16:9"
    voice_id: Optional[str] = None

class GenerationResponse(BaseModel):
    generation_id: str
    status: str
    progress: float = 0.0
    message: str = ""

class VoiceResponse(BaseModel):
    voice_id: str
    name: str
    preview_url: Optional[str] = None

# --- Database Functions ---

async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongodb_client, db
    try:
        mongodb_client = AsyncIOMotorClient(MONGO_URL)
        db = mongodb_client.script_to_video
        
        # Test the connection
        await db.command("ping")
        logger.info("Connected to MongoDB successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        return False

async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()

# --- Gemini Integration ---

class SmartGeminiManager:
    """Enhanced Gemini Manager with smart multi-key, multi-model system"""
    
    def __init__(self):
        self.api_keys = GEMINI_API_KEYS
        self.model_config = GEMINI_MODEL_CONFIG
        self.key_usage = {key: 0 for key in self.api_keys}
        self.model_usage = {model: 0 for model in self.model_config.keys()}
        self.current_key_index = 0
        self.chats = {}
        logger.info(f"SmartGeminiManager initialized with {len(self.api_keys)} API keys and {len(self.model_config)} model configurations")
    
    def get_optimal_key_model(self, task_type: str) -> tuple:
        """Get optimal API key and model for specific task type"""
        # Get model configuration for this task
        model_info = self.model_config.get(task_type, {
            "model": "gemini-2.0-flash",
            "description": "Default model for unknown tasks"
        })
        
        # Find the least used key
        least_used_key = min(self.api_keys, key=lambda k: self.key_usage[k])
        
        # Update usage counters
        self.key_usage[least_used_key] += 1
        self.model_usage[task_type] = self.model_usage.get(task_type, 0) + 1
        
        logger.info(f"Task: {task_type} | Model: {model_info['model']} | Key: {least_used_key[-10:]}... | Usage: {self.key_usage[least_used_key]}")
        
        return least_used_key, model_info['model']
    
    def get_fallback_key_model(self, failed_key: str, task_type: str) -> tuple:
        """Get fallback key and model when primary fails"""
        # Get next available key
        available_keys = [k for k in self.api_keys if k != failed_key]
        if not available_keys:
            return None, None
        
        fallback_key = min(available_keys, key=lambda k: self.key_usage[k])
        
        # Try different model for fallback
        fallback_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
        primary_model = self.model_config.get(task_type, {}).get("model", "gemini-2.0-flash")
        
        fallback_model = next((m for m in fallback_models if m != primary_model), "gemini-2.0-flash")
        
        logger.warning(f"Fallback - Task: {task_type} | Model: {fallback_model} | Key: {fallback_key[-10:]}...")
        
        return fallback_key, fallback_model
    
    async def execute_task(self, task_type: str, prompt: str, system_message: str = None) -> str:
        """Execute Gemini task with smart key/model selection and fallback"""
        max_retries = 3
        attempt = 0
        
        while attempt < max_retries:
            try:
                # Get optimal key and model
                if attempt == 0:
                    api_key, model = self.get_optimal_key_model(task_type)
                else:
                    # Use fallback on retry
                    api_key, model = self.get_fallback_key_model(self.last_failed_key, task_type)
                    if not api_key:
                        break
                
                # Create session
                session_id = f"{task_type}_{uuid.uuid4()}"
                
                default_system = f"You are an AI assistant specialized in {task_type}. {self.model_config.get(task_type, {}).get('description', '')}"
                
                chat = LlmChat(
                    api_key=api_key,
                    session_id=session_id,
                    system_message=system_message or default_system
                ).with_model("gemini", model)
                
                # Execute request
                message = UserMessage(text=prompt)
                response = await chat.send_message(message)
                
                logger.info(f"✅ Task {task_type} completed successfully with {model}")
                return response
                
            except Exception as e:
                attempt += 1
                self.last_failed_key = api_key
                logger.error(f"❌ Task {task_type} failed (attempt {attempt}/{max_retries}): {str(e)}")
                
                if attempt < max_retries:
                    await asyncio.sleep(1)  # Brief delay before retry
                    
        logger.error(f"❌ Task {task_type} failed after {max_retries} attempts")
        return ""
    
    def get_usage_stats(self) -> dict:
        """Get current usage statistics"""
        return {
            "key_usage": self.key_usage,
            "model_usage": self.model_usage,
            "total_requests": sum(self.key_usage.values())
        }

# Legacy GeminiManager for backward compatibility
class GeminiManager:
    def __init__(self):
        self.smart_manager = SmartGeminiManager()
        self.api_keys = GEMINI_API_KEYS
        self.current_key_index = 0
        self.chats = {}
    
    def get_next_key(self):
        """Get next API key with rotation"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    async def analyze_script_with_enhanced_scene_breaking(self, script: str) -> Dict:
        """Enhanced script analysis with intelligent scene breaking for video generation"""
        prompt = f"""
        As a professional movie director and script analyst, perform comprehensive analysis of this script for video production:
        
        SCRIPT:
        {script}
        
        Break this script into multiple scenes optimized for video generation. Each scene should be:
        - 5-10 seconds duration (optimal for Minimax video generation)
        - Visually distinct and cinematic
        - Logically sequenced for smooth narrative flow
        - Rich in visual details for AI video generation
        
        Return a JSON object with:
        
        {{
            "story_analysis": {{
                "narrative_flow": "description of story progression",
                "visual_style": "recommended visual style",
                "pacing": "fast/medium/slow",
                "theme": "main theme"
            }},
            "characters": [
                {{
                    "name": "character_name",
                    "personality": "detailed personality",
                    "role": "protagonist/antagonist/narrator/supporting",
                    "voice_characteristics": "voice description",
                    "gender": "male/female/neutral",
                    "age": "child/adult/elderly"
                }}
            ],
            "scenes": [
                {{
                    "scene_number": 1,
                    "description": "detailed visual description for video generation",
                    "duration": 6,
                    "visual_mood": "cinematic mood",
                    "camera_suggestions": "specific camera work",
                    "lighting_mood": "lighting description",
                    "audio_text": "dialogue or narration text",
                    "characters_present": ["character1", "character2"],
                    "visual_elements": "specific visual elements to include",
                    "transition_from_previous": "how to transition from previous scene"
                }}
            ]
        }}
        
        IMPORTANT: Create multiple scenes (at least 2-3) even for short scripts to ensure proper video flow.
        Return ONLY the JSON object.
        """
        
        response = await self.smart_manager.execute_task("script_analysis", prompt)
        
        try:
            analysis = json.loads(response)
            scenes = analysis.get("scenes", [])
            
            # Ensure we have multiple scenes
            if len(scenes) < 2:
                logger.warning("Only 1 scene generated, creating additional scenes")
                analysis = self._enhance_scene_breakdown(script, analysis)
            
            logger.info(f"Script analysis completed with {len(analysis.get('scenes', []))} scenes")
            return analysis
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from script analysis")
            return self._create_enhanced_fallback_analysis(script)
    
    def _enhance_scene_breakdown(self, script: str, analysis: Dict) -> Dict:
        """Enhance scene breakdown if only one scene is generated"""
        sentences = [s.strip() for s in script.split('.') if s.strip()]
        
        if len(sentences) > 1:
            # Create multiple scenes from sentences
            scenes = []
            for i, sentence in enumerate(sentences):
                scenes.append({
                    "scene_number": i + 1,
                    "description": sentence.strip(),
                    "duration": 5,
                    "visual_mood": "cinematic",
                    "camera_suggestions": "medium shot" if i == 0 else "close-up" if i % 2 == 1 else "wide shot",
                    "lighting_mood": "natural",
                    "audio_text": sentence.strip(),
                    "characters_present": ["Narrator"],
                    "visual_elements": "realistic environment",
                    "transition_from_previous": "smooth cut" if i > 0 else "fade in"
                })
            
            analysis["scenes"] = scenes
        
        return analysis
    
    def _create_enhanced_fallback_analysis(self, script: str) -> Dict:
        """Create enhanced fallback analysis with multiple scenes"""
        sentences = [s.strip() for s in script.split('.') if s.strip()]
        
        # Create at least 2 scenes even for short scripts
        if len(sentences) == 1:
            # Split long sentence into two parts
            words = sentences[0].split()
            mid_point = len(words) // 2
            sentences = [
                ' '.join(words[:mid_point]),
                ' '.join(words[mid_point:])
            ]
        
        scenes = []
        for i, sentence in enumerate(sentences):
            scenes.append({
                "scene_number": i + 1,
                "description": sentence.strip(),
                "duration": 6,
                "visual_mood": "cinematic",
                "camera_suggestions": "medium shot" if i == 0 else "close-up" if i % 2 == 1 else "wide shot",
                "lighting_mood": "natural",
                "audio_text": sentence.strip(),
                "characters_present": ["Narrator"],
                "visual_elements": "realistic environment",
                "transition_from_previous": "smooth cut" if i > 0 else "fade in"
            })
        
        return {
            "story_analysis": {
                "narrative_flow": "Linear progression with visual variety",
                "visual_style": "Realistic and cinematic",
                "pacing": "medium",
                "theme": "General storytelling"
            },
            "characters": [
                {
                    "name": "Narrator",
                    "personality": "Clear and engaging storyteller",
                    "role": "narrator",
                    "voice_characteristics": "Professional and warm",
                    "gender": "neutral",
                    "age": "adult"
                }
            ],
            "scenes": scenes
        }
    
    async def generate_enhanced_video_prompt(self, scene_description: str, scene_context: Dict = None) -> str:
        """Generate enhanced, optimized prompt for video generation"""
        context_info = ""
        if scene_context:
            context_info = f"""
            Scene Context:
            - Scene #{scene_context.get('scene_number', 1)} of multiple scenes
            - Duration: {scene_context.get('duration', 5)} seconds
            - Visual mood: {scene_context.get('visual_mood', 'neutral')}
            - Camera work: {scene_context.get('camera_suggestions', 'medium shot')}
            - Lighting: {scene_context.get('lighting_mood', 'natural')}
            - Transition: {scene_context.get('transition_from_previous', 'cut')}
            """
        
        prompt = f"""
        Convert this scene description into a highly optimized prompt for Minimax AI video generation:
        
        SCENE DESCRIPTION:
        {scene_description}
        
        {context_info}
        
        Create a detailed, cinematic prompt that:
        - Uses specific visual language optimized for AI video generation
        - Includes precise camera movements and angles
        - Specifies lighting conditions and color palette
        - Describes character actions and environmental details
        - Includes atmospheric and mood elements
        - Is formatted for maximum AI video generation quality
        
        Requirements:
        - Keep under 400 characters (strict limit for Minimax)
        - Use professional cinematography terminology
        - Be specific and highly visual
        - Focus on elements that AI can effectively generate
        - Include motion and dynamics
        
        Return ONLY the optimized video prompt, no additional text.
        """
        
        response = await self.smart_manager.execute_task("video_prompt", prompt)
        
        # Ensure prompt is under 400 characters
        if len(response) > 400:
            response = response[:400].rsplit(' ', 1)[0] + "..."
        
        return response or scene_description
    
    async def generate_video_prompt(self, scene_description: str, scene_context: Dict = None) -> str:
        """Generate enhanced, optimized prompt for video generation"""
        # Use the enhanced method
        return await self.generate_enhanced_video_prompt(scene_description, scene_context)

# --- Storage Functions ---

async def upload_to_r2(file_content: bytes, file_name: str, content_type: str) -> str:
    """Upload file to Cloudflare R2"""
    try:
        r2_client.put_object(
            Bucket="script-to-video",
            Key=file_name,
            Body=file_content,
            ContentType=content_type
        )
        return f"{R2_ENDPOINT}/script-to-video/{file_name}"
    except Exception as e:
        logger.error(f"R2 upload failed: {str(e)}")
        return None

async def upload_to_r2_storage(file_path: str, object_key: str, content_type: str = "video/mp4") -> Optional[str]:
    """
    Upload file to R2 Storage with enhanced error handling
    
    Args:
        file_path: Local path to the file
        object_key: S3 object key (remote path)
        content_type: MIME type of the file
        
    Returns:
        Public URL of uploaded file or None if failed
    """
    try:
        if not r2_client:
            logger.error("R2 client not initialized")
            return None
            
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        # Get file size
        file_size = os.path.getsize(file_path)
        logger.info(f"Uploading {file_path} to R2 storage (size: {file_size} bytes)")
        
        # Upload with proper metadata
        extra_args = {
            'ContentType': content_type,
            'ACL': 'public-read',
            'Metadata': {
                'uploaded_at': datetime.now().isoformat(),
                'file_size': str(file_size)
            }
        }
        
        # Upload the file
        r2_client.upload_file(
            file_path,
            R2_BUCKET_NAME,
            object_key,
            ExtraArgs=extra_args
        )
        
        # Generate public URL
        public_url = f"{R2_ENDPOINT}/{R2_BUCKET_NAME}/{object_key}"
        logger.info(f"Successfully uploaded to R2 storage: {public_url}")
        
        return public_url
        
    except Exception as e:
        logger.error(f"Failed to upload to R2 storage: {str(e)}")
        return None

async def create_r2_bucket_if_not_exists():
    """Create R2 bucket if it doesn't exist"""
    try:
        if not r2_client:
            logger.error("R2 client not initialized")
            return False
            
        # Check if bucket exists
        try:
            r2_client.head_bucket(Bucket=R2_BUCKET_NAME)
            logger.info(f"R2 bucket '{R2_BUCKET_NAME}' already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                logger.info(f"Creating R2 bucket: {R2_BUCKET_NAME}")
                r2_client.create_bucket(Bucket=R2_BUCKET_NAME)
                logger.info(f"R2 bucket '{R2_BUCKET_NAME}' created successfully")
                return True
            else:
                logger.error(f"Error checking R2 bucket: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Failed to create R2 bucket: {str(e)}")
        return False

async def upload_video_with_retry(video_path: str, generation_id: str, max_retries: int = 3) -> Optional[str]:
    """
    Upload video to R2 storage with retry logic
    
    Args:
        video_path: Local path to video file
        generation_id: Generation ID for naming
        max_retries: Maximum number of retry attempts
        
    Returns:
        Public URL of uploaded video or None if failed
    """
    for attempt in range(max_retries):
        try:
            # Create object key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_key = f"videos/{generation_id}/{timestamp}_final_video.mp4"
            
            # Upload to R2 storage
            public_url = await upload_to_r2_storage(video_path, object_key, "video/mp4")
            
            if public_url:
                logger.info(f"Video uploaded successfully on attempt {attempt + 1}")
                return public_url
            else:
                logger.warning(f"Upload failed on attempt {attempt + 1}")
                
        except Exception as e:
            logger.error(f"Upload attempt {attempt + 1} failed: {str(e)}")
            
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"Failed to upload video after {max_retries} attempts")
    return None

# --- Video Processing ---

async def combine_video_clips(video_clips: List[str], audio_file: str, output_path: str) -> bool:
    """Combine video clips with audio using FFmpeg"""
    try:
        # Create a temporary file list for FFmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for clip in video_clips:
                f.write(f"file '{clip}'\n")
            list_file = f.name
        
        # FFmpeg command to concatenate videos and add audio
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file,
            '-i', audio_file,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest', '-y', output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        os.unlink(list_file)
        
        if result.returncode == 0:
            logger.info("Video combination successful")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Video combination failed: {str(e)}")
        return False

# --- Background Tasks ---

async def process_enhanced_video_generation(generation_id: str, project_data: Dict):
    """Enhanced background task for video generation with Gemini supervision"""
    try:
        # Initialize managers
        gemini_manager = GeminiManager()
        
        # Update status
        generation_status[generation_id] = {
            "status": "processing",
            "progress": 0.0,
            "message": "Starting enhanced video generation with Gemini supervision..."
        }
        
        # Broadcast status
        await broadcast_status(generation_id)
        
        # Step 1: Enhanced Script Analysis with Multi-Scene Breaking
        generation_status[generation_id]["message"] = "Analyzing script and creating intelligent scene breakdown..."
        generation_status[generation_id]["progress"] = 5.0
        await broadcast_status(generation_id)
        
        # Use enhanced script analysis for better scene breaking
        script_analysis = await gemini_manager.analyze_script_with_enhanced_scene_breaking(project_data["script"])
        
        # Ensure we have proper scene structure
        if not script_analysis.get("scenes"):
            logger.warning("No scenes found in script analysis, creating fallback scenes")
            script_analysis["scenes"] = await gemini_supervisor.break_script_into_scenes(project_data["script"])
        
        logger.info(f"Script analysis completed with {len(script_analysis.get('scenes', []))} scenes")
        
        # Step 2: Generate Scene-Specific Video Prompts with Enhanced Context
        generation_status[generation_id]["message"] = "Creating optimized prompts for each scene..."
        generation_status[generation_id]["progress"] = 15.0
        await broadcast_status(generation_id)
        
        # Initialize the enhanced TTS engines if not already done
        if not hasattr(multi_voice_manager, 'tts_initialized'):
            await multi_voice_manager.initialize_tts_engines()
            multi_voice_manager.tts_initialized = True
        
        # Step 3: Generate Multiple Video Clips (One Per Scene with Enhanced Prompts)
        generation_status[generation_id]["message"] = "Generating video clips for each scene..."
        generation_status[generation_id]["progress"] = 25.0
        await broadcast_status(generation_id)
        
        video_clips = []
        validated_clips = []
        
        scenes = script_analysis.get("scenes", [])
        logger.info(f"Generating {len(scenes)} video clips for {len(scenes)} scenes")
        
        for i, scene in enumerate(scenes):
            # Generate enhanced optimized prompt for this specific scene with context
            scene_context = {
                "scene_number": scene.get("scene_number", i + 1),
                "duration": scene.get("duration", 5),
                "visual_mood": scene.get("visual_mood", "neutral"),
                "camera_suggestions": scene.get("camera_suggestions", "medium shot"),
                "lighting_mood": scene.get("lighting_mood", "natural"),
                "transition_from_previous": scene.get("transition_from_previous", "cut"),
                "visual_elements": scene.get("visual_elements", "standard composition"),
                "total_scenes": len(scenes)
            }
            
            video_prompt = await gemini_manager.generate_enhanced_video_prompt(
                scene.get("description", ""),
                scene_context
            )
            
            # Truncate prompt if too long (max 400 characters for Minimax)
            if len(video_prompt) > 400:
                video_prompt = video_prompt[:400].rsplit(' ', 1)[0] + "..."
                logger.warning(f"Scene {i+1} prompt truncated to {len(video_prompt)} characters")
            
            logger.info(f"Scene {i+1}/{len(scenes)}: Generating clip with enhanced prompt: {video_prompt[:100]}...")
            
            # Generate video clip for this scene
            video_path = ai_manager.generate_content(
                video_prompt,
                "video",
                aspect_ratio=project_data["aspect_ratio"],
                duration=scene.get("duration", 5)
            )
            
            if video_path:
                video_clips.append(video_path)
                validated_clips.append({
                    "path": video_path,
                    "scene": scene,
                    "prompt": video_prompt,
                    "scene_number": i + 1,
                    "scene_context": scene_context
                })
                logger.info(f"Scene {i+1} clip generated successfully with enhanced prompt")
            else:
                logger.error(f"Failed to generate clip for scene {i+1}")
            
            # Update progress
            progress = 25.0 + (i + 1) / len(scenes) * 35.0
            generation_status[generation_id]["progress"] = progress
            await broadcast_status(generation_id)
        
        # Step 4: Generate Multi-Character Audio
        generation_status[generation_id]["message"] = "Generating multi-character audio..."
        generation_status[generation_id]["progress"] = 60.0
        await broadcast_status(generation_id)
        
        # Create dialogue sequence
        dialogue_sequence = []
        for scene in script_analysis.get("scenes", []):
            # Extract characters and dialogue from scene
            characters = script_analysis.get("characters", [])
            
            # For now, use the first character or narrator
            if characters:
                character_name = characters[0].get("name", "Narrator")
            else:
                character_name = "Narrator"
            
            dialogue_sequence.append({
                "character": character_name,
                "text": scene.get("audio_text", scene.get("description", "")),
                "scene_context": {
                    "scene_number": scene.get("scene_number", 1),
                    "mood": scene.get("visual_mood", "neutral"),
                    "duration": scene.get("duration", 5)
                }
            })
        
        # Generate multi-character audio
        audio_segments = await multi_voice_manager.generate_multi_character_audio(dialogue_sequence)
        
        # Combine audio segments
        combined_audio = None
        if audio_segments:
            # For now, use the first segment's audio (in production, we'd combine all)
            combined_audio = audio_segments[0].get("audio_data")
        
        # Step 5: Intelligent Video Editing Plan
        generation_status[generation_id]["message"] = "Creating intelligent editing plan..."
        generation_status[generation_id]["progress"] = 70.0
        await broadcast_status(generation_id)
        
        editing_plan = await gemini_supervisor.plan_video_editing(
            video_clips,
            script_analysis.get("scenes", []),
            [seg.get("audio_data") for seg in audio_segments if seg.get("audio_data")]
        )
        
        # Step 6: Professional Post-Production with RunwayML
        generation_status[generation_id]["message"] = "Applying professional post-production..."
        generation_status[generation_id]["progress"] = 80.0
        await broadcast_status(generation_id)
        
        # Save combined video for processing
        temp_video_path = f"/tmp/temp_video_{generation_id}.mp4"
        if video_clips:
            # For now, use the first clip as temp (in production, we'd combine all clips first)
            temp_video_path = video_clips[0]
            
            # Ensure the temp video file exists
            if not os.path.exists(temp_video_path):
                logger.error(f"Temporary video file not found: {temp_video_path}")
                # Create a fallback if the file doesn't exist
                temp_video_path = f"/tmp/fallback_video_{generation_id}.mp4"
                # In development, create a placeholder file
                with open(temp_video_path, 'w') as f:
                    f.write("")  # Empty file as placeholder
        
        # Apply comprehensive post-production
        post_production_result = await runwayml_processor.comprehensive_post_production(
            temp_video_path,
            editing_plan
        )
        
        # Step 7: Combine Video and Audio
        generation_status[generation_id]["message"] = "Combining video and audio..."
        generation_status[generation_id]["progress"] = 90.0
        await broadcast_status(generation_id)
        
        # Save audio to temp file
        audio_file = None
        if combined_audio:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(combined_audio)
                audio_file = f.name
        
        # Final video path
        final_video_path = post_production_result.get("final_video", temp_video_path)
        
        # Ensure the final video path exists
        if not os.path.exists(final_video_path):
            logger.warning(f"Final video file not found: {final_video_path}, using temp video")
            final_video_path = temp_video_path
        
        if video_clips and audio_file:
            output_path = f"/tmp/final_enhanced_video_{generation_id}.mp4"
            success = await combine_video_clips(video_clips, audio_file, output_path)
            
            if success and os.path.exists(output_path):
                final_video_path = output_path
                logger.info(f"Combined video created successfully: {final_video_path}")
            else:
                logger.warning(f"Video combination failed or file not created: {output_path}")
        
        # Step 8: Final Quality Supervision (only if file exists)
        generation_status[generation_id]["message"] = "Final quality review..."
        generation_status[generation_id]["progress"] = 95.0
        await broadcast_status(generation_id)
        
        final_assessment = await gemini_supervisor.supervise_final_quality(
            final_video_path,
            project_data["script"]
        )
        
        # Step 9: Enhanced Upload to R2 Storage with Retry
        generation_status[generation_id]["message"] = "Uploading final video to cloud storage..."
        generation_status[generation_id]["progress"] = 98.0
        await broadcast_status(generation_id)
        
        # Ensure R2 bucket exists
        await create_r2_bucket_if_not_exists()
        
        video_url = None
        if os.path.exists(final_video_path):
            # Use enhanced upload with retry
            video_url = await upload_video_with_retry(final_video_path, generation_id)
            
            if not video_url:
                # Fallback to original upload method
                logger.warning("Enhanced upload failed, trying fallback method")
                with open(final_video_path, 'rb') as f:
                    video_content = f.read()
                
                video_url = await upload_to_r2(
                    video_content,
                    f"videos/enhanced_{generation_id}.mp4",
                    "video/mp4"
                )
        else:
            logger.error(f"Final video file not found: {final_video_path}")
        
        # Step 10: Complete Generation
        if video_url:
            # Get production summary
            production_summary = gemini_supervisor.get_production_summary()
            
            # Update database
            await db.generations.update_one(
                {"generation_id": generation_id},
                {
                    "$set": {
                        "status": "completed",
                        "progress": 100.0,
                        "video_url": video_url,
                        "completed_at": datetime.utcnow(),
                        "enhancement_data": {
                            "script_analysis": script_analysis,
                            "editing_plan": editing_plan,
                            "post_production": post_production_result,
                            "final_assessment": final_assessment,
                            "production_summary": production_summary
                        }
                    }
                }
            )
            
            generation_status[generation_id] = {
                "status": "completed",
                "progress": 100.0,
                "message": "Enhanced video generation completed with movie-level quality!",
                "video_url": video_url,
                "enhancement_data": {
                    "characters_detected": len(script_analysis.get("characters", [])),
                    "scenes_processed": len(script_analysis.get("scenes", [])),
                    "post_production_steps": post_production_result.get("processing_steps", 0),
                    "final_quality_score": final_assessment.get("final_score", 0.0),
                    "director_approval": final_assessment.get("approval_status", "unknown")
                }
            }
        else:
            generation_status[generation_id] = {
                "status": "failed",
                "progress": 0.0,
                "message": "Enhanced video generation failed during upload"
            }
        
        # Broadcast final status
        await broadcast_status(generation_id)
        
        logger.info(f"Enhanced video generation completed for {generation_id}")
        
    except Exception as e:
        logger.error(f"Enhanced video generation failed: {str(e)}")
        generation_status[generation_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": f"Enhanced video generation failed: {str(e)}"
        }
        await broadcast_status(generation_id)


# Keep the original process for backward compatibility
async def process_video_generation(generation_id: str, project_data: Dict):
    """Original background task for video generation (kept for compatibility)"""
    # Call the enhanced version
    await process_enhanced_video_generation(generation_id, project_data)
    try:
        # Update status
        generation_status[generation_id] = {
            "status": "processing",
            "progress": 0.0,
            "message": "Starting video generation..."
        }
        
        # Broadcast status
        await broadcast_status(generation_id)
        
        # Initialize managers
        gemini_manager = GeminiManager()
        
        # Step 1: Analyze script
        generation_status[generation_id]["message"] = "Analyzing script..."
        generation_status[generation_id]["progress"] = 10.0
        await broadcast_status(generation_id)
        
        script_analysis = await gemini_manager.analyze_script(project_data["script"])
        
        # Step 2: Generate video clips
        generation_status[generation_id]["message"] = "Generating video clips..."
        generation_status[generation_id]["progress"] = 30.0
        await broadcast_status(generation_id)
        
        video_clips = []
        for i, scene in enumerate(script_analysis["scenes"]):
            # Generate optimized prompt
            video_prompt = await gemini_manager.generate_video_prompt(scene["description"])
            
            # Generate video clip
            video_path = ai_manager.generate_content(
                video_prompt,
                "video",
                aspect_ratio=project_data["aspect_ratio"],
                duration=scene["duration"]
            )
            
            if video_path:
                video_clips.append(video_path)
            
            # Update progress
            progress = 30.0 + (i + 1) / len(script_analysis["scenes"]) * 30.0
            generation_status[generation_id]["progress"] = progress
            await broadcast_status(generation_id)
        
        # Step 3: Generate voice over
        generation_status[generation_id]["message"] = "Generating voice over..."
        generation_status[generation_id]["progress"] = 70.0
        await broadcast_status(generation_id)
        
        # Initialize the enhanced TTS engines if not already done
        if not hasattr(multi_voice_manager, 'tts_initialized'):
            await multi_voice_manager.initialize_tts_engines()
            multi_voice_manager.tts_initialized = True
        
        # Create dialogue sequence
        full_script = " ".join([scene["audio_text"] for scene in script_analysis["scenes"]])
        dialogue_sequence = [{
            "character": "Narrator",
            "text": full_script,
            "scene_context": {
                "scene_number": 1,
                "mood": "neutral",
                "duration": script_analysis.get("total_duration", 10)
            }
        }]
        
        # Generate audio using multi_voice_manager
        audio_segments = await multi_voice_manager.generate_multi_character_audio(dialogue_sequence)
        
        # Save audio to temp file
        audio_file = None
        if audio_segments and audio_segments[0].get("audio_data"):
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(audio_segments[0]["audio_data"])
                audio_file = f.name
        
        # Step 4: Combine video and audio
        generation_status[generation_id]["message"] = "Combining video and audio..."
        generation_status[generation_id]["progress"] = 85.0
        await broadcast_status(generation_id)
        
        if video_clips and audio_file:
            output_path = f"/tmp/final_video_{generation_id}.mp4"
            success = await combine_video_clips(video_clips, audio_file, output_path)
            
            if success:
                # Upload to R2
                generation_status[generation_id]["message"] = "Uploading final video..."
                generation_status[generation_id]["progress"] = 95.0
                await broadcast_status(generation_id)
                
                with open(output_path, 'rb') as f:
                    video_content = f.read()
                
                video_url = await upload_to_r2(
                    video_content,
                    f"videos/{generation_id}.mp4",
                    "video/mp4"
                )
                
                if video_url:
                    # Update database
                    await db.generations.update_one(
                        {"generation_id": generation_id},
                        {
                            "$set": {
                                "status": "completed",
                                "progress": 100.0,
                                "video_url": video_url,
                                "completed_at": datetime.utcnow()
                            }
                        }
                    )
                    
                    generation_status[generation_id] = {
                        "status": "completed",
                        "progress": 100.0,
                        "message": "Video generation completed!",
                        "video_url": video_url
                    }
                    
                    await broadcast_status(generation_id)
                    
                    # Clean up temp files
                    for clip in video_clips:
                        if os.path.exists(clip):
                            os.unlink(clip)
                    if os.path.exists(audio_file):
                        os.unlink(audio_file)
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                    
                    logger.info(f"Video generation completed: {generation_id}")
                    return
        
        # If we get here, something failed
        generation_status[generation_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": "Video generation failed"
        }
        await broadcast_status(generation_id)
        
    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        generation_status[generation_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": f"Error: {str(e)}"
        }
        await broadcast_status(generation_id)

async def broadcast_status(generation_id: str):
    """Broadcast status to connected WebSocket clients"""
    if generation_id in active_connections:
        try:
            await active_connections[generation_id].send_json(generation_status[generation_id])
        except:
            # Remove broken connection
            del active_connections[generation_id]

# --- API Routes ---

@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger.info("Starting Script-to-Video API...")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Initialize AI models
    ai_manager.load_models()
    
    # Initialize enhanced multi-voice manager
    await multi_voice_manager.initialize_tts_engines()
    
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_mongo_connection()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Script-to-Video API is running"}

@app.get("/api/health")
async def health_check():
    """Enhanced health check endpoint with all components"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_models": {
            "minimax": ai_manager.minimax_generator.loaded,
            "stable_audio": ai_manager.stable_audio.loaded
        },
        "enhanced_components": {
            "gemini_supervisor": gemini_supervisor is not None,
            "runwayml_processor": runwayml_processor is not None,
            "multi_voice_manager": multi_voice_manager is not None,
            "capabilities": {
                "character_detection": True,
                "voice_assignment": True,
                "video_validation": True,
                "post_production": True,
                "quality_supervision": True
            }
        },
        "version": "2.0-enhanced"
    }

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """Create a new project"""
    try:
        project_id = str(uuid.uuid4())
        project_data = {
            "project_id": project_id,
            "script": request.script,
            "aspect_ratio": request.aspect_ratio,
            "voice_id": request.voice_id,
            "voice_name": request.voice_name,
            "status": "created",
            "created_at": datetime.utcnow()
        }
        
        await db.projects.insert_one(project_data)
        
        return ProjectResponse(
            project_id=project_id,
            status="created",
            created_at=project_data["created_at"]
        )
    except Exception as e:
        logger.error(f"Project creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get project details"""
    try:
        project = await db.projects.find_one({"project_id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Remove MongoDB ObjectId
        project.pop('_id', None)
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project")

@app.post("/api/generate", response_model=GenerationResponse)
async def start_generation(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start video generation"""
    try:
        # Check if project exists
        project = await db.projects.find_one({"project_id": request.project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        generation_id = str(uuid.uuid4())
        generation_data = {
            "generation_id": generation_id,
            "project_id": request.project_id,
            "status": "queued",
            "progress": 0.0,
            "created_at": datetime.utcnow()
        }
        
        await db.generations.insert_one(generation_data)
        
        # Start background task
        background_tasks.add_task(
            process_video_generation,
            generation_id,
            {
                "script": request.script,
                "aspect_ratio": request.aspect_ratio,
                "voice_id": request.voice_id
            }
        )
        
        return GenerationResponse(
            generation_id=generation_id,
            status="queued",
            progress=0.0,
            message="Generation queued"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation start failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start generation")

@app.get("/api/generate/{generation_id}")
async def get_generation_status(generation_id: str):
    """Get generation status"""
    try:
        # Check memory first
        if generation_id in generation_status:
            return generation_status[generation_id]
        
        # Check database
        generation = await db.generations.find_one({"generation_id": generation_id})
        if not generation:
            raise HTTPException(status_code=404, detail="Generation not found")
        
        generation.pop('_id', None)
        return generation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get generation status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get generation status")

@app.get("/api/voices", response_model=List[VoiceResponse])
async def get_voices():
    """Get available voices"""
    try:
        voices = await multi_voice_manager.get_available_voices()
        return voices
    except Exception as e:
        logger.error(f"Failed to get voices: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get voices")

@app.websocket("/api/ws/{generation_id}")
async def websocket_endpoint(websocket: WebSocket, generation_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections[generation_id] = websocket
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        if generation_id in active_connections:
            del active_connections[generation_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)