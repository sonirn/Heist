#!/usr/bin/env python3
"""
Enhanced Multi-Character Voice Manager
Intelligent voice assignment and generation for multiple characters
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
import requests
import aiohttp
import aiofiles

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiCharacterVoiceManager:
    """
    Enhanced Multi-Character Voice Manager
    
    This class provides intelligent voice assignment and generation for multiple
    characters based on their personalities and traits.
    """
    
    def __init__(self, elevenlabs_api_key: str):
        """
        Initialize multi-character voice manager
        
        Args:
            elevenlabs_api_key: ElevenLabs API key
        """
        self.api_key = elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Voice categories based on character traits
        self.voice_categories = {
            "narrator": {
                "preferred_traits": ["professional", "clear", "authoritative"],
                "voice_settings": {"stability": 0.8, "clarity": 0.9, "style": 0.5}
            },
            "protagonist": {
                "preferred_traits": ["engaging", "warm", "confident"],
                "voice_settings": {"stability": 0.7, "clarity": 0.8, "style": 0.7}
            },
            "antagonist": {
                "preferred_traits": ["dramatic", "deep", "intimidating"],
                "voice_settings": {"stability": 0.9, "clarity": 0.7, "style": 0.8}
            },
            "child": {
                "preferred_traits": ["young", "high-pitched", "energetic"],
                "voice_settings": {"stability": 0.6, "clarity": 0.8, "style": 0.9}
            },
            "elderly": {
                "preferred_traits": ["wise", "experienced", "calm"],
                "voice_settings": {"stability": 0.9, "clarity": 0.8, "style": 0.6}
            },
            "character": {
                "preferred_traits": ["distinctive", "memorable", "expressive"],
                "voice_settings": {"stability": 0.7, "clarity": 0.7, "style": 0.8}
            }
        }
        
        # Available voices cache
        self.available_voices = []
        self.voice_assignments = {}
        
        logger.info("Multi-character voice manager initialized")
    
    async def get_available_voices(self) -> List[Dict]:
        """
        Get available voices from ElevenLabs
        
        Returns:
            List of available voice data
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/voices", headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        voices = data.get("voices", [])
                        
                        # Process and categorize voices
                        processed_voices = []
                        for voice in voices:
                            processed_voice = {
                                "voice_id": voice.get("voice_id"),
                                "name": voice.get("name"),
                                "category": voice.get("category", "general"),
                                "description": voice.get("description", ""),
                                "gender": self._detect_gender(voice.get("name", "")),
                                "age_group": self._detect_age_group(voice.get("name", "")),
                                "accent": voice.get("accent", "american"),
                                "use_cases": voice.get("use_cases", []),
                                "labels": voice.get("labels", {}),
                                "preview_url": voice.get("preview_url")
                            }
                            processed_voices.append(processed_voice)
                        
                        self.available_voices = processed_voices
                        logger.info(f"Retrieved {len(processed_voices)} available voices")
                        return processed_voices
                    else:
                        logger.error(f"Failed to get voices: {response.status}")
                        return self._get_fallback_voices()
                        
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return self._get_fallback_voices()
    
    def _detect_gender(self, voice_name: str) -> str:
        """Detect gender from voice name"""
        male_indicators = ["adam", "alex", "daniel", "ethan", "josh", "marcus", "charlie", "brian", "luke", "sam"]
        female_indicators = ["alice", "bella", "domi", "elli", "emily", "grace", "charlotte", "jessica", "rachel", "sarah"]
        
        name_lower = voice_name.lower()
        
        if any(indicator in name_lower for indicator in male_indicators):
            return "male"
        elif any(indicator in name_lower for indicator in female_indicators):
            return "female"
        else:
            return "neutral"
    
    def _detect_age_group(self, voice_name: str) -> str:
        """Detect age group from voice name"""
        young_indicators = ["bella", "elli", "josh", "charlie"]
        mature_indicators = ["adam", "daniel", "grace", "charlotte"]
        
        name_lower = voice_name.lower()
        
        if any(indicator in name_lower for indicator in young_indicators):
            return "young"
        elif any(indicator in name_lower for indicator in mature_indicators):
            return "mature"
        else:
            return "adult"
    
    def _get_fallback_voices(self) -> List[Dict]:
        """Get fallback voices when API fails"""
        return [
            {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "name": "Rachel",
                "category": "narrative",
                "description": "Professional female narrator",
                "gender": "female",
                "age_group": "adult",
                "accent": "american",
                "use_cases": ["narration", "storytelling"],
                "labels": {"accent": "american", "use_case": "narration"}
            },
            {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",
                "name": "Domi",
                "category": "conversational",
                "description": "Confident female voice",
                "gender": "female",
                "age_group": "adult",
                "accent": "american",
                "use_cases": ["conversation", "character"],
                "labels": {"accent": "american", "use_case": "conversation"}
            },
            {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "category": "character",
                "description": "Young female voice",
                "gender": "female",
                "age_group": "young",
                "accent": "american",
                "use_cases": ["character", "storytelling"],
                "labels": {"accent": "american", "use_case": "character"}
            },
            {
                "voice_id": "ErXwobaYiN019PkySvjV",
                "name": "Antoni",
                "category": "narrative",
                "description": "Professional male narrator",
                "gender": "male",
                "age_group": "adult",
                "accent": "american",
                "use_cases": ["narration", "storytelling"],
                "labels": {"accent": "american", "use_case": "narration"}
            },
            {
                "voice_id": "VR6AewLTigWG4xSOukaG",
                "name": "Arnold",
                "category": "conversational",
                "description": "Mature male voice",
                "gender": "male",
                "age_group": "mature",
                "accent": "american",
                "use_cases": ["conversation", "character"],
                "labels": {"accent": "american", "use_case": "conversation"}
            }
        ]
    
    async def assign_voices_to_characters(self, characters: List[Dict], voice_assignments: Dict = None) -> Dict[str, Dict]:
        """
        Intelligently assign voices to characters
        
        Args:
            characters: List of character data with personality traits
            voice_assignments: Optional pre-assigned voice mappings from Gemini supervisor
            
        Returns:
            Dict mapping character names to voice data
        """
        try:
            if not self.available_voices:
                await self.get_available_voices()
            
            assignments = {}
            used_voices = set()
            
            # Use Gemini supervisor assignments if available
            if voice_assignments and "voice_assignments" in voice_assignments:
                gemini_assignments = voice_assignments["voice_assignments"]
                
                for char_name, assignment in gemini_assignments.items():
                    voice_id = assignment.get("voice_id")
                    
                    # Find the voice in available voices
                    selected_voice = None
                    for voice in self.available_voices:
                        if voice["voice_id"] == voice_id:
                            selected_voice = voice
                            break
                    
                    if selected_voice:
                        assignments[char_name] = {
                            "voice_data": selected_voice,
                            "settings": assignment.get("settings", {}),
                            "reasoning": assignment.get("reasoning", "Gemini supervisor assignment"),
                            "assignment_method": "gemini_supervised"
                        }
                        used_voices.add(voice_id)
                        logger.info(f"Assigned voice {selected_voice['name']} to character {char_name} (Gemini supervised)")
            
            # Assign remaining characters
            for character in characters:
                char_name = character.get("name", "Unknown")
                
                if char_name in assignments:
                    continue  # Already assigned by Gemini
                
                # Determine character category
                char_traits = character.get("personality", "").lower()
                char_role = character.get("role", "character").lower()
                
                category = self._determine_character_category(char_role, char_traits)
                
                # Find best matching voice
                best_voice = self._find_best_voice_match(character, category, used_voices)
                
                if best_voice:
                    voice_settings = self.voice_categories[category]["voice_settings"].copy()
                    
                    # Adjust settings based on character traits
                    voice_settings = self._adjust_voice_settings(voice_settings, character)
                    
                    assignments[char_name] = {
                        "voice_data": best_voice,
                        "settings": voice_settings,
                        "reasoning": f"Matched based on {category} category and character traits",
                        "assignment_method": "intelligent_matching"
                    }
                    used_voices.add(best_voice["voice_id"])
                    logger.info(f"Assigned voice {best_voice['name']} to character {char_name} (intelligent matching)")
            
            self.voice_assignments = assignments
            return assignments
            
        except Exception as e:
            logger.error(f"Voice assignment failed: {str(e)}")
            return {}
    
    def _determine_character_category(self, role: str, traits: str) -> str:
        """Determine character category based on role and traits"""
        if "narrator" in role:
            return "narrator"
        elif "protagonist" in role or "hero" in role or "main" in role:
            return "protagonist"
        elif "antagonist" in role or "villain" in role:
            return "antagonist"
        elif "child" in traits or "young" in traits or "kid" in traits:
            return "child"
        elif "elderly" in traits or "old" in traits or "wise" in traits:
            return "elderly"
        else:
            return "character"
    
    def _find_best_voice_match(self, character: Dict, category: str, used_voices: set) -> Optional[Dict]:
        """Find the best matching voice for a character"""
        available_voices = [v for v in self.available_voices if v["voice_id"] not in used_voices]
        
        if not available_voices:
            # If all voices are used, allow reuse
            available_voices = self.available_voices
        
        # Get character requirements
        char_gender = character.get("voice_characteristics", {}).get("gender", "neutral")
        char_age = character.get("voice_characteristics", {}).get("age", "adult")
        
        # Score voices based on matching criteria
        scored_voices = []
        
        for voice in available_voices:
            score = 0
            
            # Gender matching
            if char_gender != "neutral" and voice["gender"] == char_gender:
                score += 3
            elif voice["gender"] == "neutral":
                score += 1
            
            # Age group matching
            if char_age == "child" and voice["age_group"] == "young":
                score += 2
            elif char_age == "adult" and voice["age_group"] == "adult":
                score += 2
            elif char_age == "elderly" and voice["age_group"] == "mature":
                score += 2
            
            # Category matching
            if category == "narrator" and voice["category"] == "narrative":
                score += 3
            elif category in ["protagonist", "antagonist"] and voice["category"] == "conversational":
                score += 2
            elif category == "character" and voice["category"] == "character":
                score += 2
            
            # Use case matching
            if category == "narrator" and "narration" in voice.get("use_cases", []):
                score += 2
            elif category != "narrator" and "character" in voice.get("use_cases", []):
                score += 1
            
            scored_voices.append((voice, score))
        
        # Sort by score and return best match
        scored_voices.sort(key=lambda x: x[1], reverse=True)
        
        return scored_voices[0][0] if scored_voices else None
    
    def _adjust_voice_settings(self, base_settings: Dict, character: Dict) -> Dict:
        """Adjust voice settings based on character traits"""
        settings = base_settings.copy()
        
        char_traits = character.get("personality", "").lower()
        char_emotion = character.get("voice_characteristics", {}).get("emotion", "neutral")
        
        # Adjust based on emotional state
        if char_emotion == "excited":
            settings["style"] = min(1.0, settings["style"] + 0.2)
        elif char_emotion == "calm":
            settings["stability"] = min(1.0, settings["stability"] + 0.1)
        elif char_emotion == "dramatic":
            settings["style"] = min(1.0, settings["style"] + 0.3)
        
        # Adjust based on personality traits
        if "confident" in char_traits:
            settings["clarity"] = min(1.0, settings["clarity"] + 0.1)
        elif "shy" in char_traits:
            settings["stability"] = min(1.0, settings["stability"] + 0.1)
            settings["style"] = max(0.0, settings["style"] - 0.1)
        
        return settings
    
    async def generate_character_speech(self, character_name: str, text: str, scene_context: Dict = None) -> Optional[bytes]:
        """
        Generate speech for a specific character
        
        Args:
            character_name: Name of the character
            text: Text to convert to speech
            scene_context: Optional scene context for emotional adjustments
            
        Returns:
            Audio data in bytes
        """
        try:
            if character_name not in self.voice_assignments:
                logger.error(f"No voice assignment found for character: {character_name}")
                return None
            
            assignment = self.voice_assignments[character_name]
            voice_data = assignment["voice_data"]
            voice_settings = assignment["settings"]
            
            # Adjust settings based on scene context
            if scene_context:
                voice_settings = self._adjust_settings_for_scene(voice_settings, scene_context)
            
            # Generate speech
            audio_data = await self._generate_speech_with_voice(
                text, 
                voice_data["voice_id"], 
                voice_settings
            )
            
            if audio_data:
                logger.info(f"Generated speech for character {character_name}: {len(audio_data)} bytes")
                return audio_data
            else:
                logger.error(f"Failed to generate speech for character {character_name}")
                return None
                
        except Exception as e:
            logger.error(f"Character speech generation failed: {str(e)}")
            return None
    
    def _adjust_settings_for_scene(self, base_settings: Dict, scene_context: Dict) -> Dict:
        """Adjust voice settings based on scene context"""
        settings = base_settings.copy()
        
        scene_mood = scene_context.get("mood", "neutral").lower()
        
        if scene_mood == "tense":
            settings["stability"] = max(0.0, settings["stability"] - 0.1)
            settings["style"] = min(1.0, settings["style"] + 0.1)
        elif scene_mood == "calm":
            settings["stability"] = min(1.0, settings["stability"] + 0.1)
            settings["style"] = max(0.0, settings["style"] - 0.1)
        elif scene_mood == "dramatic":
            settings["style"] = min(1.0, settings["style"] + 0.2)
        
        return settings
    
    async def _generate_speech_with_voice(self, text: str, voice_id: str, voice_settings: Dict) -> Optional[bytes]:
        """Generate speech using specific voice and settings"""
        try:
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            data = {
                "text": text,
                "voice_settings": voice_settings,
                "model_id": "eleven_multilingual_v2"
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"Speech generation failed: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Speech generation API call failed: {str(e)}")
            return None
    
    async def generate_multi_character_audio(self, dialogue_sequence: List[Dict]) -> List[Dict]:
        """
        Generate audio for multiple characters in sequence
        
        Args:
            dialogue_sequence: List of dialogue items with character and text
            
        Returns:
            List of audio segments with character data
        """
        try:
            audio_segments = []
            
            for i, dialogue in enumerate(dialogue_sequence):
                character_name = dialogue.get("character", "Unknown")
                text = dialogue.get("text", "")
                scene_context = dialogue.get("scene_context", {})
                
                if not text.strip():
                    continue
                
                # Generate speech for this character
                audio_data = await self.generate_character_speech(
                    character_name, 
                    text, 
                    scene_context
                )
                
                if audio_data:
                    audio_segments.append({
                        "segment_id": i + 1,
                        "character": character_name,
                        "text": text,
                        "audio_data": audio_data,
                        "voice_info": self.voice_assignments.get(character_name, {}),
                        "duration": len(audio_data) / 16000 * 8,  # Rough estimate
                        "scene_context": scene_context
                    })
                    
                    logger.info(f"Generated audio segment {i + 1} for character {character_name}")
                else:
                    logger.warning(f"Failed to generate audio for character {character_name}")
            
            logger.info(f"Generated {len(audio_segments)} audio segments for multi-character dialogue")
            return audio_segments
            
        except Exception as e:
            logger.error(f"Multi-character audio generation failed: {str(e)}")
            return []
    
    def get_voice_assignment_summary(self) -> Dict[str, Any]:
        """Get summary of current voice assignments"""
        return {
            "total_characters": len(self.voice_assignments),
            "assignments": self.voice_assignments,
            "available_voices": len(self.available_voices),
            "voice_categories": list(self.voice_categories.keys()),
            "assignment_timestamp": datetime.now().isoformat()
        }

# Global multi-character voice manager instance
multi_voice_manager = None

def get_multi_voice_manager(api_key: str) -> MultiCharacterVoiceManager:
    """Get or create multi-character voice manager instance"""
    global multi_voice_manager
    if multi_voice_manager is None:
        multi_voice_manager = MultiCharacterVoiceManager(api_key)
    return multi_voice_manager