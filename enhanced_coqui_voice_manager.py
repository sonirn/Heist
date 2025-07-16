#!/usr/bin/env python3
"""
Enhanced Coqui TTS Voice Manager with Hindi Support and Multiple Character Voices
Free, open-source text-to-speech implementation with multilingual support
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
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCoquiVoiceManager:
    """
    Enhanced Coqui TTS Voice Manager with Hindi Support and Multiple Character Voices
    
    This class provides intelligent voice assignment and generation for multiple
    characters using Coqui TTS with multilingual support, focusing on Hindi.
    """
    
    def __init__(self):
        """
        Initialize Enhanced Coqui TTS voice manager with Hindi support
        """
        self.tts_engines = {}
        self.available_models = []
        self.voice_assignments = {}
        self.language_detector = None
        
        # Hindi-focused voice categories with specific character types
        self.hindi_voice_categories = {
            "hindi_narrator": {
                "preferred_traits": ["professional", "clear", "authoritative"],
                "model": "tts_models/hi/male/tacotron2-DDC",
                "language": "hi",
                "gender": "male",
                "speed": 1.0,
                "pitch": 1.0,
                "character_types": ["narrator", "storyteller", "announcer"]
            },
            "hindi_protagonist_male": {
                "preferred_traits": ["engaging", "warm", "confident", "heroic"],
                "model": "tts_models/hi/male/tacotron2-DDC",
                "language": "hi",
                "gender": "male",
                "speed": 1.1,
                "pitch": 1.1,
                "character_types": ["hero", "protagonist", "main_character"]
            },
            "hindi_protagonist_female": {
                "preferred_traits": ["engaging", "warm", "confident", "gentle"],
                "model": "tts_models/hi/female/tacotron2-DDC",
                "language": "hi",
                "gender": "female",
                "speed": 1.1,
                "pitch": 1.2,
                "character_types": ["heroine", "protagonist", "main_character"]
            },
            "hindi_antagonist": {
                "preferred_traits": ["dramatic", "deep", "intimidating", "powerful"],
                "model": "tts_models/hi/male/tacotron2-DDC",
                "language": "hi",
                "gender": "male",
                "speed": 0.9,
                "pitch": 0.8,
                "character_types": ["villain", "antagonist", "enemy"]
            },
            "hindi_child": {
                "preferred_traits": ["young", "high-pitched", "energetic", "innocent"],
                "model": "tts_models/hi/female/tacotron2-DDC",
                "language": "hi",
                "gender": "female",
                "speed": 1.3,
                "pitch": 1.4,
                "character_types": ["child", "kid", "young"]
            },
            "hindi_elderly": {
                "preferred_traits": ["wise", "experienced", "calm", "respectful"],
                "model": "tts_models/hi/male/tacotron2-DDC",
                "language": "hi",
                "gender": "male",
                "speed": 0.8,
                "pitch": 0.9,
                "character_types": ["elder", "grandfather", "wise_man"]
            },
            "hindi_female_character": {
                "preferred_traits": ["distinctive", "expressive", "emotional"],
                "model": "tts_models/hi/female/tacotron2-DDC",
                "language": "hi",
                "gender": "female",
                "speed": 1.0,
                "pitch": 1.1,
                "character_types": ["female_character", "woman", "mother"]
            },
            "hindi_male_character": {
                "preferred_traits": ["distinctive", "strong", "expressive"],
                "model": "tts_models/hi/male/tacotron2-DDC",
                "language": "hi",
                "gender": "male",
                "speed": 1.0,
                "pitch": 1.0,
                "character_types": ["male_character", "man", "father"]
            }
        }
        
        # English fallback categories
        self.english_voice_categories = {
            "english_narrator": {
                "preferred_traits": ["professional", "clear", "authoritative"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "language": "en",
                "speed": 1.0,
                "pitch": 1.0
            },
            "english_protagonist": {
                "preferred_traits": ["engaging", "warm", "confident"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "language": "en",
                "speed": 1.1,
                "pitch": 1.1
            },
            "english_antagonist": {
                "preferred_traits": ["dramatic", "deep", "intimidating"],
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "language": "en",
                "speed": 0.9,
                "pitch": 0.8
            }
        }
        
        # Combined voice categories
        self.voice_categories = {**self.hindi_voice_categories, **self.english_voice_categories}
        
        # Available Hindi voices (at least 6 as requested)
        self.available_hindi_voices = [
            {
                "voice_id": "coqui_hindi_narrator",
                "name": "Hindi Narrator (पुरुष कथावाचक)",
                "category": "hindi_narrator",
                "language": "hi",
                "gender": "male",
                "description": "Professional Hindi narrator voice for storytelling",
                "model": "tts_models/hi/male/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_protagonist_male",
                "name": "Hindi Male Hero (पुरुष नायक)",
                "category": "hindi_protagonist_male",
                "language": "hi",
                "gender": "male",
                "description": "Confident Hindi male protagonist voice",
                "model": "tts_models/hi/male/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_protagonist_female",
                "name": "Hindi Female Hero (महिला नायिका)",
                "category": "hindi_protagonist_female",
                "language": "hi",
                "gender": "female",
                "description": "Warm Hindi female protagonist voice",
                "model": "tts_models/hi/female/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_antagonist",
                "name": "Hindi Villain (खलनायक)",
                "category": "hindi_antagonist",
                "language": "hi",
                "gender": "male",
                "description": "Dramatic Hindi antagonist voice",
                "model": "tts_models/hi/male/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_child",
                "name": "Hindi Child (बच्चा)",
                "category": "hindi_child",
                "language": "hi",
                "gender": "female",
                "description": "Young energetic Hindi child voice",
                "model": "tts_models/hi/female/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_elderly",
                "name": "Hindi Elder (बुजुर्ग)",
                "category": "hindi_elderly",
                "language": "hi",
                "gender": "male",
                "description": "Wise Hindi elderly voice",
                "model": "tts_models/hi/male/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_female_character",
                "name": "Hindi Female Character (महिला पात्र)",
                "category": "hindi_female_character",
                "language": "hi",
                "gender": "female",
                "description": "Expressive Hindi female character voice",
                "model": "tts_models/hi/female/tacotron2-DDC"
            },
            {
                "voice_id": "coqui_hindi_male_character",
                "name": "Hindi Male Character (पुरुष पात्र)",
                "category": "hindi_male_character",
                "language": "hi",
                "gender": "male",
                "description": "Strong Hindi male character voice",
                "model": "tts_models/hi/male/tacotron2-DDC"
            }
        ]
        
        # English fallback voices
        self.available_english_voices = [
            {
                "voice_id": "english_narrator",
                "name": "English Narrator",
                "category": "english_narrator",
                "language": "en",
                "description": "Professional English narrator voice",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "english_protagonist",
                "name": "English Protagonist",
                "category": "english_protagonist",
                "language": "en",
                "description": "Engaging English protagonist voice",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            },
            {
                "voice_id": "english_antagonist",
                "name": "English Antagonist",
                "category": "english_antagonist",
                "language": "en",
                "description": "Dramatic English antagonist voice",
                "model": "tts_models/en/ljspeech/tacotron2-DDC"
            }
        ]
        
        # Combined available voices
        self.available_voices = self.available_hindi_voices + self.available_english_voices
        
        # Initialize with fallback mode first
        self.fallback_mode = True
        self.xtts_model = None
        
        logger.info(f"Enhanced Coqui voice manager initialized with {len(self.available_hindi_voices)} Hindi voices and {len(self.available_english_voices)} English voices")
    
    async def initialize_tts_engines(self):
        """Initialize the TTS engines with multilingual support"""
        try:
            # Initialize language detector
            try:
                from langdetect import detect
                self.language_detector = detect
                logger.info("Language detector initialized successfully")
            except ImportError:
                logger.warning("Language detector not available, using fallback detection")
            
            # Try to initialize XTTS-v2 for multilingual support
            try:
                from TTS.api import TTS
                
                # Try to load XTTS-v2 (supports 17 languages including Hindi)
                try:
                    self.xtts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
                    logger.info("XTTS-v2 multilingual model loaded successfully")
                    self.fallback_mode = False
                except Exception as e:
                    logger.warning(f"XTTS-v2 loading failed: {str(e)}, trying basic models")
                
                # Load basic Hindi models if available
                if not self.xtts_model:
                    try:
                        self.tts_engines['hindi'] = TTS(model_name="tts_models/hi/male/tacotron2-DDC", progress_bar=False)
                        logger.info("Hindi TTS model loaded successfully")
                        self.fallback_mode = False
                    except Exception as e:
                        logger.warning(f"Hindi TTS loading failed: {str(e)}")
                
                # Load English model as fallback
                try:
                    self.tts_engines['english'] = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
                    logger.info("English TTS model loaded successfully")
                    self.fallback_mode = False
                except Exception as e:
                    logger.warning(f"English TTS loading failed: {str(e)}")
                
            except ImportError:
                logger.warning("TTS library not available, using fallback mode")
                self.fallback_mode = True
            
            # Fallback to gTTS if Coqui TTS is not available
            if self.fallback_mode:
                try:
                    from gtts import gTTS
                    self.tts_engines['fallback'] = gTTS
                    logger.info("Using gTTS as fallback TTS engine")
                except ImportError:
                    logger.warning("gTTS not available, using synthetic audio")
            
            return True
            
        except Exception as e:
            logger.error(f"TTS engine initialization failed: {str(e)}")
            self.fallback_mode = True
            return False
    
    def detect_script_language(self, text: str) -> str:
        """
        Detect the primary language of the script
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code ('hi' for Hindi, 'en' for English, etc.)
        """
        try:
            # Check for Hindi characters (Devanagari script)
            hindi_pattern = re.compile(r'[\u0900-\u097F]')
            if hindi_pattern.search(text):
                return 'hi'
            
            # Use language detector if available
            if self.language_detector:
                detected_lang = self.language_detector(text)
                if detected_lang == 'hi':
                    return 'hi'
                elif detected_lang in ['en', 'english']:
                    return 'en'
            
            # Default to English if uncertain
            return 'en'
            
        except Exception as e:
            logger.warning(f"Language detection failed: {str(e)}, defaulting to English")
            return 'en'
    
    async def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices with language information
        
        Returns:
            List of voice dictionaries with id, name, category, and language
        """
        return self.available_voices
    
    def detect_characters(self, script: str) -> List[Dict]:
        """
        Detect characters in the script with language awareness
        
        Args:
            script: Input script text
            
        Returns:
            List of detected characters with traits and language information
        """
        characters = []
        script_language = self.detect_script_language(script)
        
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
                        'traits': self._analyze_character_traits(char_name, script, script_language),
                        'category': self._categorize_character(char_name, script, script_language),
                        'language': script_language
                    })
        
        # If no characters detected, add narrator
        if not characters:
            narrator_category = 'hindi_narrator' if script_language == 'hi' else 'english_narrator'
            characters.append({
                'name': 'Narrator',
                'traits': ['professional', 'clear', 'authoritative'],
                'category': narrator_category,
                'language': script_language
            })
        
        return characters
    
    def _analyze_character_traits(self, character_name: str, script: str, language: str) -> List[str]:
        """Analyze character traits from script with language awareness"""
        traits = []
        name_lower = character_name.lower()
        
        # Hindi-specific character analysis
        if language == 'hi':
            # Hindi words for character types
            hindi_child_words = ['बच्चा', 'बच्ची', 'लड़का', 'लड़की', 'child', 'kid', 'boy', 'girl']
            hindi_elder_words = ['बुजुर्ग', 'दादा', 'दादी', 'नाना', 'नानी', 'old', 'elder', 'grand']
            hindi_villain_words = ['खलनायक', 'दुष्ट', 'villain', 'bad', 'evil', 'dark']
            hindi_hero_words = ['नायक', 'नायिका', 'hero', 'heroine', 'main', 'protagonist']
            
            if any(word in name_lower for word in hindi_child_words):
                traits.extend(['young', 'high-pitched', 'energetic', 'innocent'])
            elif any(word in name_lower for word in hindi_elder_words):
                traits.extend(['wise', 'experienced', 'calm', 'respectful'])
            elif any(word in name_lower for word in hindi_villain_words):
                traits.extend(['dramatic', 'deep', 'intimidating', 'powerful'])
            elif any(word in name_lower for word in hindi_hero_words):
                traits.extend(['engaging', 'warm', 'confident', 'heroic'])
            else:
                traits.extend(['distinctive', 'expressive', 'emotional'])
        else:
            # English character analysis
            if any(word in name_lower for word in ['child', 'kid', 'boy', 'girl', 'baby']):
                traits.extend(['young', 'high-pitched', 'energetic'])
            elif any(word in name_lower for word in ['old', 'elder', 'grand']):
                traits.extend(['wise', 'experienced', 'calm'])
            elif any(word in name_lower for word in ['villain', 'bad', 'evil', 'dark']):
                traits.extend(['dramatic', 'deep', 'intimidating'])
            elif any(word in name_lower for word in ['hero', 'main', 'protagonist']):
                traits.extend(['engaging', 'warm', 'confident'])
            else:
                traits.extend(['distinctive', 'memorable', 'expressive'])
        
        return traits
    
    def _categorize_character(self, character_name: str, script: str, language: str) -> str:
        """Categorize character based on traits and language"""
        traits = self._analyze_character_traits(character_name, script, language)
        name_lower = character_name.lower()
        
        # Language-specific categorization
        if language == 'hi':
            # Hindi-specific categorization
            if 'young' in traits or 'innocent' in traits:
                return 'hindi_child'
            elif 'wise' in traits or 'experienced' in traits:
                return 'hindi_elderly'
            elif 'dramatic' in traits or 'intimidating' in traits:
                return 'hindi_antagonist'
            elif 'engaging' in traits or 'heroic' in traits:
                # Determine gender for protagonist
                if any(word in name_lower for word in ['नायिका', 'heroine', 'female', 'girl', 'woman']):
                    return 'hindi_protagonist_female'
                else:
                    return 'hindi_protagonist_male'
            elif 'professional' in traits or 'authoritative' in traits:
                return 'hindi_narrator'
            else:
                # Determine gender for generic characters
                if any(word in name_lower for word in ['female', 'girl', 'woman', 'lady', 'महिला', 'औरत']):
                    return 'hindi_female_character'
                else:
                    return 'hindi_male_character'
        else:
            # English categorization
            if 'young' in traits:
                return 'english_child'
            elif 'wise' in traits:
                return 'english_elderly'
            elif 'dramatic' in traits:
                return 'english_antagonist'
            elif 'engaging' in traits:
                return 'english_protagonist'
            elif 'professional' in traits:
                return 'english_narrator'
            else:
                return 'english_character'
    
    async def assign_voices_to_characters(self, characters: List[Dict], script: str = None) -> Dict:
        """
        Assign voices to characters based on their traits and language
        
        Args:
            characters: List of character dictionaries
            script: Optional script text for context
            
        Returns:
            Dictionary mapping character names to voice assignments
        """
        voice_assignments = {}
        used_voices = set()
        
        for character in characters:
            char_name = character['name']
            category = character['category']
            language = character.get('language', 'en')
            
            # Find best matching voice for this character
            best_voice = None
            
            # Filter voices by language first
            language_voices = [v for v in self.available_voices if v.get('language', 'en') == language]
            
            # First, try to find a voice from the same category
            for voice in language_voices:
                if voice['category'] == category and voice['voice_id'] not in used_voices:
                    best_voice = voice
                    break
            
            # If no voice found in category, use any available voice from same language
            if not best_voice:
                for voice in language_voices:
                    if voice['voice_id'] not in used_voices:
                        best_voice = voice
                        break
            
            # If no voice found in language, use any available voice
            if not best_voice:
                for voice in self.available_voices:
                    if voice['voice_id'] not in used_voices:
                        best_voice = voice
                        break
            
            # If all voices are used, reuse the first appropriate voice
            if not best_voice:
                best_voice = language_voices[0] if language_voices else self.available_voices[0]
            
            voice_assignments[char_name] = {
                'voice_id': best_voice['voice_id'],
                'voice_name': best_voice['name'],
                'category': best_voice['category'],
                'language': best_voice.get('language', 'en'),
                'gender': best_voice.get('gender', 'neutral'),
                'settings': self.voice_categories[best_voice['category']]
            }
            
            used_voices.add(best_voice['voice_id'])
        
        self.voice_assignments = voice_assignments
        return voice_assignments
    
    async def generate_character_speech(self, character_name: str, text: str, scene_context: Dict = None) -> Optional[bytes]:
        """
        Generate speech for a specific character with language-aware TTS
        
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
            language = voice_config.get('language', 'en')
            
            if not self.fallback_mode:
                # Use real TTS engines
                if self.xtts_model:
                    return await self._generate_with_xtts(text, voice_config, language)
                elif language in self.tts_engines:
                    return await self._generate_with_coqui(text, voice_config, language)
                else:
                    return await self._generate_fallback_audio(text, voice_config)
            else:
                # Use fallback synthetic audio
                return await self._generate_fallback_audio(text, voice_config)
                
        except Exception as e:
            logger.error(f"Character speech generation failed: {str(e)}")
            return None
    
    async def _generate_with_xtts(self, text: str, voice_config: Dict, language: str) -> Optional[bytes]:
        """Generate speech using XTTS-v2 multilingual model"""
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Use XTTS-v2 for multilingual generation
            self.xtts_model.tts_to_file(
                text=text,
                file_path=temp_path,
                language=language
            )
            
            # Read the audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            logger.info(f"Generated XTTS audio: {len(audio_data)} bytes for language '{language}'")
            return audio_data
            
        except Exception as e:
            logger.error(f"XTTS generation failed: {str(e)}")
            return None
    
    async def _generate_with_coqui(self, text: str, voice_config: Dict, language: str) -> Optional[bytes]:
        """Generate speech using Coqui TTS language-specific models"""
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Use appropriate TTS engine based on language
            tts_engine = self.tts_engines.get(language, self.tts_engines.get('english'))
            
            if tts_engine:
                tts_engine.tts_to_file(text=text, file_path=temp_path)
                
                # Read the audio file
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up
                os.unlink(temp_path)
                
                logger.info(f"Generated Coqui audio: {len(audio_data)} bytes for language '{language}'")
                return audio_data
            else:
                logger.warning(f"No TTS engine available for language '{language}'")
                return None
            
        except Exception as e:
            logger.error(f"Coqui TTS generation failed: {str(e)}")
            return None
    
    async def _generate_fallback_audio(self, text: str, voice_config: Dict) -> Optional[bytes]:
        """Generate fallback synthetic audio with language-aware characteristics"""
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
            language = voice_config.get('language', 'en')
            gender = voice_config.get('gender', 'neutral')
            
            # Base frequency adjustments for different languages and genders
            base_freq = 200
            
            if language == 'hi':
                # Hindi typically has different tonal qualities
                base_freq = 220
            
            # Gender-based frequency adjustments
            if gender == 'female':
                base_freq *= 1.3
            elif gender == 'male':
                base_freq *= 0.9
            
            # Adjust frequency based on voice category
            if 'child' in voice_config['category']:
                base_freq *= 1.5
            elif 'elderly' in voice_config['category']:
                base_freq *= 0.8
            elif 'antagonist' in voice_config['category']:
                base_freq *= 0.7
            
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
            
            logger.info(f"Generated fallback audio: {len(audio_data)} bytes for {language} {gender} character '{voice_config['voice_name']}'")
            return audio_data
            
        except Exception as e:
            logger.error(f"Fallback audio generation failed: {str(e)}")
            return None
    
    async def generate_multi_character_audio(self, dialogue_sequence: List[Dict]) -> List[Dict]:
        """
        Generate audio for multiple characters in sequence with language awareness
        
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
                    voice_info = self.voice_assignments.get(character_name, {})
                    audio_sequence.append({
                        'character': character_name,
                        'text': text,
                        'audio_data': audio_data,
                        'voice_info': voice_info,
                        'language': voice_info.get('language', 'en')
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
            'hindi_voices': len(self.available_hindi_voices),
            'english_voices': len(self.available_english_voices),
            'voice_categories': list(self.voice_categories.keys()),
            'supported_languages': ['hi', 'en'],
            'character_detection': True,
            'multi_character_support': True,
            'multilingual_support': True,
            'language_detection': True,
            'voice_cloning': self.xtts_model is not None,
            'real_time_generation': True,
            'fallback_mode': self.fallback_mode,
            'engine': "XTTS-v2 Multilingual" if self.xtts_model else "Coqui TTS" if not self.fallback_mode else "Fallback Synthetic"
        }

# Factory function to create enhanced voice manager
def get_enhanced_coqui_voice_manager() -> EnhancedCoquiVoiceManager:
    """Get Enhanced Coqui voice manager instance"""
    return EnhancedCoquiVoiceManager()