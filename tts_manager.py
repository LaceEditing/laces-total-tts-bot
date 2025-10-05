"""
TTS Manager - Handles multiple Text-to-Speech services
Supports: ElevenLabs, StreamElements, Coqui TTS, Azure
"""

import os
import requests
from pathlib import Path
import pygame
import base64
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

class TTSManager:
    def __init__(self, service='elevenlabs', voice='default', elevenlabs_settings=None):
        """Initialize TTS manager with specified service"""
        self.service = service
        self.voice = voice
        self.audio_folder = Path('audio_cache')
        self.audio_folder.mkdir(exist_ok=True)

        # ElevenLabs settings with defaults
        self.elevenlabs_settings = elevenlabs_settings or {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True
        }

        # Initialize pygame mixer for audio playback
        pygame.mixer.init()

        # Initialize service-specific clients
        if service == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if api_key:
                self.elevenlabs_client = ElevenLabs(api_key=api_key)
            else:
                print("Warning: ELEVENLABS_API_KEY not found")

    def speak(self, text, callback_on_start=None, callback_on_end=None):
        """Convert text to speech and play audio"""
        if not text.strip():
            return

        print(f"[TTS] Speaking with {self.service}: {text[:50]}...")

        # Generate audio based on service
        audio_file = None

        try:
            if self.service == 'elevenlabs':
                audio_file = self._elevenlabs_tts(text)
            elif self.service == 'streamelements':
                audio_file = self._streamelements_tts(text)
            elif self.service == 'coqui-tts':
                audio_file = self._coqui_tts(text)
            elif self.service == 'azure':
                audio_file = self._azure_tts(text)
            else:
                print(f"Unknown TTS service: {self.service}")
                return

            # Play audio file
            if audio_file and audio_file.exists():
                if callback_on_start:
                    callback_on_start()

                self._play_audio(audio_file)

                if callback_on_end:
                    callback_on_end()

        except Exception as e:
            print(f"TTS Error: {e}")
            if callback_on_end:
                callback_on_end()

    def _elevenlabs_tts(self, text):
        """Generate speech using ElevenLabs"""
        try:
            # Handle custom voice format "Name (voice_id)"
            voice_id = self.voice
            if '(' in voice_id and ')' in voice_id:
                # Extract voice_id from "Name (voice_id)" format
                voice_id = voice_id.split('(')[1].split(')')[0]

            # Generate audio with custom settings
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                output_format="mp3_44100_128",
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings=VoiceSettings(
                    stability=self.elevenlabs_settings.get('stability', 0.5),
                    similarity_boost=self.elevenlabs_settings.get('similarity_boost', 0.75),
                    style=self.elevenlabs_settings.get('style', 0.0),
                    use_speaker_boost=self.elevenlabs_settings.get('use_speaker_boost', True)
                )
            )

            # Use unique filename to avoid permission issues
            import time
            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'elevenlabs_{timestamp}.mp3'

            # Save to file
            with open(audio_file, 'wb') as f:
                for chunk in audio_generator:
                    f.write(chunk)

            return audio_file

        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None

    def _streamelements_tts(self, text):
        """Generate speech using StreamElements (free)"""
        try:
            # StreamElements TTS API endpoint
            voice_name = self.voice if self.voice != 'default' else 'Brian'
            url = f"https://api.streamelements.com/kappa/v2/speech"

            params = {
                'voice': voice_name,
                'text': text
            }

            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()

            # Use unique filename to avoid permission issues
            import time
            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'streamelements_{timestamp}.mp3'

            # Save audio
            with open(audio_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

            return audio_file

        except Exception as e:
            print(f"StreamElements TTS error: {e}")
            return None

    def _coqui_tts(self, text):
        """Generate speech using Coqui TTS (open source, local)"""
        try:
            from TTS.api import TTS

            # Initialize model (you can change model)
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC",
                     progress_bar=False, gpu=False)

            # Use unique filename
            import time
            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'coqui_{timestamp}.wav'

            tts.tts_to_file(text=text, file_path=str(audio_file))

            return audio_file

        except Exception as e:
            print(f"Coqui TTS error: {e}")
            print("Install with: pip install TTS")
            return None

    def _azure_tts(self, text):
        """Generate speech using Azure TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_key = os.getenv('AZURE_TTS_KEY')
            service_region = os.getenv('AZURE_TTS_REGION', 'eastus')

            if not speech_key:
                print("AZURE_TTS_KEY not found")
                return None

            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=service_region
            )

            # Set voice
            voice_name = self.voice if self.voice != 'default' else 'en-US-JennyNeural'
            speech_config.speech_synthesis_voice_name = voice_name

            # Use unique filename
            import time
            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'azure_{timestamp}.wav'

            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))

            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return audio_file
            else:
                print(f"Azure TTS failed: {result.reason}")
                return None

        except Exception as e:
            print(f"Azure TTS error: {e}")
            return None

    def _play_audio(self, audio_file):
        """Play audio file using pygame"""
        try:
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()

            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

        except Exception as e:
            print(f"Audio playback error: {e}")

    def set_service(self, service):
        """Change TTS service"""
        self.service = service

    def set_voice(self, voice):
        """Change voice ID/name"""
        self.voice = voice

    def stop(self):
        """Stop current audio playback"""
        try:
            pygame.mixer.music.stop()
        except:
            pass


# Available voices reference
ELEVENLABS_VOICES = {
    'rachel': 'Rachel - Natural female voice',
    'drew': 'Drew - Natural male voice',
    'clyde': 'Clyde - Friendly male voice',
    'paul': 'Paul - Mature male voice',
    'domi': 'Domi - Energetic female voice',
    'dave': 'Dave - British male voice',
    'fin': 'Fin - Irish male voice',
    'sarah': 'Sarah - Soft female voice',
    'antoni': 'Antoni - Articulate male voice',
    'thomas': 'Thomas - Mature male voice',
    'charlie': 'Charlie - Australian male voice',
    'emily': 'Emily - American female voice',
    'elli': 'Elli - Young female voice',
    'callum': 'Callum - British male voice',
    'patrick': 'Patrick - Deep male voice',
    'harry': 'Harry - Anxious male voice',
    'liam': 'Liam - Calm male voice',
    'dorothy': 'Dorothy - Pleasant female voice',
    'josh': 'Josh - Young male voice',
    'arnold': 'Arnold - Crisp male voice',
    'charlotte': 'Charlotte - Smooth female voice',
    'alice': 'Alice - Confident female voice',
    'matilda': 'Matilda - British female voice',
    'james': 'James - Calm male voice'
}

STREAMELEMENTS_VOICES = [
    'Brian', 'Ivy', 'Justin', 'Russell', 'Nicole', 'Emma', 'Amy', 'Joanna',
    'Salli', 'Kimberly', 'Kendra', 'Joey', 'Matthew', 'Geraint', 'Raveena'
]


if __name__ == '__main__':
    # Test TTS
    print("Testing TTS Manager...")

    tts = TTSManager(service='streamelements', voice='Brian')
    tts.speak("Hello! This is a test of the text to speech system.")

    print("Test complete!")