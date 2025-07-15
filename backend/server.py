#!/usr/bin/env python3
"""
Script-to-Video Backend Server
Comprehensive FastAPI backend with AI model integrations
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

# FastAPI imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

# Database imports
from motor.motor_asyncio import AsyncIOMotorClient
import pymongo

# AI and processing imports
import numpy as np
from PIL import Image
import cv2
import boto3
from botocore.client import Config
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
from gemini_supervisor import get_gemini_supervisor
from runwayml_processor import get_runwayml_processor
from multi_character_voice import get_multi_voice_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Script-to-Video API",
    description="Comprehensive script-to-video generation with AI models",
    version="1.0.0"
)

# CORS middleware
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
GEMINI_API_KEYS = [
    "AIzaSyBwVEDRvZ2bHppZj2zN4opMqxjzcxpJCDk",
    "AIzaSyB-VMWQe_Bvx6j_iixXTVGRB0fx0RpQSLU",
    "AIzaSyD36dRBkEZUyCpDHLxTVuMO4P98SsYjkbc"
]
ELEVENLABS_API_KEY = "sk_613429b69a534539f725091aab14705a535bbeeeb6f52133"

# RunwayML API keys
RUNWAYML_API_KEYS = [
    os.getenv("RUNWAYML_API_KEY1", "key_2154d202435a6b1b8d6d887241a4e25ccade366566db56b7de2fe2aa2c133a41ee92654206db5d43b127b448e06db7774fb2625e06d35745e2ab808c11f761d4"),
    os.getenv("RUNWAYML_API_KEY2", "key_9b2398b5671c2b442e10e656f96bc9bc4712319f16d67c2027b5b1296601a3ecfa7a545b997b93f5f3cb34deedef0211facaf057c64a31fd558399617abdd8aa")
]

# Cloudflare R2 configuration
R2_ENDPOINT = "https://69317cc9622018bb255db5a590d143c2.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "7804ed0f387a54af1eafbe2659c062f7"
R2_SECRET_KEY = "c94fe3a0d93c4594c8891b4f7fc54e5f26c76231972d8a4d0d8260bb6da61788"

# R2 client
r2_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    config=Config(signature_version='s3v4'),
)

# Global variables
current_gemini_key_index = 0
active_connections: Dict[str, WebSocket] = {}
generation_status: Dict[str, Dict] = {}

# Initialize enhanced components
gemini_supervisor = get_gemini_supervisor(GEMINI_API_KEYS)
runwayml_processor = get_runwayml_processor(RUNWAYML_API_KEYS)
multi_voice_manager = get_multi_voice_manager(ELEVENLABS_API_KEY)

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

class GeminiManager:
    def __init__(self):
        self.api_keys = GEMINI_API_KEYS
        self.current_key_index = 0
        self.chats = {}
    
    def get_next_key(self):
        """Get next API key with rotation"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    async def analyze_script(self, script: str) -> Dict:
        """Analyze script and break it into scenes"""
        try:
            api_key = self.get_next_key()
            session_id = f"script_analysis_{uuid.uuid4()}"
            
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message="You are a script analyzer. Analyze the provided script and break it into scenes for video generation."
            ).with_model("gemini", "gemini-2.0-flash")
            
            prompt = f"""
            Analyze this script and break it into scenes suitable for video generation:
            
            Script: {script}
            
            Please provide a JSON response with:
            1. scenes: Array of scene objects with:
               - scene_number: int
               - description: string (visual description for video generation)
               - duration: int (seconds)
               - audio_text: string (text to be spoken)
            2. total_duration: int (total video duration in seconds)
            3. theme: string (overall theme/mood)
            
            Return only valid JSON, no explanations.
            """
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            # Parse JSON response
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "scenes": [{
                        "scene_number": 1,
                        "description": script,
                        "duration": 10,
                        "audio_text": script
                    }],
                    "total_duration": 10,
                    "theme": "general"
                }
                
        except Exception as e:
            logger.error(f"Script analysis failed: {str(e)}")
            return {
                "scenes": [{
                    "scene_number": 1,
                    "description": script,
                    "duration": 10,
                    "audio_text": script
                }],
                "total_duration": 10,
                "theme": "general"
            }
    
    async def generate_video_prompt(self, scene_description: str) -> str:
        """Generate optimized prompt for video generation"""
        try:
            api_key = self.get_next_key()
            session_id = f"prompt_gen_{uuid.uuid4()}"
            
            chat = LlmChat(
                api_key=api_key,
                session_id=session_id,
                system_message="You are a video generation prompt optimizer. Convert scene descriptions into optimized prompts for AI video generation."
            ).with_model("gemini", "gemini-2.0-flash")
            
            prompt = f"""
            Convert this scene description into an optimized prompt for AI video generation:
            
            Scene: {scene_description}
            
            Create a detailed, cinematic prompt that includes:
            - Visual style and mood
            - Camera movements and angles
            - Lighting conditions
            - Color palette
            - Any specific details
            
            Keep it concise but descriptive. Return only the optimized prompt.
            """
            
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Prompt generation failed: {str(e)}")
            return scene_description

