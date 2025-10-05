"""
Input Handlers - Twitch Chat, Microphone, Screen Capture
"""

import os
import threading
import queue
import speech_recognition as sr
from PIL import ImageGrab, Image
import base64
from io import BytesIO
import socket


# Twitch IRC Handler
class TwitchChatHandler:
    def __init__(self, channel, oauth_token=None):
        """Initialize Twitch chat connection"""
        self.channel = channel.lower().replace('#', '')
        self.oauth_token = oauth_token or os.getenv('TWITCH_OAUTH_TOKEN')
        self.message_queue = queue.Queue()
        self.running = False
        self.connection = None
        self.thread = None

        # Twitch IRC settings
        self.server = 'irc.chat.twitch.tv'
        self.port = 6667
        self.nickname = 'chatbot'

    def start(self):
        """Start listening to Twitch chat"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._connect_and_listen, daemon=True)
        self.thread.start()
        print(f"[Twitch] Started listening to #{self.channel}")

    def stop(self):
        """Stop listening to Twitch chat"""
        self.running = False
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
        print("[Twitch] Stopped")

    def _connect_and_listen(self):
        """Connect to Twitch IRC and listen for messages"""
        try:
            # Create socket connection
            self.connection = socket.socket()
            self.connection.connect((self.server, self.port))

            # Authenticate
            if self.oauth_token:
                self.connection.send(f"PASS {self.oauth_token}\r\n".encode('utf-8'))
            else:
                self.connection.send(f"PASS oauth:your_token_here\r\n".encode('utf-8'))

            self.connection.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
            self.connection.send(f"JOIN #{self.channel}\r\n".encode('utf-8'))

            print(f"[Twitch] Connected to #{self.channel}")

            # Listen for messages
            while self.running:
                try:
                    response = self.connection.recv(2048).decode('utf-8')

                    if response.startswith('PING'):
                        # Respond to ping
                        self.connection.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))

                    elif 'PRIVMSG' in response:
                        # Parse chat message
                        username = response.split('!')[0][1:]
                        message = response.split('PRIVMSG')[1].split(':')[1].strip()

                        # Add to queue
                        self.message_queue.put({
                            'username': username,
                            'message': message
                        })

                        print(f"[Twitch] {username}: {message}")

                except Exception as e:
                    if self.running:
                        print(f"[Twitch] Error receiving: {e}")
                    break

        except Exception as e:
            print(f"[Twitch] Connection error: {e}")

    def get_message(self):
        """Get next message from queue (non-blocking)"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    def has_messages(self):
        """Check if there are pending messages"""
        return not self.message_queue.empty()


# Microphone Handler
class MicrophoneHandler:
    def __init__(self):
        """Initialize microphone handler"""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_available = False

        # Try to initialize microphone
        try:
            self.microphone = sr.Microphone()

            # Adjust for ambient noise
            print("[Mic] Calibrating microphone...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[Mic] Ready!")
            self.is_available = True

        except Exception as e:
            print(f"[Mic] Warning: Microphone not available - {e}")
            print("[Mic] Voice input will be disabled")
            self.is_available = False

    def listen_once(self, timeout=10):
        """Listen for speech and return transcribed text"""
        if not self.is_available:
            print("[Mic] Microphone not available")
            return None

        try:
            print("[Mic] Listening...")
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

            print("[Mic] Processing speech...")

            # Try Google Speech Recognition (free)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"[Mic] Recognized: {text}")
                return text
            except sr.UnknownValueError:
                print("[Mic] Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"[Mic] Recognition error: {e}")
                return None

        except sr.WaitTimeoutError:
            print("[Mic] Listening timeout")
            return None
        except Exception as e:
            print(f"[Mic] Error: {e}")
            return None

    def listen_continuous(self, callback, stop_event):
        """Continuously listen and call callback with transcribed text"""

        def listen_thread():
            while not stop_event.is_set():
                text = self.listen_once(timeout=5)
                if text and callback:
                    callback(text)

        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()
        return thread


# Screen Capture Handler
class ScreenCaptureHandler:
    def __init__(self):
        """Initialize screen capture handler"""
        self.last_capture = None

    def capture_screen(self, region=None):
        """Capture screenshot and return as base64 encoded image"""
        try:
            # Capture screen
            if region:
                # region should be (left, top, right, bottom)
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()

            # Resize if too large (to save tokens)
            max_size = (1024, 1024)
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Convert to base64
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            self.last_capture = img_base64

            # Return as data URL for OpenAI Vision API
            return f"data:image/png;base64,{img_base64}"

        except Exception as e:
            print(f"[Screen] Capture error: {e}")
            return None

    def get_last_capture(self):
        """Get the last captured screenshot"""
        if self.last_capture:
            return f"data:image/png;base64,{self.last_capture}"
        return None

    def capture_window(self, window_title):
        """Capture specific window (platform-specific)"""
        # This would require platform-specific code (pygetwindow on Windows)
        # For now, just capture full screen
        return self.capture_screen()


# Combined Input Manager
class InputManager:
    def __init__(self):
        """Initialize all input handlers"""
        self.twitch = None
        self.microphone = MicrophoneHandler()
        self.screen = ScreenCaptureHandler()

        self.enabled_inputs = {
            'twitch': False,
            'microphone': True,
            'screen': False
        }

    def enable_twitch(self, channel, oauth_token=None):
        """Enable Twitch chat input"""
        self.twitch = TwitchChatHandler(channel, oauth_token)
        self.twitch.start()
        self.enabled_inputs['twitch'] = True

    def disable_twitch(self):
        """Disable Twitch chat input"""
        if self.twitch:
            self.twitch.stop()
        self.enabled_inputs['twitch'] = False

    def enable_microphone(self):
        """Enable microphone input"""
        self.enabled_inputs['microphone'] = True

    def disable_microphone(self):
        """Disable microphone input"""
        self.enabled_inputs['microphone'] = False

    def enable_screen(self):
        """Enable screen capture"""
        self.enabled_inputs['screen'] = True

    def disable_screen(self):
        """Disable screen capture"""
        self.enabled_inputs['screen'] = False

    def get_twitch_messages(self):
        """Get all pending Twitch messages"""
        messages = []
        if self.twitch and self.enabled_inputs['twitch']:
            while self.twitch.has_messages():
                msg = self.twitch.get_message()
                if msg:
                    messages.append(msg)
        return messages

    def listen_microphone(self, timeout=10):
        """Listen for microphone input once"""
        if self.enabled_inputs['microphone']:
            return self.microphone.listen_once(timeout)
        return None

    def capture_screen(self):
        """Capture screen if enabled"""
        if self.enabled_inputs['screen']:
            return self.screen.capture_screen()
        return None


if __name__ == '__main__':
    # Test input handlers
    print("Testing Input Handlers...")

    # Test microphone
    print("\n=== Testing Microphone ===")
    mic = MicrophoneHandler()
    print("Say something...")
    text = mic.listen_once(timeout=5)
    if text:
        print(f"You said: {text}")

    # Test screen capture
    print("\n=== Testing Screen Capture ===")
    screen = ScreenCaptureHandler()
    capture = screen.capture_screen()
    if capture:
        print(f"Screen captured! (base64 length: {len(capture)})")

    print("\nTests complete!")