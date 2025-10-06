"""
TTS Manager - ENHANCED with Real-Time Audio-Reactive Avatar Switching
Analyzes actual audio volume levels for natural, responsive mouth animation
"""

import os
import sys

import requests
from pathlib import Path
import pygame
import threading
import time
import numpy as np
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

class TTSManager:
    def __init__(self, service='elevenlabs', voice='default', elevenlabs_settings=None):
        """Initialize TTS manager with audio-reactive capabilities"""
        self.service = service
        self.voice = voice
        self.audio_folder = Path('audio_cache')
        self.audio_folder.mkdir(exist_ok=True)

        # ElevenLabs settings
        self.elevenlabs_settings = elevenlabs_settings or {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True
        }

        # Hide console windows on Windows
        if sys.platform == 'win32':
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'directsound'

        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Audio monitoring state
        self.is_playing = False
        self.audio_active = False  # True when volume above threshold
        self.monitoring_thread = None
        self.stop_monitoring = False

        # Volume detection settings
        self.volume_threshold = 0.01  # Adjustable sensitivity (0.0-1.0)
        self.min_speech_duration = 0.05  # Minimum sound duration to trigger (seconds)
        self.min_silence_duration = 0.1  # Minimum silence duration to trigger (seconds)

        # Current audio analysis
        self.current_volume = 0.0
        self.volume_history = []  # For smoothing
        self.audio_data = None

        # Callbacks for avatar switching
        self.on_audio_start = None  # Called when audio starts
        self.on_audio_active = None  # Called when volume rises above threshold
        self.on_audio_silent = None  # Called when volume drops below threshold
        self.on_audio_end = None  # Called when audio ends

        # Initialize service-specific clients
        if service == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if api_key:
                self.elevenlabs_client = ElevenLabs(api_key=api_key)

    def set_volume_threshold(self, threshold):
        """Set the volume threshold for speech detection (0.0-1.0)"""
        self.volume_threshold = max(0.0, min(1.0, threshold))
        print(f"[TTS] Volume threshold set to {self.volume_threshold:.3f}")

    def speak(self, text, callback_on_start=None, callback_on_end=None):
        """Convert text to speech and play with audio-reactive monitoring"""
        if not text.strip():
            return

        print(f"[TTS] Speaking with {self.service}: {text[:50]}...")

        # Generate audio
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

            # Play audio with real-time monitoring
            if audio_file and audio_file.exists():
                if callback_on_start:
                    callback_on_start()

                # Pre-analyze audio file for volume levels
                self._analyze_audio_file(audio_file)

                # Play with real-time volume monitoring
                self._play_audio_with_volume_monitoring(audio_file)

                if callback_on_end:
                    callback_on_end()

        except Exception as e:
            print(f"TTS Error: {e}")
            if callback_on_end:
                callback_on_end()

    def _analyze_audio_file(self, audio_file):
        """Analyze audio file to extract volume envelope"""
        try:
            # Load audio file with pygame
            sound = pygame.mixer.Sound(str(audio_file))

            # Get raw audio data
            # Note: pygame doesn't provide easy access to raw data, so we'll use numpy
            # to load the file directly for analysis
            from scipy.io import wavfile
            import wave

            # Convert mp3 to wav if needed for analysis
            if audio_file.suffix == '.mp3':
                # For MP3, we'll use pydub if available
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_mp3(str(audio_file))
                    samples = np.array(audio.get_array_of_samples())
                    sample_rate = audio.frame_rate

                    # Normalize to -1.0 to 1.0
                    if audio.sample_width == 2:  # 16-bit
                        samples = samples / 32768.0
                    elif audio.sample_width == 1:  # 8-bit
                        samples = samples / 128.0

                except ImportError:
                    print("[TTS] pydub not available, using basic monitoring")
                    self.audio_data = None
                    return
            else:
                # Load WAV directly
                try:
                    sample_rate, samples = wavfile.read(str(audio_file))
                    # Normalize to -1.0 to 1.0
                    if samples.dtype == np.int16:
                        samples = samples / 32768.0
                    elif samples.dtype == np.int8:
                        samples = samples / 128.0
                except:
                    print("[TTS] Could not load audio for analysis")
                    self.audio_data = None
                    return

            # Handle stereo (take mean of channels)
            if len(samples.shape) > 1:
                samples = np.mean(samples, axis=1)

            # Calculate RMS (volume) in small windows
            window_size = int(sample_rate * 0.02)  # 20ms windows
            hop_size = int(sample_rate * 0.01)  # 10ms hop

            volume_envelope = []
            for i in range(0, len(samples) - window_size, hop_size):
                window = samples[i:i+window_size]
                rms = np.sqrt(np.mean(window**2))
                volume_envelope.append(rms)

            # Store analysis results
            self.audio_data = {
                'volume_envelope': volume_envelope,
                'sample_rate': sample_rate,
                'window_duration': 0.01,  # 10ms per window
                'max_volume': max(volume_envelope) if volume_envelope else 1.0
            }

            print(f"[TTS] Audio analyzed: {len(volume_envelope)} windows, max volume: {self.audio_data['max_volume']:.3f}")

        except Exception as e:
            print(f"[TTS] Audio analysis error: {e}")
            self.audio_data = None

    def _play_audio_with_volume_monitoring(self, audio_file):
        """Play audio and monitor volume levels in real-time"""
        try:
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()

            self.is_playing = True
            self.audio_active = False
            self.volume_history = []

            # Trigger start callback
            if self.on_audio_start:
                self.on_audio_start()

            # Start monitoring thread
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(
                target=self._monitor_volume_realtime,
                daemon=True
            )
            self.monitoring_thread.start()

            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(100)  # Check 100 times per second

            # Stop monitoring
            self.stop_monitoring = True
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=0.5)

            self.is_playing = False
            self.audio_active = False

            # Trigger end callback
            if self.on_audio_end:
                self.on_audio_end()

        except Exception as e:
            print(f"Audio playback error: {e}")
            self.is_playing = False
            self.audio_active = False

    def _monitor_volume_realtime(self):
        """Monitor audio volume in real-time and trigger callbacks"""
        last_state = False  # False = silent, True = active
        state_start_time = time.time()

        while not self.stop_monitoring and self.is_playing:
            try:
                # Get current playback position
                playback_pos = pygame.mixer.music.get_pos() / 1000.0  # Convert ms to seconds

                # Get volume at current position from analysis
                volume = self._get_volume_at_position(playback_pos)
                self.current_volume = volume

                # Add to history for smoothing
                self.volume_history.append(volume)
                if len(self.volume_history) > 5:
                    self.volume_history.pop(0)

                # Use smoothed volume
                smoothed_volume = np.mean(self.volume_history)

                # Determine if audio is active (above threshold)
                is_active = smoothed_volume > self.volume_threshold

                # Check for state changes with minimum duration requirements
                current_time = time.time()
                state_duration = current_time - state_start_time

                if is_active != last_state:
                    # State is changing - check minimum duration
                    if is_active and state_duration >= self.min_silence_duration:
                        # Silent -> Active (mouth opens)
                        self.audio_active = True
                        if self.on_audio_active:
                            self.on_audio_active()
                        print(f"[TTS] 🎤 ACTIVE (volume: {smoothed_volume:.3f})")
                        last_state = True
                        state_start_time = current_time

                    elif not is_active and state_duration >= self.min_speech_duration:
                        # Active -> Silent (mouth closes)
                        self.audio_active = False
                        if self.on_audio_silent:
                            self.on_audio_silent()
                        print(f"[TTS] 🤐 SILENT (volume: {smoothed_volume:.3f})")
                        last_state = False
                        state_start_time = current_time

                # Check frequently for responsive animation
                time.sleep(0.01)  # 10ms = 100 checks per second

            except Exception as e:
                print(f"[TTS] Monitoring error: {e}")
                break

    def _get_volume_at_position(self, position):
        """Get volume level at specific playback position"""
        if not self.audio_data:
            # Fallback: assume constant volume
            return 0.5

        # Calculate window index
        window_idx = int(position / self.audio_data['window_duration'])

        # Get volume from envelope
        envelope = self.audio_data['volume_envelope']
        if 0 <= window_idx < len(envelope):
            # Normalize by max volume
            normalized = envelope[window_idx] / self.audio_data['max_volume']
            return normalized

        return 0.0

    def get_current_volume(self):
        """Get current volume level (0.0-1.0)"""
        return self.current_volume

    def set_audio_callbacks(self, on_start=None, on_active=None, on_silent=None, on_end=None):
        """
        Set callbacks for audio-reactive events

        on_start: Called when audio playback starts
        on_active: Called when volume rises above threshold (mouth opens)
        on_silent: Called when volume drops below threshold (mouth closes)
        on_end: Called when audio playback ends
        """
        self.on_audio_start = on_start
        self.on_audio_active = on_active
        self.on_audio_silent = on_silent
        self.on_audio_end = on_end

    # [Previous TTS generation methods remain the same]
    def _elevenlabs_tts(self, text):
        """Generate speech using ElevenLabs"""
        try:
            voice_id = self.voice
            if '(' in voice_id and ')' in voice_id:
                voice_id = voice_id.split('(')[1].split(')')[0]

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

            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'elevenlabs_{timestamp}.mp3'

            with open(audio_file, 'wb') as f:
                for chunk in audio_generator:
                    f.write(chunk)

            return audio_file

        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None

    def _streamelements_tts(self, text):
        """Generate speech using StreamElements"""
        try:
            voice_name = self.voice if self.voice != 'default' else 'Brian'
            url = f"https://api.streamelements.com/kappa/v2/speech"
            params = {'voice': voice_name, 'text': text}

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
        """Generate speech using Coqui TTS"""
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
            return None

    def _azure_tts(self, text):
        """Generate speech using Azure TTS"""
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_key = os.getenv('AZURE_TTS_KEY')
            service_region = os.getenv('AZURE_TTS_REGION', 'eastus')

            if not speech_key:
                return None

            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
            voice_name = self.voice if self.voice != 'default' else 'en-US-JennyNeural'
            speech_config.speech_synthesis_voice_name = voice_name

            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'azure_{timestamp}.wav'
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))

            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = synthesizer.speak_text_async(text).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return audio_file
            return None

        except Exception as e:
            print(f"Azure TTS error: {e}")
            return None

    def stop(self):
        """Stop current audio playback"""
        try:
            self.stop_monitoring = True
            pygame.mixer.music.stop()
            self.is_playing = False
            self.audio_active = False
        except:
            pass


if __name__ == '__main__':
    print("Testing Audio-Reactive TTS...")

    def on_start():
        print("🎬 [START] Audio playback started")

    def on_active():
        print("   🎤 [MOUTH OPEN] Volume above threshold - SPEAKING")

    def on_silent():
        print("   🤐 [MOUTH CLOSED] Volume below threshold - SILENT")

    def on_end():
        print("🎬 [END] Audio playback finished")

    tts = TTSManager(service='streamelements', voice='Brian')
    tts.set_volume_threshold(0.02)  # Adjust sensitivity
    tts.set_audio_callbacks(on_start=on_start, on_active=on_active, on_silent=on_silent, on_end=on_end)

    test_text = "Hello! This is a test. Notice how the mouth opens and closes naturally with the speech. Pretty cool, right?"
    tts.speak(test_text)

    print("\n✅ Test complete!")