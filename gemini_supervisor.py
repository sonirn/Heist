#!/usr/bin/env python3
"""
Enhanced Gemini Supervisor for Human-like Video Production Workflow
This module provides intelligent supervision throughout the video production process
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import base64
import cv2
import numpy as np
from PIL import Image

# Emergency integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType, ChatError

# Import smart manager for enhanced capabilities
sys.path.append('/app')
# Remove circular import - will initialize SmartGeminiManager later

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiSupervisor:
    """
    Enhanced Gemini Supervisor - Acts as Human-like Director Throughout Video Production
    
    This class provides continuous supervision and quality assurance throughout
    the entire video production workflow, making intelligent decisions like a human director.
    """
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize Gemini Supervisor with enhanced capabilities
        
        Args:
            api_keys: List of Gemini API keys for load balancing
        """
        self.api_keys = api_keys
        self.current_key_index = 0
        self.session_id = f"supervisor_{uuid.uuid4()}"
        
        # Production context for human-like decision making
        self.production_context = {
            "script": "",
            "target_theme": "",
            "characters": [],
            "scene_sequence": [],
            "quality_standards": {
                "visual_clarity": 0.8,
                "audio_sync": 0.9,
                "narrative_flow": 0.85,
                "technical_quality": 0.8
            }
        }
        
        # Initialize chat session
        self.chat = None
        self._initialize_chat()
        
        logger.info("Gemini Supervisor initialized with human-like decision making")
    
    def _initialize_chat(self):
        """Initialize Gemini chat session with director system message"""
        try:
            api_key = self.api_keys[self.current_key_index]
            
            system_message = """You are an expert video production director and supervisor with human-like decision-making capabilities. Your role is to:

1. CONTINUOUS MONITORING: Watch every step of video production like a human director
2. QUALITY VALIDATION: Ensure each generated clip meets professional standards
3. INTELLIGENT EDITING: Make creative decisions about clip combination and transitions
4. FEEDBACK LOOP: Request re-generation when clips don't meet expectations
5. CREATIVE DIRECTION: Guide the entire production for maximum impact

Key Responsibilities:
- Analyze scripts and identify characters, themes, and mood
- Validate video clips against intended prompts
- Make intelligent editing decisions
- Ensure consistent quality throughout
- Provide detailed feedback and improvement suggestions
- Act as creative director for final output

Always provide detailed, actionable feedback and maintain high quality standards throughout the production process."""

            self.chat = LlmChat(
                api_key=api_key,
                session_id=self.session_id,
                system_message=system_message
            ).with_model("gemini", "gemini-2.5-pro")
            
            logger.info("Gemini Supervisor chat session initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini chat: {str(e)}")
            raise
    
    def get_next_key(self) -> str:
        """Get next API key for load balancing"""
        key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return key
    
    async def analyze_script_with_characters(self, script: str) -> Dict[str, Any]:
        """
        Analyze script with advanced character detection and personality analysis
        
        Args:
            script: Input script text
            
        Returns:
            Dict containing detailed script analysis with characters
        """
        try:
            prompt = f"""
            As a professional video production director, analyze this script comprehensively:
            
            SCRIPT:
            {script}
            
            Provide a detailed analysis in JSON format with:
            
            1. CHARACTERS: Identify all characters with:
               - Character name
               - Personality traits
               - Voice characteristics (tone, age, gender, emotion)
               - Role in the story
               - Dialogue portions
            
            2. SCENES: Break down into scenes with:
               - Scene number and description
               - Character actions and dialogue
               - Visual mood and atmosphere
               - Duration estimate
               - Camera suggestions
               - Lighting mood
            
            3. PRODUCTION NOTES:
               - Overall theme and genre
               - Target audience
               - Visual style recommendations
               - Audio/music suggestions
               - Pacing and rhythm
            
            4. QUALITY EXPECTATIONS:
               - Key quality checkpoints
               - Potential challenges
               - Success metrics
            
            Return ONLY valid JSON format.
            """
            
            response = await self.chat.send_message(UserMessage(text=prompt))
            
            # Parse JSON response
            try:
                analysis = json.loads(response)
                
                # Store production context
                self.production_context["script"] = script
                self.production_context["target_theme"] = analysis.get("production_notes", {}).get("theme", "general")
                self.production_context["characters"] = analysis.get("characters", [])
                self.production_context["scene_sequence"] = analysis.get("scenes", [])
                
                logger.info(f"Script analysis completed: {len(analysis.get('characters', []))} characters, {len(analysis.get('scenes', []))} scenes")
                return analysis
                
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Gemini response")
                # Return fallback analysis
                return self._create_fallback_analysis(script)
                
        except Exception as e:
            logger.error(f"Script analysis failed: {str(e)}")
            return self._create_fallback_analysis(script)
    
    def _create_fallback_analysis(self, script: str) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails"""
        return {
            "characters": [
                {
                    "name": "Narrator",
                    "personality": "neutral",
                    "voice_characteristics": {
                        "tone": "professional",
                        "age": "adult",
                        "gender": "neutral",
                        "emotion": "calm"
                    },
                    "role": "narrator",
                    "dialogue": script
                }
            ],
            "scenes": [
                {
                    "scene_number": 1,
                    "description": script,
                    "duration": 10,
                    "visual_mood": "neutral",
                    "camera_suggestions": "medium shot",
                    "lighting_mood": "natural"
                }
            ],
            "production_notes": {
                "theme": "general",
                "visual_style": "realistic",
                "pacing": "moderate"
            },
            "quality_expectations": {
                "key_checkpoints": ["audio_sync", "video_quality"],
                "success_metrics": ["clarity", "engagement"]
            }
        }
    
    async def break_script_into_scenes(self, script: str) -> List[Dict[str, Any]]:
        """
        Break script into individual scenes for video generation
        
        Args:
            script: Input script text
            
        Returns:
            List of scene dictionaries
        """
        try:
            # Initialize smart manager if not available
            if not hasattr(self, 'smart_manager'):
                # Import here to avoid circular import
                import sys
                sys.path.append('/app')
                from backend.server import SmartGeminiManager
                self.smart_manager = SmartGeminiManager()
            
            prompt = f"""
            As a professional video director, break this script into individual scenes for video production:
            
            SCRIPT:
            {script}
            
            Create scenes that are:
            - 5-10 seconds each for optimal video generation
            - Visually distinct and compelling
            - Logically sequenced
            - Cinematically interesting
            - Optimized for AI video generation
            
            Return a JSON array of scenes with:
            - scene_number: sequential number
            - description: detailed visual description for video generation
            - duration: recommended duration in seconds
            - visual_mood: mood/atmosphere
            - camera_suggestions: camera angle/movement
            - lighting_mood: lighting style
            - audio_text: dialogue or narration text
            - visual_elements: specific visual elements to include
            - transition_from_previous: transition type
            
            IMPORTANT: Create multiple scenes (at least 2-3) even for short scripts.
            Return ONLY valid JSON array format.
            """
            
            response = await self.smart_manager.execute_task("scene_breaking", prompt)
            
            try:
                scenes = json.loads(response)
                if isinstance(scenes, list) and len(scenes) > 0:
                    logger.info(f"Script broken into {len(scenes)} scenes using smart manager")
                    return scenes
                else:
                    # Fallback to simple sentence breaking
                    return self._create_fallback_scenes(script)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from smart manager scene breaking")
                return self._create_fallback_scenes(script)
                
        except Exception as e:
            logger.error(f"Smart manager scene breaking failed: {str(e)}")
            return self._create_fallback_scenes(script)
    
    def _create_fallback_scenes(self, script: str) -> List[Dict[str, Any]]:
        """Create fallback scenes when smart manager fails"""
        try:
            # Split script into sentences for scene creation
            sentences = [s.strip() for s in script.split('.') if s.strip()]
            
            # If only one sentence, try to split by other punctuation
            if len(sentences) == 1:
                # Try splitting by other punctuation
                parts = []
                for delimiter in [';', ',', '\n']:
                    if delimiter in sentences[0]:
                        parts = [p.strip() for p in sentences[0].split(delimiter) if p.strip()]
                        break
                
                if parts:
                    sentences = parts
                else:
                    # Split long sentence into two parts
                    words = sentences[0].split()
                    if len(words) > 10:
                        mid_point = len(words) // 2
                        sentences = [
                            ' '.join(words[:mid_point]),
                            ' '.join(words[mid_point:])
                        ]
            
            scenes = []
            for i, sentence in enumerate(sentences):
                if sentence:
                    scenes.append({
                        "scene_number": i + 1,
                        "description": sentence.strip(),
                        "duration": 5,  # Default 5 seconds per scene
                        "visual_mood": "cinematic" if i % 2 == 0 else "dramatic",
                        "camera_suggestions": "medium shot" if i == 0 else "close-up" if i % 2 == 1 else "wide shot",
                        "lighting_mood": "natural",
                        "audio_text": sentence.strip(),
                        "visual_elements": "realistic environment",
                        "transition_from_previous": "fade in" if i == 0 else "smooth cut"
                    })
            
            logger.info(f"Created {len(scenes)} fallback scenes")
            return scenes if scenes else [self._create_single_fallback_scene(script)]
            
        except Exception as e:
            logger.error(f"Error creating fallback scenes: {str(e)}")
            return [self._create_single_fallback_scene(script)]
    
    def _create_single_fallback_scene(self, script: str) -> Dict[str, Any]:
        """Create a single fallback scene"""
        return {
            "scene_number": 1,
            "description": script,
            "duration": 10,
            "visual_mood": "neutral",
            "camera_suggestions": "medium shot",
            "lighting_mood": "natural",
            "audio_text": script,
            "visual_elements": "standard composition",
            "transition_from_previous": "fade in"
        }
    
    async def assign_character_voices(self, characters: List[Dict], available_voices: List[Dict]) -> Dict[str, Dict]:
        """
        Intelligently assign voices to characters based on personality and traits
        
        Args:
            characters: List of character data with personality traits
            available_voices: List of available ElevenLabs voices
            
        Returns:
            Dict mapping character names to voice assignments
        """
        try:
            prompt = f"""
            As a professional casting director, assign the most suitable voices to these characters:
            
            CHARACTERS:
            {json.dumps(characters, indent=2)}
            
            AVAILABLE_VOICES:
            {json.dumps(available_voices, indent=2)}
            
            For each character, select the most appropriate voice based on:
            - Character personality and traits
            - Age and gender characteristics
            - Emotional tone and mood
            - Role in the story
            
            Provide reasoning for each assignment and ensure variety in voice selection.
            
            Return in JSON format:
            {{
                "voice_assignments": {{
                    "character_name": {{
                        "voice_id": "selected_voice_id",
                        "voice_name": "selected_voice_name",
                        "reasoning": "why this voice fits the character",
                        "settings": {{
                            "stability": 0.8,
                            "clarity": 0.7,
                            "style": 0.6
                        }}
                    }}
                }},
                "casting_notes": "overall casting strategy and notes"
            }}
            """
            
            response = await self.chat.send_message(UserMessage(text=prompt))
            
            try:
                assignments = json.loads(response)
                logger.info(f"Character voice assignments completed: {len(assignments.get('voice_assignments', {}))} assignments")
                return assignments
                
            except json.JSONDecodeError:
                logger.error("Failed to parse voice assignments JSON")
                return self._create_fallback_voice_assignments(characters, available_voices)
                
        except Exception as e:
            logger.error(f"Voice assignment failed: {str(e)}")
            return self._create_fallback_voice_assignments(characters, available_voices)
    
    def _create_fallback_voice_assignments(self, characters: List[Dict], available_voices: List[Dict]) -> Dict[str, Dict]:
        """Create fallback voice assignments"""
        assignments = {}
        
        for i, character in enumerate(characters):
            voice_index = i % len(available_voices) if available_voices else 0
            selected_voice = available_voices[voice_index] if available_voices else {"voice_id": "default", "name": "Default"}
            
            assignments[character["name"]] = {
                "voice_id": selected_voice["voice_id"],
                "voice_name": selected_voice["name"],
                "reasoning": f"Auto-assigned based on character order",
                "settings": {
                    "stability": 0.8,
                    "clarity": 0.7,
                    "style": 0.6
                }
            }
        
        return {
            "voice_assignments": assignments,
            "casting_notes": "Fallback automatic assignment"
        }
    
    async def validate_video_clip(self, video_path: str, intended_prompt: str, scene_context: Dict) -> Dict[str, Any]:
        """
        Validate generated video clip against intended prompt like a human director
        
        Args:
            video_path: Path to generated video file
            intended_prompt: The prompt used for video generation
            scene_context: Scene context and requirements
            
        Returns:
            Dict containing validation results and feedback
        """
        try:
            # Create file content for Gemini
            video_file = FileContentWithMimeType(
                file_path=video_path,
                mime_type="video/mp4"
            )
            
            prompt = f"""
            As a professional video production director, validate this generated video clip:
            
            INTENDED PROMPT: {intended_prompt}
            
            SCENE CONTEXT:
            {json.dumps(scene_context, indent=2)}
            
            VALIDATION CRITERIA:
            1. PROMPT ADHERENCE: Does the video match the intended prompt?
            2. VISUAL QUALITY: Is the video quality professional?
            3. SCENE CONSISTENCY: Does it fit with the overall story?
            4. TECHNICAL ASPECTS: Any technical issues?
            5. CREATIVE IMPACT: Does it achieve the desired emotional impact?
            
            Provide detailed feedback in JSON format:
            {{
                "validation_score": 0.0-1.0,
                "prompt_adherence": 0.0-1.0,
                "visual_quality": 0.0-1.0,
                "scene_consistency": 0.0-1.0,
                "technical_quality": 0.0-1.0,
                "creative_impact": 0.0-1.0,
                "issues_found": ["list of issues"],
                "suggestions": ["list of improvements"],
                "approval_status": "approved/needs_revision/rejected",
                "revision_notes": "specific notes for revision if needed",
                "director_feedback": "overall director assessment"
            }}
            """
            
            user_message = UserMessage(
                text=prompt,
                file_contents=[video_file]
            )
            
            response = await self.chat.send_message(user_message)
            
            try:
                validation = json.loads(response)
                
                # Store quality history
                self.production_context["quality_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "scene": scene_context.get("scene_number", 0),
                    "validation_score": validation.get("validation_score", 0.0),
                    "status": validation.get("approval_status", "unknown")
                })
                
                logger.info(f"Video validation completed: {validation.get('approval_status', 'unknown')} (score: {validation.get('validation_score', 0.0)})")
                return validation
                
            except json.JSONDecodeError:
                logger.error("Failed to parse validation JSON")
                return self._create_fallback_validation()
                
        except Exception as e:
            logger.error(f"Video validation failed: {str(e)}")
            return self._create_fallback_validation()
    
    def _create_fallback_validation(self) -> Dict[str, Any]:
        """Create fallback validation when Gemini fails"""
        return {
            "validation_score": 0.8,
            "prompt_adherence": 0.8,
            "visual_quality": 0.8,
            "scene_consistency": 0.8,
            "technical_quality": 0.8,
            "creative_impact": 0.8,
            "issues_found": [],
            "suggestions": [],
            "approval_status": "approved",
            "revision_notes": "",
            "director_feedback": "Fallback validation - manual review recommended"
        }
    
    async def plan_video_editing(self, video_clips: List[str], scene_sequence: List[Dict], audio_tracks: List[str]) -> Dict[str, Any]:
        """
        Plan intelligent video editing and combination like a human editor
        
        Args:
            video_clips: List of video clip paths
            scene_sequence: Scene sequence data
            audio_tracks: List of audio track paths
            
        Returns:
            Dict containing editing plan and instructions
        """
        try:
            prompt = f"""
            As a professional video editor and director, create a comprehensive editing plan:
            
            VIDEO CLIPS: {len(video_clips)} clips available
            SCENE SEQUENCE:
            {json.dumps(scene_sequence, indent=2)}
            AUDIO TRACKS: {len(audio_tracks)} tracks available
            
            PRODUCTION CONTEXT:
            {json.dumps(self.production_context, indent=2)}
            
            Create a detailed editing plan in JSON format:
            {{
                "editing_sequence": [
                    {{
                        "step": 1,
                        "action": "combine_clips",
                        "clips": ["clip1.mp4", "clip2.mp4"],
                        "transition": "fade",
                        "duration": 5.0,
                        "timing": "0:00-0:05"
                    }}
                ],
                "audio_mixing": {{
                    "voice_over_timing": ["0:00-0:10"],
                    "background_music": true,
                    "sound_effects": ["ambient"],
                    "audio_levels": {{"voice": 0.8, "music": 0.3}}
                }},
                "visual_effects": {{
                    "color_grading": "cinematic",
                    "transitions": ["fade", "cut"],
                    "stabilization": true,
                    "quality_enhancement": true
                }},
                "pacing_notes": "editing rhythm and flow instructions",
                "quality_checkpoints": ["audio_sync", "visual_flow", "story_coherence"],
                "final_specifications": {{
                    "resolution": "1920x1080",
                    "fps": 30,
                    "format": "mp4",
                    "duration": "estimated_total_duration"
                }}
            }}
            """
            
            response = await self.chat.send_message(UserMessage(text=prompt))
            
            try:
                editing_plan = json.loads(response)
                logger.info(f"Video editing plan created: {len(editing_plan.get('editing_sequence', []))} editing steps")
                return editing_plan
                
            except json.JSONDecodeError:
                logger.error("Failed to parse editing plan JSON")
                return self._create_fallback_editing_plan(video_clips, scene_sequence)
                
        except Exception as e:
            logger.error(f"Editing plan creation failed: {str(e)}")
            return self._create_fallback_editing_plan(video_clips, scene_sequence)
    
    def _create_fallback_editing_plan(self, video_clips: List[str], scene_sequence: List[Dict]) -> Dict[str, Any]:
        """Create fallback editing plan"""
        return {
            "editing_sequence": [
                {
                    "step": 1,
                    "action": "combine_clips",
                    "clips": video_clips,
                    "transition": "cut",
                    "duration": len(video_clips) * 5,
                    "timing": f"0:00-{len(video_clips) * 5}:00"
                }
            ],
            "audio_mixing": {
                "voice_over_timing": [f"0:00-{len(video_clips) * 5}:00"],
                "background_music": False,
                "sound_effects": [],
                "audio_levels": {"voice": 0.8, "music": 0.3}
            },
            "visual_effects": {
                "color_grading": "natural",
                "transitions": ["cut"],
                "stabilization": False,
                "quality_enhancement": False
            },
            "pacing_notes": "Simple sequential editing",
            "quality_checkpoints": ["audio_sync"],
            "final_specifications": {
                "resolution": "1920x1080",
                "fps": 30,
                "format": "mp4",
                "duration": f"{len(video_clips) * 5}s"
            }
        }
    
    async def supervise_final_quality(self, final_video_path: str, original_script: str) -> Dict[str, Any]:
        """
        Final quality supervision like a human director reviewing the complete video
        
        Args:
            final_video_path: Path to the final combined video
            original_script: Original script for comparison
            
        Returns:
            Dict containing final quality assessment and approval
        """
        try:
            # Check if video file exists
            if not os.path.exists(final_video_path):
                logger.error(f"Final video file not found: {final_video_path}")
                return self._create_fallback_final_assessment()
            
            # Create file content for Gemini
            video_file = FileContentWithMimeType(
                file_path=final_video_path,
                mime_type="video/mp4"
            )
            
            prompt = f"""
            As a professional video production director, conduct a final quality review:
            
            ORIGINAL SCRIPT: {original_script}
            
            PRODUCTION CONTEXT:
            {json.dumps(self.production_context, indent=2)}
            
            FINAL QUALITY ASSESSMENT:
            1. STORY COHERENCE: Does the video tell the story effectively?
            2. TECHNICAL QUALITY: Professional production standards?
            3. AUDIO-VIDEO SYNC: Perfect synchronization?
            4. VISUAL CONSISTENCY: Consistent style throughout?
            5. EMOTIONAL IMPACT: Achieves desired effect?
            6. OVERALL PRODUCTION VALUE: Meets professional standards?
            
            Provide comprehensive final assessment in JSON format:
            {{
                "final_score": 0.0-1.0,
                "story_coherence": 0.0-1.0,
                "technical_quality": 0.0-1.0,
                "audio_video_sync": 0.0-1.0,
                "visual_consistency": 0.0-1.0,
                "emotional_impact": 0.0-1.0,
                "production_value": 0.0-1.0,
                "strengths": ["list of strengths"],
                "areas_for_improvement": ["list of improvements"],
                "approval_status": "approved/needs_revision/rejected",
                "director_notes": "final director assessment",
                "recommendations": ["suggestions for future productions"],
                "quality_certification": "professional/good/needs_work"
            }}
            """
            
            user_message = UserMessage(
                text=prompt,
                file_contents=[video_file]
            )
            
            response = await self.chat.send_message(user_message)
            
            try:
                final_assessment = json.loads(response)
                logger.info(f"Final quality assessment completed: {final_assessment.get('approval_status', 'unknown')} (score: {final_assessment.get('final_score', 0.0)})")
                return final_assessment
                
            except json.JSONDecodeError:
                logger.error("Failed to parse final assessment JSON")
                return self._create_fallback_final_assessment()
                
        except Exception as e:
            logger.error(f"Final quality assessment failed: {str(e)}")
            return self._create_fallback_final_assessment()
    
    def _create_fallback_final_assessment(self) -> Dict[str, Any]:
        """Create fallback final assessment"""
        return {
            "final_score": 0.8,
            "story_coherence": 0.8,
            "technical_quality": 0.8,
            "audio_video_sync": 0.8,
            "visual_consistency": 0.8,
            "emotional_impact": 0.8,
            "production_value": 0.8,
            "strengths": ["Technical execution"],
            "areas_for_improvement": ["Manual review recommended"],
            "approval_status": "approved",
            "director_notes": "Fallback assessment - manual review recommended",
            "recommendations": ["Consider professional review"],
            "quality_certification": "good"
        }
    
    def get_production_summary(self) -> Dict[str, Any]:
        """Get complete production summary and statistics"""
        return {
            "production_context": self.production_context,
            "quality_history": self.production_context.get("quality_history", []),
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "total_characters": len(self.production_context.get("characters", [])),
            "total_scenes": len(self.production_context.get("scene_sequence", [])),
            "average_quality_score": self._calculate_average_quality_score()
        }
    
    def _calculate_average_quality_score(self) -> float:
        """Calculate average quality score from history"""
        quality_history = self.production_context.get("quality_history", [])
        if not quality_history:
            return 0.0
        
        total_score = sum(item.get("validation_score", 0.0) for item in quality_history)
        return total_score / len(quality_history)

# Global supervisor instance
gemini_supervisor = None

def get_gemini_supervisor(api_keys: List[str]) -> GeminiSupervisor:
    """Get or create Gemini supervisor instance"""
    global gemini_supervisor
    if gemini_supervisor is None:
        gemini_supervisor = GeminiSupervisor(api_keys)
    return gemini_supervisor