"""
Chatbot Engine - Enhanced with Audio-Reactive Avatar System
Avatar responds to actual audio volume levels in real-time
"""

import json
import threading
import time
from pathlib import Path
from llm_manager import LLMManager
from tts_manager import TTSManager
from input_handlers import InputManager
from avatar_window import AvatarWindow
import os
from dotenv import load_dotenv

env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)

class ChatbotEngine:
    def __init__(self, config_file='chatbot_config.json'):
        """Initialize chatbot engine with audio-reactive avatar"""
        self.config_file = Path(config_file)
        self.history_file = Path('conversation_history.json')
        self.load_config()

        # Components
        self.llm = None
        self.tts = None
        self.inputs = InputManager()

        # State
        self.is_running = False
        self.is_speaking = False
        self.current_thread = None

        # Twitch
        self.twitch_thread = None
        self.twitch_running = False
        self.last_twitch_response_time = 0
        self.current_twitch_username = None
        self.current_twitch_message = None

        # Avatar window
        self.avatar_window = None

        # Callbacks
        self.on_response_callback = None
        self.on_speaking_start = None
        self.on_speaking_end = None
        self.on_volume_update = None  # NEW: For audio meter updates

    def load_config(self):
        """Load configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._default_config()

    def _default_config(self):
        """Default configuration"""
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
            'volume_threshold': 0.02,  # NEW: Audio sensitivity
            'elevenlabs_stability': 0.5,
            'elevenlabs_similarity': 0.75,
            'elevenlabs_style': 0.0,
            'elevenlabs_speaker_boost': True,
            'response_length': 'normal',
            'max_response_tokens': 150,
            'twitch_speak_username': True,
            'twitch_speak_message': True,
        }

    def _build_system_prompt(self):
        """Build system prompt with personality and settings"""
        system_prompt = self.config['personality']

        if self.config['ai_name'] != 'Assistant':
            system_prompt += f"\n\nYour name is {self.config['ai_name']}."

        if self.config['user_name'] != 'User':
            system_prompt += f"\nYou are talking to {self.config['user_name']}."

        # Add response length instructions
        response_length = self.config.get('response_length', 'normal')
        if response_length == 'brief':
            system_prompt += "\n\nIMPORTANT: Keep ALL responses very brief and concise - typically 1-2 sentences (20-40 words max)."
        elif response_length == 'normal':
            system_prompt += "\n\nKeep responses concise and engaging - typically 2-4 sentences (40-80 words)."
        elif response_length == 'detailed':
            system_prompt += "\n\nProvide thorough, detailed responses - typically 4-8 sentences (80-150 words)."

        # Add response style
        response_style = self.config.get('response_style', 'conversational')
        if response_style == 'custom':
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

        # Set volume threshold for audio-reactive avatar
        volume_threshold = self.config.get('volume_threshold', 0.02)
        self.tts.set_volume_threshold(volume_threshold)

        # Set up audio-reactive callbacks
        self.tts.set_audio_callbacks(
            on_start=self._on_audio_start,
            on_active=self._on_audio_active,
            on_silent=self._on_audio_silent,
            on_end=self._on_audio_end
        )

        if self.config['twitch_enabled'] and self.config['twitch_channel']:
            self.inputs.enable_twitch(self.config['twitch_channel'])

        if self.config['mic_enabled']:
            self.inputs.enable_microphone()

        if self.config['screen_enabled']:
            self.inputs.enable_screen()

        self._load_images()
        print("[Engine] Initialized with audio-reactive avatar!")

    def _load_images(self):
        """Initialize avatar window"""
        try:
            idle_path = self.config.get('idle_image', '')
            speaking_path = self.config.get('speaking_image', '')

            if idle_path and speaking_path and Path(idle_path).exists() and Path(speaking_path).exists():
                if self.avatar_window is None:
                    self.avatar_window = AvatarWindow(
                        idle_image_path=idle_path,
                        speaking_image_path=speaking_path,
                        bg_color='#00FF00',
                        always_on_top=False
                    )
                    print(f"[Engine] Avatar window created")
                else:
                    self.avatar_window.load_images(idle_path, speaking_path)
                    print(f"[Engine] Avatar images updated")

        except Exception as e:
            print(f"[Engine] Error loading avatar: {e}")

    def start(self):
        """Start the chatbot"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True
        print(f"[Engine] {self.config['ai_name']} is running with audio-reactive avatar!")

        if self.config['twitch_enabled'] and self.inputs.twitch:
            self.start_twitch_polling()

        if self.avatar_window:
            self._show_avatar('idle')

    def stop(self):
        """Stop the chatbot"""
        self.is_running = False
        self.stop_twitch_polling()

        if self.inputs.twitch:
            self.inputs.disable_twitch()

        if self.avatar_window:
            self.avatar_window.hide()

        print("[Engine] Stopped")

    # Audio-reactive callbacks (NEW)
    def _on_audio_start(self):
        """Called when audio playback starts"""
        self.is_speaking = True
        print("[Engine] 🎬 Audio started")

        if self.on_speaking_start:
            self.on_speaking_start()

    def _on_audio_active(self):
        """Called when volume rises above threshold - MOUTH OPENS"""
        if self.avatar_window:
            self.avatar_window.show_speaking()

        # Update audio meter if callback exists
        if self.on_volume_update and self.tts:
            volume = self.tts.get_current_volume()
            self.on_volume_update(volume)

    def _on_audio_silent(self):
        """Called when volume drops below threshold - MOUTH CLOSES"""
        if self.avatar_window:
            self.avatar_window.show_idle()

        # Update audio meter if callback exists
        if self.on_volume_update and self.tts:
            volume = self.tts.get_current_volume()
            self.on_volume_update(volume)

    def _on_audio_end(self):
        """Called when audio playback ends"""
        self.is_speaking = False
        print("[Engine] 🎬 Audio finished")

        if self.avatar_window:
            self.avatar_window.show_idle()

        if self.on_speaking_end:
            self.on_speaking_end()

    def set_volume_threshold(self, threshold):
        """Update volume threshold for audio detection"""
        self.config['volume_threshold'] = threshold
        if self.tts:
            self.tts.set_volume_threshold(threshold)
        print(f"[Engine] Volume threshold updated: {threshold:.3f}")

    def start_twitch_polling(self):
        """Start polling Twitch chat"""
        if self.twitch_running:
            return

        self.twitch_running = True
        self.twitch_thread = threading.Thread(target=self._twitch_poll_loop, daemon=True)
        self.twitch_thread.start()
        print("[Engine] Twitch polling started")

    def stop_twitch_polling(self):
        """Stop Twitch polling"""
        self.twitch_running = False
        if self.twitch_thread:
            self.twitch_thread.join(timeout=2)

    def _twitch_poll_loop(self):
        """Poll Twitch for messages"""
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
                print(f"[Engine] Twitch error: {e}")
                time.sleep(1)

    def _should_respond_to_twitch(self, message):
        """Check if should respond to Twitch message"""
        import random

        response_mode = self.config.get('twitch_response_mode', 'all')

        if response_mode == 'all':
            return True
        elif response_mode == 'keywords':
            keywords = self.config.get('twitch_keywords', '!ai,!bot').split(',')
            return any(k.strip().lower() in message.lower() for k in keywords)
        elif response_mode == 'random':
            chance = self.config.get('twitch_response_chance', 100)
            return random.randint(1, 100) <= chance
        elif response_mode == 'disabled':
            return False

        return False

    def process_microphone_input(self):
        """Process microphone input"""
        if not self.inputs.enabled_inputs['microphone']:
            return

        print("[Engine] Listening...")
        user_text = self.inputs.listen_microphone(timeout=10)

        if user_text:
            screen_data = None
            if self.inputs.enabled_inputs['screen']:
                screen_data = self.inputs.capture_screen()

            self._process_and_respond(user_text, screen_data)

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
            # Get max tokens based on response length
            response_length = self.config.get('response_length', 'normal')
            if response_length == 'brief':
                max_tokens = 60
            elif response_length == 'detailed':
                max_tokens = 300
            elif response_length == 'custom':
                max_tokens = self.config.get('max_response_tokens', 150)
            else:
                max_tokens = 150

            # Get response from LLM
            model = self.config['llm_model']
            vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']

            if image_data and model in vision_models:
                response = self.llm.chat_with_vision(user_input, image_data, max_response_tokens=max_tokens)
            else:
                response = self.llm.chat(user_input, max_response_tokens=max_tokens)

            if self.on_response_callback:
                self.on_response_callback(response)

            self._speak_response(response)
            self.save_conversation_history()

        except Exception as e:
            print(f"[Engine] Error: {e}")

    def _speak_response(self, text):
        """Speak response with Twitch context"""
        if not text.strip():
            return

        tts_text = text

        # Add Twitch context if applicable
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
                tts_text = " ".join(prepend_parts) + ". " + text

        def speak_thread():
            self.tts.speak(tts_text)

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()

    def _show_avatar(self, state):
        """Show avatar in specific state"""
        if self.avatar_window:
            if state == 'speaking':
                self.avatar_window.show_speaking()
            else:
                self.avatar_window.show_idle()

    def toggle_avatar_window(self):
        """Toggle avatar window"""
        if self.avatar_window:
            self.avatar_window.toggle()
            return self.avatar_window.is_visible()
        return False

    def save_conversation_history(self):
        """Save conversation to file"""
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

            except Exception as e:
                print(f"[Engine] Error saving history: {e}")

    def set_config(self, key, value):
        """Update config"""
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