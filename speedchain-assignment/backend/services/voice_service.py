import asyncio
import logging
import os
import io
import base64
from typing import Optional
import wave

import openai
from openai import AsyncOpenAI
from elevenlabs import generate, set_api_key

logger = logging.getLogger(__name__)

class VoiceService:
    """Service for Speech-to-Text and Text-to-Speech conversion."""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # ElevenLabs setup (alternative to OpenAI TTS)
        elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        if elevenlabs_key:
            set_api_key(elevenlabs_key)
            self.use_elevenlabs = True
        else:
            self.use_elevenlabs = False
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """
        Convert speech audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Audio data in bytes (WAV, MP3, etc.)
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            # Save audio data to temporary file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            # Use OpenAI Whisper for transcription
            response = await self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
            
            transcription = response.text.strip()
            logger.info(f"Transcription successful: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return None
    
    async def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio data in bytes (MP3 format)
        """
        try:
            if self.use_elevenlabs:
                # Use ElevenLabs for higher quality
                audio = generate(
                    text=text,
                    voice="Rachel",  # Professional female voice
                    model="eleven_monolingual_v1"
                )
                return audio
            else:
                # Use OpenAI TTS
                response = await self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="nova",  # Professional female voice
                    input=text
                )
                
                # Return audio bytes
                return response.content
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            # Return empty bytes on error
            return b""
