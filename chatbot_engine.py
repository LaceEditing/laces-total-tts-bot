"""
Chatbot Engine - Main integration module
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
        """Return default configuration - UPDATED with new settings"""
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

            # NEW: Response length settings
            'response_length': 'normal',  # brief, normal, detailed, custom
            'max_response_tokens': 150,  # Used when response_length is 'custom'
            'response_style': 'conversational',  # conversational, professional, casual

            # NEW: Twitch integration settings
            'twitch_read_username': True,  # Include username in prompt
            'twitch_response_mode': 'all',  # all, keywords, random, timed
            'twitch_response_chance': 100,  # Percentage chance to respond (for random mode)
            'twitch_cooldown': 5,  # Seconds between responses
            'twitch_keywords': '!ai,!bot,!ask',  # Comma-separated keywords to trigger response
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
        """Build system prompt with personality and length instructions - NEW"""
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
        # 'custom' uses max_response_tokens setting directly

        # Add response style
        response_style = self.config.get('response_style', 'conversational')

        if response_style == 'casual':
            system_prompt += "\n\nUse a casual, friendly tone. Feel free to use contractions and casual language."
        elif response_style == 'professional':
            system_prompt += "\n\nMaintain a professional, polished tone. Use proper grammar and formal language."
        elif response_style == 'conversational':
            system_prompt += "\n\nUse a warm, conversational tone that's friendly but clear."

        return system_prompt

    def initialize(self):
        """Initialize all components with current config"""
        # Build system prompt with all settings
        system_prompt = self._build_system_prompt()

        # Initialize LLM
        self.llm = LLMManager(
            model=self.config['llm_model'],
            system_prompt=system_prompt,
            max_tokens=self.config.get('max_context_tokens', 8000)
        )

        # Initialize TTS
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

        # Initialize inputs
        if self.config['twitch_enabled'] and self.config['twitch_channel']:
            self.inputs.enable_twitch(self.config['twitch_channel'])

        if self.config['mic_enabled']:
            self.inputs.enable_microphone()

        if self.config['screen_enabled']:
            self.inputs.enable_screen()

        # Load avatar images
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
        """Start the chatbot engine - UPDATED with Twitch polling"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True
        print(f"[Engine] {self.config['ai_name']} is now running!")

        # Start Twitch polling if enabled
        if self.config['twitch_enabled'] and self.inputs.twitch:
            self.start_twitch_polling()

        # Show idle image
        if self.idle_image:
            self._show_image(self.idle_image)

    def stop(self):
        """Stop the chatbot engine - UPDATED to stop Twitch polling"""
        self.is_running = False

        # Stop Twitch polling
        self.stop_twitch_polling()

        if self.inputs.twitch:
            self.inputs.disable_twitch()

        # Hide image window
        if self.current_image_window:
            try:
                self.current_image_window.destroy()
            except:
                pass

        print("[Engine] Stopped")

    def start_twitch_polling(self):
        """Start polling Twitch chat for messages - NEW"""
        if self.twitch_running:
            return

        self.twitch_running = True
        self.twitch_thread = threading.Thread(target=self._twitch_poll_loop, daemon=True)
        self.twitch_thread.start()
        print("[Engine] Twitch polling started")

    def stop_twitch_polling(self):
        """Stop polling Twitch chat - NEW"""
        self.twitch_running = False
        if self.twitch_thread:
            self.twitch_thread.join(timeout=2)
        print("[Engine] Twitch polling stopped")

    def _twitch_poll_loop(self):
        """Poll Twitch chat for messages and respond based on settings - NEW"""
        import random

        while self.twitch_running and self.is_running:
            try:
                messages = self.inputs.get_twitch_messages()

                for msg in messages:
                    if not self.twitch_running:
                        break

                    username = msg['username']
                    message = msg['message']

                    # Check if we should respond to this message
                    should_respond = self._should_respond_to_twitch(message)

                    if should_respond:
                        # Check cooldown
                        current_time = time.time()
                        cooldown = self.config.get('twitch_cooldown', 5)

                        if current_time - self.last_twitch_response_time >= cooldown:
                            # Format the input
                            if self.config.get('twitch_read_username', True):
                                user_input = f"{username} says: {message}"
                            else:
                                user_input = message

                            print(f"[Engine] Responding to Twitch: {user_input}")

                            # Process and respond
                            self._process_and_respond(user_input)

                            # Update last response time
                            self.last_twitch_response_time = current_time
                        else:
                            remaining = cooldown - (current_time - self.last_twitch_response_time)
                            print(f"[Engine] Twitch cooldown: {remaining:.1f}s remaining")

                # Sleep briefly before next poll
                time.sleep(0.5)

            except Exception as e:
                print(f"[Engine] Twitch polling error: {e}")
                time.sleep(1)

    def _should_respond_to_twitch(self, message):
        """Determine if bot should respond to Twitch message - NEW"""
        import random

        response_mode = self.config.get('twitch_response_mode', 'all')

        if response_mode == 'all':
            # Respond to every message
            return True

        elif response_mode == 'keywords':
            # Respond only if message contains keywords
            keywords = self.config.get('twitch_keywords', '!ai,!bot,!ask')
            keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
            message_lower = message.lower()

            return any(keyword in message_lower for keyword in keyword_list)

        elif response_mode == 'random':
            # Respond based on random chance
            chance = self.config.get('twitch_response_chance', 100)
            return random.randint(1, 100) <= chance

        elif response_mode == 'disabled':
            # Don't respond to any messages
            return False

        return False

    def process_microphone_input(self):
        """Listen to microphone and process input"""
        if not self.inputs.enabled_inputs['microphone']:
            print("[Engine] Microphone is disabled")
            return

        print(f"[Engine] Listening to microphone...")

        # Listen for speech
        user_text = self.inputs.listen_microphone(timeout=10)

        if user_text:
            # Check if screen capture is enabled
            screen_data = None
            if self.inputs.enabled_inputs['screen']:
                screen_data = self.inputs.capture_screen()
                print("[Engine] Screen captured for vision input")

            # Get LLM response
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
        """Process input and generate response - UPDATED with response length control"""
        if not self.is_running:
            return

        print(f"[Engine] Processing: {user_input[:100]}")

        try:
            # Determine max response tokens based on length setting
            response_length = self.config.get('response_length', 'normal')

            if response_length == 'brief':
                max_tokens = 60  # Very short responses
            elif response_length == 'normal':
                max_tokens = 150  # Standard responses
            elif response_length == 'detailed':
                max_tokens = 300  # Longer, detailed responses
            elif response_length == 'custom':
                max_tokens = self.config.get('max_response_tokens', 150)
            else:
                max_tokens = 150  # Default

            print(f"[Engine] Max response tokens: {max_tokens}")

            # Check vision support
            model = self.config['llm_model']
            vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
            supports_vision = model in vision_models

            print(f"[Engine] Model: {model}, Supports vision: {supports_vision}, Has image: {bool(image_data)}")

            # Get response
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

            # Callback for response
            if self.on_response_callback:
                self.on_response_callback(response)

            # Speak response
            self._speak_response(response)

            # Auto-save conversation history
            self.save_conversation_history()

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Engine] Error processing input: {error_details}")

            error_response = f"Sorry, I encountered an error: {str(e)}"
            if self.on_response_callback:
                self.on_response_callback(error_response)

    def _speak_response(self, text):
        """Convert response to speech"""
        if not text.strip():
            return

        def speak_thread():
            self.tts.speak(
                text,
                callback_on_start=self._on_speaking_start,
                callback_on_end=self._on_speaking_end
            )

        # Run in separate thread to not block
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()

    def _on_speaking_start(self):
        """Called when TTS starts speaking"""
        self.is_speaking = True

        # Show speaking image
        if self.speaking_image:
            self._show_image(self.speaking_image)

        # External callback
        if self.on_speaking_start:
            self.on_speaking_start()

        print("[Engine] Started speaking")

    def _on_speaking_end(self):
        """Called when TTS finishes speaking"""
        self.is_speaking = False

        # Show idle image
        if self.idle_image:
            self._show_image(self.idle_image)

        # External callback
        if self.on_speaking_end:
            self.on_speaking_end()

        print("[Engine] Finished speaking")

    def _show_image(self, image):
        """Display avatar image in overlay window"""
        try:
            # Simple implementation - could be enhanced with transparency
            if not self.current_image_window:
                self.current_image_window = tk.Toplevel()
                self.current_image_window.overrideredirect(True)
                self.current_image_window.attributes('-topmost', True)

                # Position in bottom right
                screen_width = self.current_image_window.winfo_screenwidth()
                screen_height = self.current_image_window.winfo_screenheight()
                x = screen_width - image.width - 50
                y = screen_height - image.height - 100
                self.current_image_window.geometry(f"+{x}+{y}")

                self.image_label = tk.Label(self.current_image_window)
                self.image_label.pack()

            # Update image
            from PIL import ImageTk
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Keep reference

        except Exception as e:
            print(f"[Engine] Error showing image: {e}")

    def set_config(self, key, value):
        """Update configuration value"""
        self.config[key] = value

    def reload_config(self):
        """Reload configuration and reinitialize"""
        self.load_config()
        self.initialize()


if __name__ == '__main__':
    # Test the engine
    print("Testing Chatbot Engine...")

    engine = ChatbotEngine()
    engine.initialize()
    engine.start()

    # Test text input
    print("\nSending test message...")
    engine.process_text_input("Hello! Can you introduce yourself?")

    # Wait for response
    time.sleep(5)

    print("\nTest complete!")
    engine.stop()