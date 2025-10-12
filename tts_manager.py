"""
TTS Manager - StreamElements & ElevenLabs Only
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

# Suppress console output
if sys.platform == 'win32':
    import subprocess
    CREATE_NO_WINDOW = 0x08000000
    _original_popen = subprocess.Popen

    def _silent_popen(*args, **kwargs):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = 0
        kwargs['creationflags'] |= CREATE_NO_WINDOW
        kwargs['startupinfo'] = startupinfo
        return _original_popen(*args, **kwargs)

    subprocess.Popen = _silent_popen

if hasattr(sys, '_MEIPASS'):
    bundle_dir = sys._MEIPASS
    ffmpeg_exe = os.path.join(bundle_dir, 'ffmpeg.exe')
    ffprobe_exe = os.path.join(bundle_dir, 'ffprobe.exe')
    if os.path.exists(ffmpeg_exe):
        os.environ['FFMPEG_BINARY'] = ffmpeg_exe
        os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')
    if os.path.exists(ffprobe_exe):
        os.environ['FFPROBE_BINARY'] = ffprobe_exe

try:
    from pydub import AudioSegment
    if hasattr(sys, '_MEIPASS'):
        ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            AudioSegment.converter = ffmpeg_path
    if sys.platform == 'win32':
        import subprocess
        _pydub_original = subprocess.Popen
        def _pydub_silent(*args, **kwargs):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs['startupinfo'] = startupinfo
            if 'creationflags' not in kwargs:
                kwargs['creationflags'] = 0
            kwargs['creationflags'] |= CREATE_NO_WINDOW
            return _pydub_original(*args, **kwargs)
        subprocess.Popen = _pydub_silent
except Exception:
    AudioSegment = None


class TTSManager:
    def __init__(self, service='elevenlabs', voice='default', elevenlabs_settings=None):
        """Initialize TTS manager - StreamElements & ElevenLabs only"""
        self.service = service
        self.voice = voice
        self.audio_folder = Path('audio_cache')
        self.audio_folder.mkdir(exist_ok=True)

        self.elevenlabs_settings = elevenlabs_settings or {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True
        }

        # Suppress pygame output
        if sys.platform == 'win32':
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'directsound'

        import io
        import contextlib
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # Audio monitoring state
        self.is_playing = False
        self.audio_active = False
        self.monitoring_thread = None
        self.stop_monitoring = False

        # Volume detection settings
        self.volume_threshold = 0.01
        self.min_speech_duration = 0.05
        self.min_silence_duration = 0.1

        # Current audio analysis
        self.current_volume = 0.0
        self.volume_history = []
        self.audio_data = None

        # Callbacks
        self.on_audio_start = None
        self.on_audio_active = None
        self.on_audio_silent = None
        self.on_audio_end = None

        # Initialize ElevenLabs client
        if service == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if api_key:
                self.elevenlabs_client = ElevenLabs(api_key=api_key)

    def set_volume_threshold(self, threshold):
        """Set the volume threshold for speech detection (0.0-1.0)"""
        self.volume_threshold = max(0.0, min(1.0, threshold))

    def speak(self, text, callback_on_start=None, callback_on_end=None):
        """Convert text to speech and play with audio-reactive monitoring"""
        if not text.strip():
            return

        audio_file = None
        try:
            if self.service == 'elevenlabs':
                audio_file = self._elevenlabs_tts(text)
            elif self.service == 'streamelements':
                audio_file = self._streamelements_tts(text)
            else:
                return

            if audio_file and audio_file.exists():
                if callback_on_start:
                    callback_on_start()

                self._analyze_audio_file(audio_file)
                self._play_audio_with_volume_monitoring(audio_file)

                if callback_on_end:
                    callback_on_end()

        except Exception as e:
            print(f"[TTS] Error in speak: {e}")
            if callback_on_end:
                callback_on_end()

    def _analyze_audio_file(self, audio_file):
        """Analyze audio file to extract volume envelope"""
        try:
            if audio_file.suffix == '.mp3':
                try:
                    if AudioSegment is None:
                        self.audio_data = None
                        return
                    audio = AudioSegment.from_mp3(str(audio_file))
                    samples = np.array(audio.get_array_of_samples())
                    sample_rate = audio.frame_rate
                    if audio.sample_width == 2:
                        samples = samples / 32768.0
                    elif audio.sample_width == 1:
                        samples = samples / 128.0
                except Exception:
                    self.audio_data = None
                    return
            else:
                try:
                    from scipy.io import wavfile
                    sample_rate, samples = wavfile.read(str(audio_file))
                    if samples.dtype == np.int16:
                        samples = samples / 32768.0
                    elif samples.dtype == np.int8:
                        samples = samples / 128.0
                except Exception:
                    self.audio_data = None
                    return

            if len(samples.shape) > 1:
                samples = np.mean(samples, axis=1)

            window_size = int(sample_rate * 0.02)
            hop_size = int(sample_rate * 0.01)

            volume_envelope = []
            for i in range(0, len(samples) - window_size, hop_size):
                window = samples[i:i + window_size]
                rms = np.sqrt(np.mean(window ** 2))
                volume_envelope.append(rms)

            self.audio_data = {
                'volume_envelope': volume_envelope,
                'sample_rate': sample_rate,
                'window_duration': 0.01,
                'max_volume': max(volume_envelope) if volume_envelope else 1.0
            }
        except Exception:
            self.audio_data = None

    def _play_audio_with_volume_monitoring(self, audio_file):
        """Play audio and monitor volume levels in real-time"""
        try:
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()

            self.is_playing = True
            self.audio_active = False
            self.volume_history = []

            if self.on_audio_start:
                self.on_audio_start()

            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(
                target=self._monitor_volume_realtime,
                daemon=True
            )
            self.monitoring_thread.start()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(100)

            self.stop_monitoring = True
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=0.5)

            self.is_playing = False
            self.audio_active = False

            if self.on_audio_end:
                self.on_audio_end()

        except Exception:
            self.is_playing = False
            self.audio_active = False

    def _monitor_volume_realtime(self):
        """Monitor audio volume in real-time and trigger callbacks"""
        last_state = False
        state_start_time = time.time()

        while not self.stop_monitoring and self.is_playing:
            try:
                playback_pos = pygame.mixer.music.get_pos() / 1000.0
                volume = self._get_volume_at_position(playback_pos)
                self.current_volume = volume

                self.volume_history.append(volume)
                if len(self.volume_history) > 5:
                    self.volume_history.pop(0)

                smoothed_volume = np.mean(self.volume_history)
                is_active = smoothed_volume > self.volume_threshold

                current_time = time.time()
                state_duration = current_time - state_start_time

                if is_active != last_state:
                    if is_active and state_duration >= self.min_silence_duration:
                        self.audio_active = True
                        if self.on_audio_active:
                            self.on_audio_active()
                        last_state = True
                        state_start_time = current_time
                    elif not is_active and state_duration >= self.min_speech_duration:
                        self.audio_active = False
                        if self.on_audio_silent:
                            self.on_audio_silent()
                        last_state = False
                        state_start_time = current_time

                time.sleep(0.01)
            except Exception:
                break

    def _get_volume_at_position(self, position):
        """Get volume level at specific playback position"""
        if not self.audio_data:
            return 0.5
        window_idx = int(position / self.audio_data['window_duration'])
        envelope = self.audio_data['volume_envelope']
        if 0 <= window_idx < len(envelope):
            normalized = envelope[window_idx] / self.audio_data['max_volume']
            return normalized
        return 0.0

    def get_current_volume(self):
        """Get current volume level (0.0-1.0)"""
        return self.current_volume

    def set_audio_callbacks(self, on_start=None, on_active=None, on_silent=None, on_end=None):
        """Set callbacks for audio-reactive events"""
        self.on_audio_start = on_start
        self.on_audio_active = on_active
        self.on_audio_silent = on_silent
        self.on_audio_end = on_end

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
        except Exception:
            return None

    def _streamelements_tts(self, text):
        """Generate speech using StreamElements (Free!)"""
        try:
            voice_name = self.voice if self.voice != 'default' else 'Brian'
            url = "https://api.streamelements.com/kappa/v2/speech"
            params = {'voice': voice_name, 'text': text}

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return None

            timestamp = str(int(time.time() * 1000))
            audio_file = self.audio_folder / f'streamelements_{timestamp}.mp3'

            with open(audio_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            if audio_file.exists() and audio_file.stat().st_size > 1000:
                return audio_file
            else:
                if audio_file.exists():
                    audio_file.unlink()
                return None
        except Exception:
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
    # Test StreamElements
    tts = TTSManager(service='streamelements', voice='Brian')
    tts.speak("Testing StreamElements TTS. This is free and works great!")
    time.sleep(3)

    # Test ElevenLabs (if you have an API key)
    # tts = TTSManager(service='elevenlabs', voice='rachel')
    # tts.speak("Testing ElevenLabs premium voice quality!")