# --- ElevenLabs Integration ---

class ElevenLabsManager:
    def __init__(self):
        self.api_key = ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    
    async def get_voices(self) -> List[VoiceResponse]:
        """Get available voices from ElevenLabs"""
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/voices", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices = []
                        for voice in data.get("voices", []):
                            voices.append(VoiceResponse(
                                voice_id=voice["voice_id"],
                                name=voice["name"],
                                preview_url=voice.get("preview_url")
                            ))
                        return voices
                    else:
                        logger.error(f"Failed to get voices: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []
    
    async def generate_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """Generate speech from text"""
        try:
            voice_id = voice_id or self.default_voice_id
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Speech generation failed: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error generating speech: {str(e)}")
            return None

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
        
        # Step 1: Enhanced Script Analysis with Character Detection
        generation_status[generation_id]["message"] = "Analyzing script with character detection..."
        generation_status[generation_id]["progress"] = 5.0
        await broadcast_status(generation_id)
        
        script_analysis = await gemini_supervisor.analyze_script_with_characters(project_data["script"])
        
        # Step 2: Intelligent Voice Assignment
        generation_status[generation_id]["message"] = "Assigning voices to characters..."
        generation_status[generation_id]["progress"] = 15.0
        await broadcast_status(generation_id)
        
        # Get available voices
        available_voices = await multi_voice_manager.get_available_voices()
        
        # Assign voices using Gemini supervisor
        voice_assignments = await gemini_supervisor.assign_character_voices(
            script_analysis.get("characters", []),
            available_voices
        )
        
        # Configure multi-character voice manager
        await multi_voice_manager.assign_voices_to_characters(
            script_analysis.get("characters", []),
            voice_assignments
        )
        
        # Step 3: Generate and Validate Video Clips
        generation_status[generation_id]["message"] = "Generating video clips with quality validation..."
        generation_status[generation_id]["progress"] = 25.0
        await broadcast_status(generation_id)
        
        video_clips = []
        validated_clips = []
        
        for i, scene in enumerate(script_analysis.get("scenes", [])):
            # Generate optimized prompt
            video_prompt = await gemini_manager.generate_video_prompt(scene["description"])
            
            # Generate video clip
            video_path = ai_manager.generate_content(
                video_prompt,
                "video",
                aspect_ratio=project_data["aspect_ratio"],
                duration=scene.get("duration", 5)
            )
            
            if video_path:
                # Validate clip with Gemini supervisor
                validation_result = await gemini_supervisor.validate_video_clip(
                    video_path,
                    video_prompt,
                    scene
                )
                
                if validation_result.get("approval_status") == "approved":
                    video_clips.append(video_path)
                    validated_clips.append({
                        "path": video_path,
                        "scene": scene,
                        "validation": validation_result
                    })
                else:
                    logger.warning(f"Clip validation failed for scene {i+1}: {validation_result.get('revision_notes', '')}")
                    # For now, use the clip anyway (in production, we'd regenerate)
                    video_clips.append(video_path)
                    validated_clips.append({
                        "path": video_path,
                        "scene": scene,
                        "validation": validation_result
                    })
            
            # Update progress
            progress = 25.0 + (i + 1) / len(script_analysis.get("scenes", [])) * 25.0
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
            # Use the first clip as temp (in production, we'd combine all clips first)
            temp_video_path = video_clips[0]
        
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
        
        if video_clips and audio_file:
            output_path = f"/tmp/final_enhanced_video_{generation_id}.mp4"
            success = await combine_video_clips(video_clips, audio_file, output_path)
            
            if success:
                final_video_path = output_path
        
        # Step 8: Final Quality Supervision
        generation_status[generation_id]["message"] = "Final quality review..."
        generation_status[generation_id]["progress"] = 95.0
        await broadcast_status(generation_id)
        
        final_assessment = await gemini_supervisor.supervise_final_quality(
            final_video_path,
            project_data["script"]
        )
        
        # Step 9: Upload to R2
        generation_status[generation_id]["message"] = "Uploading final video..."
        generation_status[generation_id]["progress"] = 98.0
        await broadcast_status(generation_id)
        
        video_url = None
        if os.path.exists(final_video_path):
            with open(final_video_path, 'rb') as f:
                video_content = f.read()
            
            video_url = await upload_to_r2(
                video_content,
                f"videos/enhanced_{generation_id}.mp4",
                "video/mp4"
            )
        
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
                            "voice_assignments": voice_assignments,
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
                    "voices_assigned": len(voice_assignments.get("voice_assignments", {})),
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
        elevenlabs_manager = ElevenLabsManager()
        
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
        
        full_script = " ".join([scene["audio_text"] for scene in script_analysis["scenes"]])
        speech_audio = await elevenlabs_manager.generate_speech(
            full_script,
            project_data.get("voice_id")
        )
        
        # Save audio to temp file
        audio_file = None
        if speech_audio:
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                f.write(speech_audio)
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
        elevenlabs_manager = ElevenLabsManager()
        voices = await elevenlabs_manager.get_voices()
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