"""
Chatbot Engine - Main integration module
UPDATED: Added Twitch TTS output controls for username and message reading
"""

import json
import threading
import time
from pathlib import Path
from llm_manager import LLMManager
from tts_manager import TTSManager
from input_handlers import InputManager
from PIL import Image
import tkinter as tk
import os
from dotenv import load_dotenv

# Load environment variables at module import
env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)
    print("[Engine] Loaded environment variables from .env")
else:
    print("[Engine] Warning: No .env file found")

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

        # NEW: Twitch TTS context tracking
        self.current_twitch_username = None
        self.current_twitch_message = None

        # Avatar images
        self.speaking_image = None
        self.idle_image = None
        self.current_image_window = None

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
        """Return default configuration - UPDATED with Twitch TTS settings"""
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

            # NEW: Twitch TTS output controls
            'twitch_speak_username': True,  # TTS says username before response
            'twitch_speak_message': True,   # TTS says user's message before response
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

                print(f"[Engine] Saved conversation history to {self.history_file}")
            except Exception as e:
                print(f"[Engine] Error saving conversation history: {e}")

    def load_conversation_history(self):
        """Load conversation history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)

                if self.llm and 'conversation' in history_data:
                    self.llm.chat_history = history_data['conversation']
                    print(f"[Engine] Loaded conversation history from {self.history_file}")
                    return True
            except Exception as e:
                print(f"[Engine] Error loading conversation history: {e}")
        return False

    def _build_system_prompt(self):
        """Build system prompt with personality and length instructions"""
        system_prompt = self.config['personality']

        # Add AI name
        if self.config['ai_name'] != 'Assistant':
            system_prompt += f"\n\nYour name is {self.config['ai_name']}."

        # Add user name
        if self.config['user_name'] != 'User':
            system_prompt += f"\nYou are talking to {self.config['user_name']}."

        # Add response length instructions
        response_length = self.config.get('response_length', 'normal')

        if response_length == 'brief':
            system_prompt += "\n\nIMPORTANT: Keep ALL responses very brief and concise - typically 1-2 sentences (20-40 words max). Be direct and to the point."
        elif response_length == 'normal':
            system_prompt += "\n\nKeep responses concise and engaging - typically 2-4 sentences (40-80 words). Avoid long paragraphs unless specifically asked."
        elif response_length == 'detailed':
            system_prompt += "\n\nProvide thorough, detailed responses with explanations and context when helpful. Aim for 4-8 sentences (80-150 words) for most answers."

        # Add response style
        response_style = self.config.get('response_style', 'conversational')

        if response_style == 'casual':
            system_prompt += "\n\nUse a casual, friendly tone. Feel free to use contractions and casual language."
        elif response_style == 'professional':
            system_prompt += "\n\nMaintain a professional, polished tone. Use proper grammar and formal language."
        elif response_style == 'conversational':
            system_prompt += "\n\nUse a warm, conversational tone that's friendly but clear."
        elif response_style == 'custom':
            # Use custom style text if provided
            custom_style = self.config.get('custom_response_style', '')
            if custom_style:
                system_prompt += f"\n\n{custom_style}"

        return system_prompt

    def initialize(self):
        """Initialize all components with current config"""
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

        if self.config['twitch_enabled'] and self.config['twitch_channel']:
            self.inputs.enable_twitch(self.config['twitch_channel'])

        if self.config['mic_enabled']:
            self.inputs.enable_microphone()

        if self.config['screen_enabled']:
            self.inputs.enable_screen()

        self._load_images()

        print("[Engine] Initialized successfully!")

    def _load_images(self):
        """Load speaking and idle avatar images"""
        try:
            if self.config['speaking_image'] and Path(self.config['speaking_image']).exists():
                self.speaking_image = Image.open(self.config['speaking_image'])
                print(f"[Engine] Loaded speaking image: {self.config['speaking_image']}")

            if self.config['idle_image'] and Path(self.config['idle_image']).exists():
                self.idle_image = Image.open(self.config['idle_image'])
                print(f"[Engine] Loaded idle image: {self.config['idle_image']}")
        except Exception as e:
            print(f"[Engine] Error loading images: {e}")

    def start(self):
        """Start the chatbot engine"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True
        print(f"[Engine] {self.config['ai_name']} is now running!")

        if self.config['twitch_enabled'] and self.inputs.twitch:
            self.start_twitch_polling()

        if self.idle_image:
            self._show_image(self.idle_image)

    def stop(self):
        """Stop the chatbot engine"""
        self.is_running = False

        # Stop Twitch polling
        self.stop_twitch_polling()

        if self.inputs.twitch:
            self.inputs.disable_twitch()

        print("[Engine] Stopped")

    def start_twitch_polling(self):
        """Start polling Twitch chat for messages"""
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
        """Poll Twitch chat for messages and respond - UPDATED with TTS context tracking"""
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
                            # NEW: Store Twitch context for TTS
                            self.current_twitch_username = username
                            self.current_twitch_message = message

                            # Format the input for AI
                            if self.config.get('twitch_read_username', True):
                                user_input = f"{username} says: {message}"
                            else:
                                user_input = message

                            print(f"[Engine] Responding to Twitch: {user_input}")

                            # Process and respond
                            self._process_and_respond(user_input)

                            # NEW: Clear Twitch context after processing
                            self.current_twitch_username = None
                            self.current_twitch_message = None

                            self.last_twitch_response_time = current_time
                        else:
                            remaining = cooldown - (current_time - self.last_twitch_response_time)
                            print(f"[Engine] Twitch cooldown: {remaining:.1f}s remaining")

                time.sleep(0.5)

            except Exception as e:
                print(f"[Engine] Twitch polling error: {e}")
                time.sleep(1)

    def _should_respond_to_twitch(self, message):
        """Determine if bot should respond to Twitch message"""
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
        """Listen to microphone and process input"""
        if not self.inputs.enabled_inputs['microphone']:
            print("[Engine] Microphone is disabled")
            return

        print(f"[Engine] Listening to microphone...")

        user_text = self.inputs.listen_microphone(timeout=10)

        if user_text:
            screen_data = None
            if self.inputs.enabled_inputs['screen']:
                screen_data = self.inputs.capture_screen()
                print("[Engine] Screen captured for vision input")

            self._process_and_respond(user_text, screen_data)
        else:
            print("[Engine] No speech detected")

    def process_twitch_messages(self):
        """DEPRECATED: Use start_twitch_polling() instead"""
        print("[Engine] WARNING: process_twitch_messages() is deprecated. Twitch polling is automatic when enabled.")

    def process_text_input(self, text):
        """Process direct text input"""
        if text.strip():
            self._process_and_respond(text)

    def _process_and_respond(self, user_input, image_data=None):
        """Process input and generate response"""
        if not self.is_running:
            return

        print(f"[Engine] Processing: {user_input[:100]}")

        try:
            response_length = self.config.get('response_length', 'normal')

            if response_length == 'brief':
                max_tokens = 60
            elif response_length == 'normal':
                max_tokens = 150
            elif response_length == 'detailed':
                max_tokens = 300
            elif response_length == 'custom':
                max_tokens = self.config.get('max_response_tokens', 150)
            else:
                max_tokens = 150

            print(f"[Engine] Max response tokens: {max_tokens}")

            model = self.config['llm_model']
            vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
            supports_vision = model in vision_models

            print(f"[Engine] Model: {model}, Supports vision: {supports_vision}, Has image: {bool(image_data)}")

            if image_data and supports_vision:
                print("[Engine] Using vision model with image")
                response = self.llm.chat_with_vision(
                    user_input,
                    image_data,
                    max_response_tokens=max_tokens
                )
            elif image_data and not supports_vision:
                print(f"[Engine] WARNING: Model '{model}' doesn't support vision, using text-only")
                response = self.llm.chat(
                    user_input,
                    max_response_tokens=max_tokens
                )
                response = f"[Note: I can't see images with {model}. Please use gpt-4o for vision.]\n\n" + response
            else:
                print("[Engine] Using text-only mode")
                response = self.llm.chat(
                    user_input,
                    max_response_tokens=max_tokens
                )

            print(f"[Engine] Response: {response[:100]}")

            if self.on_response_callback:
                self.on_response_callback(response)

            self._speak_response(response)

            self.save_conversation_history()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Engine] Error processing input: {error_details}")

            error_response = f"Sorry, I encountered an error: {str(e)}"
            if self.on_response_callback:
                self.on_response_callback(error_response)

    def _speak_response(self, text):
        """Convert response to speech - UPDATED with Twitch username/message reading"""
        if not text.strip():
            return

        # NEW: Construct full TTS message with Twitch context if applicable
        tts_text = text

        # If responding to Twitch message, prepend username/message based on settings
        if self.current_twitch_username or self.current_twitch_message:
            prepend_parts = []

            # Check if we should speak the username
            if self.config.get('twitch_speak_username', True) and self.current_twitch_username:
                prepend_parts.append(self.current_twitch_username)

            # Check if we should speak the message
            if self.config.get('twitch_speak_message', True) and self.current_twitch_message:
                if prepend_parts:
                    # We have username, so format as "username said: message"
                    prepend_parts.append(f"said: {self.current_twitch_message}")
                else:
                    # No username, just say the message
                    prepend_parts.append(self.current_twitch_message)

            # Construct the prepend text
            if prepend_parts:
                prepend_text = " ".join(prepend_parts)
                tts_text = f"{prepend_text}. {text}"
                print(f"[Engine] TTS with Twitch context: {tts_text[:100]}...")

        def speak_thread():
            self.tts.speak(
                tts_text,
                callback_on_start=self._on_speaking_start,
                callback_on_end=self._on_speaking_end
            )

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()

    def _on_speaking_start(self):
        """Called when TTS starts speaking"""
        self.is_speaking = True

        if self.speaking_image:
            self._show_image(self.speaking_image)

        if self.on_speaking_start:
            self.on_speaking_start()

        print("[Engine] Started speaking")

    def _on_speaking_end(self):
        """Called when TTS finishes speaking"""
        self.is_speaking = False

        if self.idle_image:
            self._show_image(self.idle_image)

        if self.on_speaking_end:
            self.on_speaking_end()

        print("[Engine] Finished speaking")

    def _show_image(self, image):
        """Update the current avatar file for OBS to monitor"""
        try:
            import shutil

            # Ensure images folder exists
            images_folder = Path('images')
            images_folder.mkdir(exist_ok=True)

            # Get the source image path
            if image == self.speaking_image:
                source_path = self.config.get('speaking_image', '')
                print(f"[Engine] Switching to SPEAKING avatar")
            elif image == self.idle_image:
                source_path = self.config.get('idle_image', '')
                print(f"[Engine] Switching to IDLE avatar")
            else:
                return

            if not source_path or not Path(source_path).exists():
                print(f"[Engine] Avatar image not found: {source_path}")
                return

            # Copy to images/current_avatar.png that OBS can monitor
            output_path = images_folder / 'current_avatar.png'
            shutil.copy2(source_path, output_path)
            print(f"[Engine] Updated images/current_avatar.png")

        except Exception as e:
            print(f"[Engine] Error updating avatar file: {e}")

    def set_config(self, key, value):
        """Update configuration value"""
        self.config[key] = value

    def reload_config(self):
        """Reload configuration and reinitialize"""
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