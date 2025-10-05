"""
Chatbot Engine - Main integration module
Connects LLM, TTS, and Input handlers
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
            'elevenlabs_speaker_boost': True
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

    def initialize(self):
        """Initialize all components with current config"""
        # Build system prompt with personality
        system_prompt = self.config['personality']
        if self.config['ai_name'] != 'Assistant':
            system_prompt += f"\n\nYour name is {self.config['ai_name']}."
        if self.config['user_name'] != 'User':
            system_prompt += f"\nYou are talking to {self.config['user_name']}."

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
        """Start the chatbot engine"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True
        print(f"[Engine] {self.config['ai_name']} is now running!")

        # Show idle image
        if self.idle_image:
            self._show_image(self.idle_image)

    def stop(self):
        """Stop the chatbot engine"""
        self.is_running = False
        if self.inputs.twitch:
            self.inputs.disable_twitch()

        # Hide image window
        if self.current_image_window:
            try:
                self.current_image_window.destroy()
            except:
                pass

        print("[Engine] Stopped")

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
        """Process pending Twitch chat messages"""
        if not self.inputs.enabled_inputs['twitch']:
            return

        messages = self.inputs.get_twitch_messages()

        for msg in messages:
            username = msg['username']
            message = msg['message']

            # Format input with username
            user_input = f"{username} says: {message}"

            # Process and respond
            self._process_and_respond(user_input)

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
            # Get LLM response
            # Check if model supports vision
            vision_models = ['gpt-5', 'gpt-5-mini', 'gpt-4.1', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
            supports_vision = any(model in self.config['llm_model'] for model in vision_models)

            if image_data and supports_vision:
                response = self.llm.chat_with_vision(user_input, image_data)
            else:
                response = self.llm.chat(user_input)

            print(f"[Engine] Response: {response[:100]}")

            # Callback for response
            if self.on_response_callback:
                self.on_response_callback(response)

            # Speak response
            self._speak_response(response)

            # Auto-save conversation history after each interaction
            self.save_conversation_history()

        except Exception as e:
            print(f"[Engine] Error processing input: {e}")

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