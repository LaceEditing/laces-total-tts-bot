"""
TTS Manager - ENHANCED with Audio Activity Monitoring
Supports: ElevenLabs, StreamElements, Coqui TTS, Azure
NEW: Real-time audio monitoring for avatar sync
"""

import os
import requests
from pathlib import Path
import pygame
import threading
import time
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
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Audio monitoring
        self.is_playing = False
        self.audio_active = False  # True when sound is playing, False during silence
        self.monitoring_thread = None
        self.stop_monitoring = False

        # Callbacks for audio activity
        self.on_audio_start = None  # Called when audio becomes active
        self.on_audio_pause = None  # Called when audio pauses (silence)
        self.on_audio_resume = None  # Called when audio resumes after pause

        # Audio level monitoring
        self.silence_threshold = 0.01  # Adjust sensitivity (0.0-1.0)
        self.min_pause_duration = 0.2  # Minimum silence duration to trigger pause (seconds)

        # Initialize service-specific clients
        if service == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if api_key:
                self.elevenlabs_client = ElevenLabs(api_key=api_key)
            else:
                print("Warning: ELEVENLABS_API_KEY not found")

    def speak(self, text, callback_on_start=None, callback_on_end=None):
        """Convert text to speech and play audio with monitoring"""
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

            # Play audio file with monitoring
            if audio_file and audio_file.exists():
                if callback_on_start:
                    callback_on_start()

                self._play_audio_with_monitoring(audio_file, text)

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

            # Use unique filename
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
            voice_name = self.voice if self.voice != 'default' else 'Brian'
            url = f"https://api.streamelements.com/kappa/v2/speech"

            params = {
                'voice': voice_name,
                'text': text
            }

            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()

            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'streamelements_{timestamp}.mp3'

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

            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC",
                     progress_bar=False, gpu=False)

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

            voice_name = self.voice if self.voice != 'default' else 'en-US-JennyNeural'
            speech_config.speech_synthesis_voice_name = voice_name

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

    def _play_audio_with_monitoring(self, audio_file, text):
        """
        Play audio file with real-time monitoring
        Triggers callbacks when audio activity changes
        """
        try:
            pygame.mixer.music.load(str(audio_file))

            # Parse text for natural pauses (simple method)
            pause_points = self._find_text_pauses(text)

            # Start playback
            pygame.mixer.music.play()
            self.is_playing = True
            self.audio_active = True

            if self.on_audio_start:
                self.on_audio_start()

            # Start monitoring thread
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(
                target=self._monitor_audio_activity,
                args=(pause_points,),
                daemon=True
            )
            self.monitoring_thread.start()

            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Stop monitoring
            self.stop_monitoring = True
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=0.5)

            self.is_playing = False
            self.audio_active = False

        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False
            self.audio_active = False

    def _find_text_pauses(self, text):
        """
        Analyze text to estimate natural pause points
        Returns list of approximate timestamps (in seconds)
        """
        # Estimate speaking rate: ~150 words per minute = ~2.5 words per second
        words_per_second = 2.5

        pause_points = []
        words = text.split()
        current_time = 0.0

        for i, word in enumerate(words):
            # Estimate time for this word (rough approximation)
            word_duration = len(word) / (words_per_second * 5)  # 5 chars per word avg
            current_time += word_duration

            # Check for punctuation that indicates pauses
            if word.endswith('.') or word.endswith('!') or word.endswith('?'):
                # Longer pause after sentence
                pause_points.append({
                    'time': current_time,
                    'duration': 0.4,
                    'type': 'sentence'
                })
                current_time += 0.4
            elif word.endswith(',') or word.endswith(';'):
                # Shorter pause after comma
                pause_points.append({
                    'time': current_time,
                    'duration': 0.2,
                    'type': 'comma'
                })
                current_time += 0.2

        return pause_points

    def _monitor_audio_activity(self, pause_points):
        """
        Monitor audio playback and trigger callbacks during pauses
        Uses text-based pause detection for simplicity
        """
        start_time = time.time()
        last_state = True  # Start as active
        pause_index = 0

        while not self.stop_monitoring and self.is_playing:
            current_time = time.time() - start_time

            # Check if we're at a pause point
            if pause_index < len(pause_points):
                pause = pause_points[pause_index]

                # Are we at this pause point?
                if current_time >= pause['time']:
                    # Trigger pause callback
                    if self.audio_active and self.on_audio_pause:
                        print(f"[TTS] Pause detected at {current_time:.2f}s ({pause['type']})")
                        self.audio_active = False
                        self.on_audio_pause()

                    # Wait for pause duration
                    time.sleep(pause['duration'])

                    # Resume
                    if not self.audio_active and self.on_audio_resume:
                        print(f"[TTS] Resuming at {current_time:.2f}s")
                        self.audio_active = True
                        self.on_audio_resume()

                    pause_index += 1

            time.sleep(0.05)  # Check every 50ms

    def set_audio_callbacks(self, on_start=None, on_pause=None, on_resume=None):
        """
        Set callbacks for audio activity monitoring

        on_start: Called when audio playback starts
        on_pause: Called when audio pauses (silence detected)
        on_resume: Called when audio resumes after pause
        """
        self.on_audio_start = on_start
        self.on_audio_pause = on_pause
        self.on_audio_resume = on_resume

    def set_service(self, service):
        """Change TTS service"""
        self.service = service

    def set_voice(self, voice):
        """Change voice ID/name"""
        self.voice = voice

    def stop(self):
        """Stop current audio playback"""
        try:
            self.stop_monitoring = True
            pygame.mixer.music.stop()
            self.is_playing = False
            self.audio_active = False
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
    # Test TTS with audio monitoring
    print("Testing TTS Manager with Audio Monitoring...")

    def on_start():
        print("[TEST] Audio started - mouth should be OPEN")

    def on_pause():
        print("[TEST] Audio paused - mouth should CLOSE")

    def on_resume():
        print("[TEST] Audio resumed - mouth should OPEN")

    tts = TTSManager(service='streamelements', voice='Brian')
    tts.set_audio_callbacks(on_start=on_start, on_pause=on_pause, on_resume=on_resume)

    test_text = "Hello! This is a test. Can you see the pauses? I hope so, because that would be really cool!"
    tts.speak(test_text)

    print("Test complete!")