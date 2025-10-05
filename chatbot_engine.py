"""
Chatbot Engine - FIXED AVATAR SYSTEM
- Properly switches between speaking/idle images
- Optional audio-reactive animation
- Forces OBS to detect file changes
"""

import json
import threading
import time
from pathlib import Path
from llm_manager import LLMManager
from tts_manager import TTSManager
from input_handlers import InputManager
import os
from dotenv import load_dotenv

# Load environment variables
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)

class ChatbotEngine:
    def __init__(self, config_file='chatbot_config.json'):
        """Initialize chatbot engine with configuration"""
        self.config_file = Path(config_file)
        self.history_file = Path('conversation_history.json')
        self.load_config()

        # Initialize components
        self.llm = None
        self.tts = None
        self.inputs = InputManager()

        # State
        self.is_running = False
        self.is_speaking = False
        self.current_thread = None

        # Twitch polling
        self.twitch_thread = None
        self.twitch_running = False
        self.last_twitch_response_time = 0

        # Twitch TTS context tracking
        self.current_twitch_username = None
        self.current_twitch_message = None

        # FIXED: Store image PATHS instead of PIL Image objects
        self.speaking_image_path = None
        self.idle_image_path = None

        # Audio-reactive animation
        self.audio_reactive = False  # Set to True to enable
        self.animation_thread = None
        self.animation_running = False

        # Callbacks
        self.on_response_callback = None
        self.on_speaking_start = None
        self.on_speaking_end = None

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

    def _default_config(self):
        """Return default configuration"""
        return {
            'ai_name': 'Assistant',
            'user_name': 'User',
            'personality': 'You are a helpful AI assistant.',
            'llm_model': 'gpt-4o',
            'tts_service': 'elevenlabs',
            'elevenlabs_voice': 'default',
            'twitch_enabled': False,
            'twitch_channel': '',
            'mic_enabled': True,
            'screen_enabled': False,
            'speaking_image': '',
            'idle_image': '',
            'max_context_tokens': 8000,
            'auto_reset': False,
            'elevenlabs_stability': 0.5,
            'elevenlabs_similarity': 0.75,
            'elevenlabs_style': 0.0,
            'elevenlabs_speaker_boost': True,
            'response_length': 'normal',
            'max_response_tokens': 150,
            'response_style': 'conversational',
            'custom_response_style': '',
            'twitch_read_username': True,
            'twitch_response_mode': 'all',
            'twitch_response_chance': 100,
            'twitch_cooldown': 5,
            'twitch_keywords': '!ai,!bot,!ask',
            'twitch_speak_username': True,
            'twitch_speak_message': True,
        }

    def save_conversation_history(self):
        """Save conversation history to JSON file"""
        if self.llm and self.llm.chat_history:
            try:
                history_data = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'ai_name': self.config['ai_name'],
                    'model': self.config['llm_model'],
                    'conversation': self.llm.chat_history
                }
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, indent=2, ensure_ascii=False)
                print(f"[Engine] Saved conversation history")
            except Exception as e:
                print(f"[Engine] Error saving history: {e}")

    def load_conversation_history(self):
        """Load conversation history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                if self.llm and 'conversation' in history_data:
                    self.llm.chat_history = history_data['conversation']
                    print(f"[Engine] Loaded conversation history")
                    return True
            except Exception as e:
                print(f"[Engine] Error loading history: {e}")
        return False

    def _build_system_prompt(self):
        """Build system prompt with personality and settings"""
        system_prompt = self.config['personality']

        if self.config['ai_name'] != 'Assistant':
            system_prompt += f"\n\nYour name is {self.config['ai_name']}."

        if self.config['user_name'] != 'User':
            system_prompt += f"\nYou are talking to {self.config['user_name']}."

        response_length = self.config.get('response_length', 'normal')
        if response_length == 'brief':
            system_prompt += "\n\nIMPORTANT: Keep ALL responses very brief - 1-2 sentences (20-40 words max)."
        elif response_length == 'normal':
            system_prompt += "\n\nKeep responses concise - 2-4 sentences (40-80 words)."
        elif response_length == 'detailed':
            system_prompt += "\n\nProvide thorough responses - 4-8 sentences (80-150 words)."

        response_style = self.config.get('response_style', 'conversational')
        if response_style == 'casual':
            system_prompt += "\n\nUse a casual, friendly tone with informal language."
        elif response_style == 'professional':
            system_prompt += "\n\nMaintain a professional, polished tone."
        elif response_style == 'conversational':
            system_prompt += "\n\nUse a warm, conversational tone."
        elif response_style == 'custom':
            custom_style = self.config.get('custom_response_style', '')
            if custom_style:
                system_prompt += f"\n\n{custom_style}"

        return system_prompt

    def initialize(self):
        """Initialize all components"""
        system_prompt = self._build_system_prompt()

        self.llm = LLMManager(
            model=self.config['llm_model'],
            system_prompt=system_prompt,
            max_tokens=self.config.get('max_context_tokens', 8000)
        )

        elevenlabs_settings = {
            'stability': self.config.get('elevenlabs_stability', 0.5),
            'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
            'style': self.config.get('elevenlabs_style', 0.0),
            'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
        }

        self.tts = TTSManager(
            service=self.config['tts_service'],
            voice=self.config['elevenlabs_voice'],
            elevenlabs_settings=elevenlabs_settings
        )

        # Set up audio activity callbacks for avatar sync
        self.tts.set_audio_callbacks(
            on_start=self._on_audio_start,
            on_pause=self._on_audio_pause,
            on_resume=self._on_audio_resume
        )

        if self.config['twitch_enabled'] and self.config['twitch_channel']:
            self.inputs.enable_twitch(self.config['twitch_channel'])

        if self.config['mic_enabled']:
            self.inputs.enable_microphone()

        if self.config['screen_enabled']:
            self.inputs.enable_screen()

        # FIXED: Load image paths instead of PIL Images
        self._load_image_paths()

        print("[Engine] Initialized successfully!")

    def _load_image_paths(self):
        """Load and verify avatar image paths"""
        try:
            speaking_path = self.config.get('speaking_image', '')
            idle_path = self.config.get('idle_image', '')

            if speaking_path and Path(speaking_path).exists():
                self.speaking_image_path = Path(speaking_path)
                print(f"[Engine] Speaking image: {speaking_path}")
            else:
                self.speaking_image_path = None
                if speaking_path:
                    print(f"[Engine] Speaking image not found: {speaking_path}")

            if idle_path and Path(idle_path).exists():
                self.idle_image_path = Path(idle_path)
                print(f"[Engine] Idle image: {idle_path}")
            else:
                self.idle_image_path = None
                if idle_path:
                    print(f"[Engine] Idle image not found: {idle_path}")

        except Exception as e:
            print(f"[Engine] Error loading image paths: {e}")

    def start(self):
        """Start the chatbot engine"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True
        print(f"[Engine] {self.config['ai_name']} is now running!")

        if self.config['twitch_enabled'] and self.inputs.twitch:
            self.start_twitch_polling()

        # Show idle image on startup
        if self.idle_image_path:
            self._show_avatar('idle')

    def stop(self):
        """Stop the chatbot engine"""
        self.is_running = False
        self.stop_twitch_polling()
        self._stop_audio_animation()

        if self.inputs.twitch:
            self.inputs.disable_twitch()

        print("[Engine] Stopped")

    def start_twitch_polling(self):
        """Start polling Twitch chat"""
        if self.twitch_running:
            return
        self.twitch_running = True
        self.twitch_thread = threading.Thread(target=self._twitch_poll_loop, daemon=True)
        self.twitch_thread.start()
        print("[Engine] Twitch polling started")

    def stop_twitch_polling(self):
        """Stop polling Twitch chat"""
        self.twitch_running = False
        if self.twitch_thread:
            self.twitch_thread.join(timeout=2)
        print("[Engine] Twitch polling stopped")

    def _twitch_poll_loop(self):
        """Poll Twitch chat for messages"""
        import random

        while self.twitch_running and self.is_running:
            try:
                messages = self.inputs.get_twitch_messages()

                for msg in messages:
                    if not self.twitch_running:
                        break

                    username = msg['username']
                    message = msg['message']

                    should_respond = self._should_respond_to_twitch(message)

                    if should_respond:
                        current_time = time.time()
                        cooldown = self.config.get('twitch_cooldown', 5)

                        if current_time - self.last_twitch_response_time >= cooldown:
                            self.current_twitch_username = username
                            self.current_twitch_message = message

                            if self.config.get('twitch_read_username', True):
                                user_input = f"{username} says: {message}"
                            else:
                                user_input = message

                            print(f"[Engine] Responding to Twitch: {user_input}")
                            self._process_and_respond(user_input)

                            self.current_twitch_username = None
                            self.current_twitch_message = None
                            self.last_twitch_response_time = current_time

                time.sleep(0.5)

            except Exception as e:
                print(f"[Engine] Twitch polling error: {e}")
                time.sleep(1)

    def _should_respond_to_twitch(self, message):
        """Determine if should respond to Twitch message"""
        import random

        response_mode = self.config.get('twitch_response_mode', 'all')

        if response_mode == 'all':
            return True
        elif response_mode == 'keywords':
            keywords = self.config.get('twitch_keywords', '!ai,!bot,!ask')
            keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
            message_lower = message.lower()
            return any(keyword in message_lower for keyword in keyword_list)
        elif response_mode == 'random':
            chance = self.config.get('twitch_response_chance', 100)
            return random.randint(1, 100) <= chance
        elif response_mode == 'disabled':
            return False

        return False

    def process_microphone_input(self):
        """Listen to microphone and process"""
        if not self.inputs.enabled_inputs['microphone']:
            print("[Engine] Microphone disabled")
            return

        print("[Engine] Listening...")
        user_text = self.inputs.listen_microphone(timeout=10)

        if user_text:
            screen_data = None
            if self.inputs.enabled_inputs['screen']:
                screen_data = self.inputs.capture_screen()
                print("[Engine] Screen captured")

            self._process_and_respond(user_text, screen_data)
        else:
            print("[Engine] No speech detected")

    def process_text_input(self, text):
        """Process text input"""
        if text.strip():
            self._process_and_respond(text)

    def _process_and_respond(self, user_input, image_data=None):
        """Process input and generate response"""
        if not self.is_running:
            return

        print(f"[Engine] Processing: {user_input[:100]}")

        try:
            response_length = self.config.get('response_length', 'normal')
            max_tokens = {
                'brief': 60,
                'normal': 150,
                'detailed': 300,
                'custom': self.config.get('max_response_tokens', 150)
            }.get(response_length, 150)

            model = self.config['llm_model']
            vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
            supports_vision = model in vision_models

            if image_data and supports_vision:
                response = self.llm.chat_with_vision(
                    user_input, image_data, max_response_tokens=max_tokens
                )
            else:
                response = self.llm.chat(user_input, max_response_tokens=max_tokens)

            print(f"[Engine] Response: {response[:100]}")

            if self.on_response_callback:
                self.on_response_callback(response)

            self._speak_response(response)
            self.save_conversation_history()

        except Exception as e:
            import traceback
            print(f"[Engine] Error: {traceback.format_exc()}")
            error_response = f"Sorry, error: {str(e)}"
            if self.on_response_callback:
                self.on_response_callback(error_response)

    def _speak_response(self, text):
        """Convert response to speech with avatar animation"""
        if not text.strip():
            return

        # Construct TTS text with Twitch context if applicable
        tts_text = text

        if self.current_twitch_username or self.current_twitch_message:
            prepend_parts = []

            if self.config.get('twitch_speak_username', True) and self.current_twitch_username:
                prepend_parts.append(self.current_twitch_username)

            if self.config.get('twitch_speak_message', True) and self.current_twitch_message:
                if prepend_parts:
                    prepend_parts.append(f"said: {self.current_twitch_message}")
                else:
                    prepend_parts.append(self.current_twitch_message)

            if prepend_parts:
                prepend_text = " ".join(prepend_parts)
                tts_text = f"{prepend_text}. {text}"

        def speak_thread():
            self.tts.speak(
                tts_text,
                callback_on_start=self._on_speaking_start,
                callback_on_end=self._on_speaking_end
            )

        threading.Thread(target=speak_thread, daemon=True).start()

    def _on_speaking_start(self):
        """Called when TTS starts"""
        self.is_speaking = True
        print("[Engine] Started speaking")

        # Show speaking image
        if self.speaking_image_path:
            self._show_avatar('speaking')

        # Start audio-reactive animation if enabled
        if self.audio_reactive and self.speaking_image_path and self.idle_image_path:
            self._start_audio_animation()

        if self.on_speaking_start:
            self.on_speaking_start()

    def _on_speaking_end(self):
        """Called when TTS finishes"""
        self.is_speaking = False
        print("[Engine] Finished speaking")

        # Stop audio animation
        self._stop_audio_animation()

        # Show idle image
        if self.idle_image_path:
            self._show_avatar('idle')

        if self.on_speaking_end:
            self.on_speaking_end()

    def _on_audio_start(self):
        """Called when audio playback actually starts (from TTS)"""
        print("[Engine] Audio started")
        if self.speaking_image_path:
            self._show_avatar('speaking')

    def _on_audio_pause(self):
        """Called when audio pauses (silence in speech)"""
        print("[Engine] Audio paused - showing idle")
        if self.idle_image_path:
            self._show_avatar('idle')

    def _on_audio_resume(self):
        """Called when audio resumes after pause"""
        print("[Engine] Audio resumed - showing speaking")
        if self.speaking_image_path:
            self._show_avatar('speaking')

    def _show_avatar(self, state):
        """
        FIXED: Update avatar image for OBS (Windows-safe version)
        state: 'speaking' or 'idle'
        """
        try:
            import shutil
            import gc

            # Ensure images folder exists
            images_folder = Path('images')
            images_folder.mkdir(exist_ok=True)

            # Get source image
            if state == 'speaking' and self.speaking_image_path:
                source_path = self.speaking_image_path
                print(f"[Engine] Switching to SPEAKING avatar")
            elif state == 'idle' and self.idle_image_path:
                source_path = self.idle_image_path
                print(f"[Engine] Switching to IDLE avatar")
            else:
                return

            if not source_path.exists():
                print(f"[Engine] Image not found: {source_path}")
                return

            output_path = images_folder / 'current_avatar.png'

            # WINDOWS-SAFE FILE REPLACEMENT
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to delete old file
                    if output_path.exists():
                        try:
                            output_path.unlink()
                            time.sleep(0.02)  # Brief pause for Windows
                        except PermissionError:
                            # File locked - try alternate method
                            if attempt == max_retries - 1:
                                # Last attempt - just overwrite
                                print(f"[Engine] File locked, overwriting instead")

                    # Copy new image
                    shutil.copy2(source_path, output_path)

                    # Update timestamp
                    os.utime(output_path, None)

                    # Force garbage collection to release handles
                    gc.collect()

                    print(f"[Engine] ✅ Avatar updated to {state}")
                    break

                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(0.05 * (attempt + 1))
                        continue
                    else:
                        print(f"[Engine] ⚠️ File locked, update may be delayed")
                except Exception as e:
                    print(f"[Engine] Error in avatar update: {e}")
                    break

        except Exception as e:
            print(f"[Engine] Error updating avatar: {e}")

    def _start_audio_animation(self):
        """Start audio-reactive mouth animation"""
        if self.animation_running:
            return

        self.animation_running = True
        self.animation_thread = threading.Thread(target=self._audio_animation_loop, daemon=True)
        self.animation_thread.start()
        print("[Engine] Started audio-reactive animation")

    def _stop_audio_animation(self):
        """Stop audio-reactive animation"""
        self.animation_running = False
        if self.animation_thread:
            self.animation_thread.join(timeout=0.5)
        print("[Engine] Stopped audio-reactive animation")

    def _audio_animation_loop(self):
        """
        Audio-reactive animation loop (Windows-optimized)
        Rapidly switches between speaking/idle based on a pattern
        """
        try:
            import random

            switch_count = 0
            error_count = 0

            while self.animation_running and self.is_speaking:
                try:
                    # Speaking pattern: mostly open, occasional close
                    if random.random() < 0.7:  # 70% speaking
                        self._show_avatar('speaking')
                        # Slightly slower timing for Windows file handling
                        time.sleep(random.uniform(0.15, 0.35))
                        switch_count += 1
                    else:  # 30% brief idle (mouth closing)
                        self._show_avatar('idle')
                        time.sleep(random.uniform(0.1, 0.2))
                        switch_count += 1

                except Exception as e:
                    error_count += 1
                    if error_count < 5:  # Don't spam errors
                        print(f"[Engine] Animation frame error: {e}")
                    time.sleep(0.1)  # Brief pause on error

            print(f"[Engine] Animation completed: {switch_count} frames, {error_count} errors")

        except Exception as e:
            print(f"[Engine] Animation loop error: {e}")

    def set_config(self, key, value):
        """Update configuration"""
        self.config[key] = value

    def reload_config(self):
        """Reload configuration"""
        self.load_config()
        self.initialize()


if __name__ == '__main__':
    print("Testing Chatbot Engine...")
    engine = ChatbotEngine()
    engine.initialize()
    engine.start()

    print("\nSending test message...")
    engine.process_text_input("Hello! Can you introduce yourself?")

    time.sleep(5)
    print("\nTest complete!")
    engine.stop()