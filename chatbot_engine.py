import json
import threading
import time
from pathlib import Path
from collections import deque
from llm_manager import LLMManager
from tts_manager import TTSManager
from input_handlers import InputManager
from avatar_window import AvatarWindow
import os
from dotenv import load_dotenv
import re

env_file = Path('.env')
if env_file.exists():
    load_dotenv(env_file)


class ChatbotEngine:
    def __init__(self, config_file='chatbot_config.json'):
        """Initialize chatbot engine with audio-reactive avatar"""
        self.config_file = Path(config_file)
        self.history_file = Path('conversation_history.json')
        self.load_config()

        self.llm = None
        self.tts = None
        self.inputs = InputManager()

        self.is_running = False
        self.is_speaking = False
        self.current_thread = None

        self.twitch_thread = None
        self.twitch_running = False
        self.last_twitch_response_time = 0
        self.current_twitch_username = None
        self.current_twitch_message = None

        self.avatar_window = None

        self.on_response_callback = None
        self.on_speaking_start = None
        self.on_speaking_end = None
        self.on_volume_update = None

        # TTS queue system for sequential speaking
        self.tts_queue = deque()
        self.tts_processing = False
        self.tts_lock = threading.Lock()

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
            'tts_service': 'streamelements',
            'elevenlabs_voice': 'Brian',
            'twitch_enabled': False,
            'twitch_channel': '',
            'twitch_username_blacklist': [],
            'twitch_emote_prefix_blacklist': [],
            'twitch_cooldown': 5,
            'twitch_response_mode': 'all',
            'twitch_keywords': '!ai,!bot',
            'twitch_response_chance': 100,
            'twitch_read_username': True,
            'twitch_speak_username': True,
            'twitch_speak_message': True,
            'twitch_strip_emojis': True,
            'mic_enabled': True,
            'screen_enabled': False,
            'hotkey_toggle': 'F4',
            'hotkey_stop': 'P',
            'hotkey_screenshot': 'F5',
            'speaking_image': '',
            'idle_image': '',
            'avatar_bg_color': '#00FF00',
            'avatar_transparency': False,
            'max_context_tokens': 8000,
            'volume_threshold': 0.02,
            'elevenlabs_stability': 0.5,
            'elevenlabs_similarity': 0.75,
            'elevenlabs_style': 0.0,
            'elevenlabs_speaker_boost': True,
            'response_length': 'normal',
            'max_response_tokens': 150,
            'rate_limit_response': "I'm a bit overwhelmed right now, give me a moment!"
        }

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def set_config(self, key, value):
        """Update config"""
        self.config[key] = value

    def reload_config(self):
        """Reload configuration"""
        self.load_config()
        self.initialize()

    def initialize(self):
        """Initialize LLM and TTS"""
        system_prompt = self._build_system_prompt()

        self.llm = LLMManager(
            model=self.config['llm_model'],
            system_prompt=system_prompt
        )

        elevenlabs_settings = {
            'stability': self.config.get('elevenlabs_stability', 0.5),
            'similarity_boost': self.config.get('elevenlabs_similarity', 0.75),
            'style': self.config.get('elevenlabs_style', 0.0),
            'use_speaker_boost': self.config.get('elevenlabs_speaker_boost', True)
        }

        self.tts = TTSManager(
            service=self.config['tts_service'],
            voice=self.config.get('elevenlabs_voice', 'default'),
            elevenlabs_settings=elevenlabs_settings
        )

        self.tts.set_audio_callbacks(
            on_start=self._on_audio_start,
            on_active=self._on_audio_active,
            on_silent=self._on_audio_silent,
            on_end=self._on_audio_end
        )

        self.tts.set_volume_threshold(self.config.get('volume_threshold', 0.02))

        if self.config.get('twitch_enabled', False) and self.config.get('twitch_channel'):
            channel = self.config['twitch_channel']
            oauth_token = os.getenv('TWITCH_OAUTH_TOKEN', '')

            if oauth_token and not self.inputs.twitch:
                self.inputs.enable_twitch(channel, oauth_token)

        if self.config.get('speaking_image') and self.config.get('idle_image'):
            if not self.avatar_window:
                self.avatar_window = AvatarWindow(
                    idle_image_path=self.config['idle_image'],
                    speaking_image_path=self.config['speaking_image'],
                    bg_color=self.config.get('avatar_bg_color', '#00FF00'),
                    transparent=self.config.get('avatar_transparency', False),
                    always_on_top=False
                )

    def _build_system_prompt(self):
        """Build system prompt with personality and settings"""
        system_prompt = self.config['personality']

        if self.config['ai_name'] != 'Assistant':
            system_prompt += f"\n\nYour name is {self.config['ai_name']}."

        if self.config['user_name'] != 'User':
            system_prompt += f"\nYou are talking to {self.config['user_name']}."

        response_length = self.config.get('response_length', 'normal')
        if response_length == 'brief':
            system_prompt += "\n\nIMPORTANT: Keep ALL responses very brief and concise - typically 1-2 sentences (20-40 words max)."
        elif response_length == 'normal':
            system_prompt += "\n\nKeep responses concise and engaging - typically 2-4 sentences (40-80 words)."
        elif response_length == 'detailed':
            system_prompt += "\n\nProvide thorough, detailed responses - typically 4-8 sentences (80-150 words)."

        return system_prompt

    def start(self):
        """Start the chatbot"""
        if not self.llm or not self.tts:
            self.initialize()

        self.is_running = True

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

    def _on_audio_start(self):
        """Called when audio playback starts"""
        self.is_speaking = True

        if self.on_speaking_start:
            self.on_speaking_start()

    def _on_audio_active(self):
        """Called when volume rises above threshold"""
        if self.avatar_window:
            self.avatar_window.show_speaking()

        if self.on_volume_update and self.tts:
            volume = self.tts.get_current_volume()
            self.on_volume_update(volume)

    def _on_audio_silent(self):
        """Called when volume drops below threshold"""
        if self.avatar_window:
            self.avatar_window.show_idle()

        if self.on_volume_update and self.tts:
            volume = self.tts.get_current_volume()
            self.on_volume_update(volume)

    def _on_audio_end(self):
        """Called when audio playback ends"""
        self.is_speaking = False

        if self.avatar_window:
            self.avatar_window.show_idle()

        if self.on_speaking_end:
            self.on_speaking_end()

    def set_volume_threshold(self, threshold):
        """Update volume threshold for audio detection"""
        self.config['volume_threshold'] = threshold
        if self.tts:
            self.tts.set_volume_threshold(threshold)

    def start_twitch_polling(self):
        """Start polling Twitch chat"""
        if self.twitch_running:
            return

        self.twitch_running = True
        self.twitch_thread = threading.Thread(target=self._twitch_poll_loop, daemon=True)
        self.twitch_thread.start()

    def stop_twitch_polling(self):
        """Stop Twitch polling"""
        self.twitch_running = False
        if self.twitch_thread:
            self.twitch_thread.join(timeout=2)

    def _twitch_poll_loop(self):
        """Poll Twitch for messages"""
        while self.twitch_running and self.is_running:
            try:
                messages = self.inputs.get_twitch_messages()

                for msg in messages:
                    if not self.twitch_running:
                        break

                    username = msg['username']
                    message = msg['message']

                    # CHECK USERNAME BLACKLIST
                    blacklist = self.config.get('twitch_username_blacklist', [])
                    if username.lower() in [u.lower() for u in blacklist]:
                        continue  # Skip blacklisted users

                    should_respond = self._should_respond_to_twitch(message)

                    if should_respond:
                        current_time = time.time()
                        cooldown = self.config.get('twitch_cooldown', 5)

                        if current_time - self.last_twitch_response_time >= cooldown:
                            cleaned_message = self._strip_keyword_from_message(message)
                            cleaned_message = self._strip_emojis(cleaned_message)
                            cleaned_message = self._strip_custom_emotes(cleaned_message)

                            self.current_twitch_username = username
                            self.current_twitch_message = cleaned_message

                            if self.config.get('twitch_read_username', True):
                                user_input = f"{username} says: {cleaned_message}"
                            else:
                                user_input = cleaned_message

                            self._process_and_respond(user_input)

                            self.current_twitch_username = None
                            self.current_twitch_message = None
                            self.last_twitch_response_time = current_time

                time.sleep(0.5)

            except Exception:
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

    def _strip_keyword_from_message(self, message):
        """Remove keyword from message if in keywords mode"""
        response_mode = self.config.get('twitch_response_mode', 'all')

        if response_mode != 'keywords':
            return message

        keywords = self.config.get('twitch_keywords', '!ai,!bot').split(',')
        message_lower = message.lower()

        for keyword in keywords:
            keyword = keyword.strip()
            keyword_lower = keyword.lower()

            if keyword_lower in message_lower:
                pos = message_lower.find(keyword_lower)
                message = (message[:pos] + message[pos + len(keyword):]).strip()
                break

        return message

    def _strip_custom_emotes(self, text):
        """Remove custom emotes with blacklisted prefixes"""
        prefix_blacklist = self.config.get('twitch_emote_prefix_blacklist', [])

        if not prefix_blacklist:
            return text

        # Pattern matches :prefix_emotename: or prefix_emotename
        for prefix in prefix_blacklist:
            # Match both :prefix_xxx: and prefix_xxx patterns
            pattern = rf':?{re.escape(prefix)}_?\w*:?'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _strip_emojis(self, text):
        """Remove emojis, emoticons, and Twitch emotes from text"""
        if not self.config.get('twitch_strip_emojis', True):
            return text

        # Remove Unicode emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002500-\U00002BEF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)

        # Remove text-based emoticons
        emoticon_patterns = [
            r':\)+', r':\(+', r':D+', r':P+', r':O+', r';\)+',
            r'XD+', r'xD+', r'>:\(+', r':\|+', r':/+', r':\\+',
            r'<3+', r':3+', r':\*+', r';P+', r':S+', r':@+',
            r'T_T+', r'ToT+', r'\^\^+', r'o\.o', r'O\.O',
            r'-_-+', r'>_<+', r'=\)+', r'=\(+', r'=D+', r'=P+'
        ]

        for pattern in emoticon_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove common Twitch emotes
        common_twitch_emotes = [
            'Kappa', 'PogChamp', 'LUL', 'TriHard', 'BibleThump', 'SMOrc', 'MingLee',
            'KappaPride', 'Kreygasm', 'DansGame', 'NotLikeThis', 'ResidentSleeper',
            'FailFish', 'WutFace', 'PJSalt', 'CoolStoryBob', 'EleGiggle', '4Head',
            'KEKW', 'PepeLaugh', 'monkaS', 'Sadge', 'OMEGALUL', 'LULW', 'POGGERS',
            'Pepega', 'FeelsGoodMan', 'FeelsBadMan', 'GIGACHAD', 'Copium', 'NOTED'
        ]

        for emote in common_twitch_emotes:
            pattern = r'\b' + re.escape(emote) + r'\b'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove excessive repeated characters
        text = re.sub(r'(.)\1{3,}', r'\1', text)

        # Clean up spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def process_microphone_input(self):
        """Process microphone input"""
        if not self.inputs.enabled_inputs['microphone']:
            return

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

        try:
            response_length = self.config.get('response_length', 'normal')
            if response_length == 'brief':
                max_tokens = 60
            elif response_length == 'detailed':
                max_tokens = 300
            elif response_length == 'custom':
                max_tokens = self.config.get('max_response_tokens', 150)
            else:
                max_tokens = 150

            model = self.config['llm_model']
            vision_models = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']

            try:
                if image_data and model in vision_models:
                    response = self.llm.chat_with_vision(user_input, image_data, max_response_tokens=max_tokens)
                else:
                    response = self.llm.chat(user_input, max_response_tokens=max_tokens)

            except Exception as e:
                # HANDLE RATE LIMITING
                error_str = str(e).lower()
                if 'rate' in error_str or 'quota' in error_str or 'limit' in error_str or '429' in error_str:
                    response = self.config.get('rate_limit_response',
                                               "I'm a bit overwhelmed right now, give me a moment!")
                else:
                    raise

            if self.on_response_callback:
                self.on_response_callback(response)

            # QUEUE THE SPEECH instead of speaking directly
            self._queue_speech(response)
            self.save_conversation_history()

        except Exception:
            pass

    def _queue_speech(self, text):
        """Add speech to queue for sequential processing"""
        with self.tts_lock:
            self.tts_queue.append(text)

            # Start processing if not already running
            if not self.tts_processing:
                self.tts_processing = True
                threading.Thread(target=self._process_tts_queue, daemon=True).start()

    def _process_tts_queue(self):
        """Process TTS queue sequentially - ensures bot finishes speaking before next message"""
        while True:
            with self.tts_lock:
                if not self.tts_queue:
                    self.tts_processing = False
                    break

                text = self.tts_queue.popleft()

            # Speak the response (blocks until complete)
            self._speak_response(text)

    def _speak_response(self, text):
        """Speak response with Twitch context"""
        if not text.strip():
            return

        # STRIP EMOJIS FROM BOT'S OUTPUT
        clean_text = self._strip_emojis(text)

        tts_text = clean_text

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
                tts_text = " ".join(prepend_parts) + ". " + clean_text

        def speak_thread():
            self.tts.speak(tts_text)

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
        thread.join()  # Wait for speech to complete

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

            except Exception:
                pass


if __name__ == '__main__':
    engine = ChatbotEngine()
    engine.initialize()
    engine.start()

    engine.process_text_input("Hello! Can you introduce yourself?")

    time.sleep(5)

    engine.stop()