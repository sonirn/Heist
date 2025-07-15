#!/usr/bin/env python3
"""
Coqui TTS Voice Manager
Free, open-source text-to-speech implementation replacing ElevenLabs
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
import io
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoquiVoiceManager:
    """
    Coqui TTS Voice Manager
    
    This class provides intelligent voice assignment and generation for multiple
    characters using Coqui TTS as a free alternative to ElevenLabs.
    """
    
    def __init__(self):
        """
        Initialize Coqui TTS voice manager
        """
        self.tts_engine = None
        self.available_models = []
        self.voice_assignments = {}
        
        # Voice categories based on character traits
        self.voice_categories = {
            "narrator": {
                "preferred_traits": ["professional", "clear", "authoritative"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 1.0,
                "pitch": 1.0
            },
            "protagonist": {
                "preferred_traits": ["engaging", "warm", "confident"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 1.1,
                "pitch": 1.1
            },
            "antagonist": {
                "preferred_traits": ["dramatic", "deep", "intimidating"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 0.9,
                "pitch": 0.8
            },
            "child": {
                "preferred_traits": ["young", "high-pitched", "energetic"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 1.2,
                "pitch": 1.3
            },
            "elderly": {
                "preferred_traits": ["wise", "experienced", "calm"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 0.8,
                "pitch": 0.9
            },
            "character": {
                "preferred_traits": ["distinctive", "memorable", "expressive"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "speed": 1.0,
                "pitch": 1.0
            }
        }
        
        # Available voices (Coqui TTS models)
        self.available_voices = [
            {
                "voice_id": "coqui_narrator",
                "name": "Narrator Voice",
                "category": "narrator",
                "description": "Professional, clear, authoritative voice for narration",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_protagonist",
                "name": "Protagonist Voice",
                "category": "protagonist", 
                "description": "Engaging, warm, confident voice for main characters",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_antagonist",
                "name": "Antagonist Voice",
                "category": "antagonist",
                "description": "Dramatic, deep, intimidating voice for villains",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_child",
                "name": "Child Voice",
                "category": "child",
                "description": "Young, high-pitched, energetic voice for children",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_elderly",
                "name": "Elderly Voice",
                "category": "elderly",
                "description": "Wise, experienced, calm voice for elderly characters",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_character",
                "name": "Character Voice",
                "category": "character",
                "description": "Distinctive, memorable, expressive voice for unique characters",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            }
        ]
        
        # Initialize with fallback mode first
        self.fallback_mode = True
        
        logger.info("Coqui voice manager initialized in fallback mode")
    
    async def initialize_tts_engine(self):
        """Initialize the Coqui TTS engine"""
        try:
            # Try to import and initialize TTS
            from TTS.api import TTS
            
            # Initialize with a basic English model
            self.tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            self.fallback_mode = False
            logger.info("Coqui TTS engine initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize Coqui TTS engine: {str(e)}")
            logger.info("Running in fallback mode with synthetic audio")
            self.fallback_mode = True
            return False
    
    async def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices
        
        Returns:
            List of voice dictionaries with id, name, and category
        """
        return self.available_voices
    
    def detect_characters(self, script: str) -> List[Dict]:
        """
        Detect characters in the script
        
        Args:
            script: Input script text
            
        Returns:
            List of detected characters with traits
        """
        characters = []
        
        # Simple character detection based on common patterns
        lines = script.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                # Dialogue format: "CHARACTER: dialogue"
                char_name = line.split(':')[0].strip()
                if char_name and char_name not in [c['name'] for c in characters]:
                    characters.append({
                        'name': char_name,
                        'traits': self._analyze_character_traits(char_name, script),
                        'category': self._categorize_character(char_name, script)
                    })
        
        # If no characters detected, add narrator
        if not characters:
            characters.append({
                'name': 'Narrator',
                'traits': ['professional', 'clear', 'authoritative'],
                'category': 'narrator'
            })
        
        return characters
    
    def _analyze_character_traits(self, character_name: str, script: str) -> List[str]:
        """Analyze character traits from script"""
        traits = []
        
        # Simple trait analysis based on character name and context
        name_lower = character_name.lower()
        
        if any(word in name_lower for word in ['child', 'kid', 'boy', 'girl', 'baby']):
            traits.extend(['young', 'high-pitched', 'energetic'])
        elif any(word in name_lower for word in ['old', 'elder', 'grand']):
            traits.extend(['wise', 'experienced', 'calm'])
        elif any(word in name_lower for word in ['villain', 'bad', 'evil', 'dark']):
            traits.extend(['dramatic', 'deep', 'intimidating'])
        elif any(word in name_lower for word in ['hero', 'main', 'protagonist']):
            traits.extend(['engaging', 'warm', 'confident'])
        elif any(word in name_lower for word in ['narrator', 'voice']):
            traits.extend(['professional', 'clear', 'authoritative'])
        else:
            traits.extend(['distinctive', 'memorable', 'expressive'])
        
        return traits
    
    def _categorize_character(self, character_name: str, script: str) -> str:
        """Categorize character based on traits"""
        traits = self._analyze_character_traits(character_name, script)
        
        if 'young' in traits or 'high-pitched' in traits:
            return 'child'
        elif 'wise' in traits or 'experienced' in traits:
            return 'elderly'
        elif 'dramatic' in traits or 'intimidating' in traits:
            return 'antagonist'
        elif 'engaging' in traits or 'confident' in traits:
            return 'protagonist'
        elif 'professional' in traits or 'authoritative' in traits:
            return 'narrator'
        else:
            return 'character'
    
    async def assign_voices_to_characters(self, characters: List[Dict]) -> Dict:
        """
        Assign voices to characters based on their traits
        
        Args:
            characters: List of character dictionaries
            
        Returns:
            Dictionary mapping character names to voice assignments
        """
        voice_assignments = {}
        used_voices = set()
        
        for character in characters:
            char_name = character['name']
            category = character['category']
            
            # Find best matching voice for this character
            best_voice = None
            
            # First, try to find a voice from the same category
            for voice in self.available_voices:
                if voice['category'] == category and voice['voice_id'] not in used_voices:
                    best_voice = voice
                    break
            
            # If no voice found in category, use any available voice
            if not best_voice:
                for voice in self.available_voices:
                    if voice['voice_id'] not in used_voices:
                        best_voice = voice
                        break
            
            # If all voices are used, reuse the first one
            if not best_voice:
                best_voice = self.available_voices[0]
            
            voice_assignments[char_name] = {
                'voice_id': best_voice['voice_id'],
                'voice_name': best_voice['name'],
                'category': best_voice['category'],
                'settings': self.voice_categories[best_voice['category']]
            }
            
            used_voices.add(best_voice['voice_id'])
        
        self.voice_assignments = voice_assignments
        return voice_assignments
    
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
                logger.warning(f"No voice assigned to character: {character_name}")
                return None
            
            voice_config = self.voice_assignments[character_name]
            
            if not self.fallback_mode and self.tts_engine:
                # Use real Coqui TTS engine
                return await self._generate_with_coqui(text, voice_config)
            else:
                # Use fallback synthetic audio
                return await self._generate_fallback_audio(text, voice_config)
                
        except Exception as e:
            logger.error(f"Character speech generation failed: {str(e)}")
            return None
    
    async def _generate_with_coqui(self, text: str, voice_config: Dict) -> Optional[bytes]:
        """Generate speech using Coqui TTS"""
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech with Coqui TTS
            self.tts_engine.tts_to_file(text=text, file_path=temp_path)
            
            # Read the audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Coqui TTS generation failed: {str(e)}")
            return None
    
    async def _generate_fallback_audio(self, text: str, voice_config: Dict) -> Optional[bytes]:
        """Generate fallback synthetic audio"""
        try:
            # Create synthetic audio data based on text length and voice settings
            import wave
            import struct
            import math
            
            # Audio parameters
            sample_rate = 22050
            duration = max(1.0, len(text) * 0.1)  # Rough estimate based on text length
            
            # Get voice settings
            settings = voice_config.get('settings', {})
            base_freq = 200  # Base frequency
            
            # Adjust frequency based on voice category
            if voice_config['category'] == 'child':
                base_freq = 300
            elif voice_config['category'] == 'elderly':
                base_freq = 150
            elif voice_config['category'] == 'antagonist':
                base_freq = 120
            
            # Generate synthetic audio
            frames = []
            for i in range(int(sample_rate * duration)):
                # Simple sine wave with some variation
                t = i / sample_rate
                freq = base_freq + 50 * math.sin(2 * math.pi * t * 0.5)
                value = int(32767 * 0.3 * math.sin(2 * math.pi * freq * t))
                frames.append(struct.pack('<h', value))
            
            # Create WAV file in memory
            audio_buffer = io.BytesIO()
            with wave.open(audio_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(b''.join(frames))
            
            audio_data = audio_buffer.getvalue()
            
            logger.info(f"Generated fallback audio: {len(audio_data)} bytes for character '{voice_config['voice_name']}'")
            return audio_data
            
        except Exception as e:
            logger.error(f"Fallback audio generation failed: {str(e)}")
            return None
    
    async def generate_multi_character_audio(self, dialogue_sequence: List[Dict]) -> List[Dict]:
        """
        Generate audio for multiple characters in sequence
        
        Args:
            dialogue_sequence: List of dialogue items with character and text
            
        Returns:
            List of audio items with character name and audio data
        """
        audio_sequence = []
        
        for dialogue_item in dialogue_sequence:
            character_name = dialogue_item.get('character', 'Narrator')
            text = dialogue_item.get('text', '')
            scene_context = dialogue_item.get('scene_context', {})
            
            if text.strip():
                audio_data = await self.generate_character_speech(
                    character_name, text, scene_context
                )
                
                if audio_data:
                    audio_sequence.append({
                        'character': character_name,
                        'text': text,
                        'audio_data': audio_data,
                        'voice_info': self.voice_assignments.get(character_name, {})
                    })
                else:
                    logger.warning(f"Failed to generate audio for character: {character_name}")
        
        return audio_sequence
    
    def get_character_voices(self) -> Dict:
        """Get current character voice assignments"""
        return self.voice_assignments
    
    def get_voice_capabilities(self) -> Dict:
        """Get voice manager capabilities"""
        return {
            'total_voices': len(self.available_voices),
            'voice_categories': list(self.voice_categories.keys()),
            'character_detection': True,
            'multi_character_support': True,
            'real_time_generation': True,
            'fallback_mode': self.fallback_mode,
            'engine': "Coqui TTS" if not self.fallback_mode else "Fallback Synthetic"
        }

# Factory function to create voice manager
def get_coqui_voice_manager() -> CoquiVoiceManager:
    """Get Coqui voice manager instance"""
    return CoquiVoiceManager()