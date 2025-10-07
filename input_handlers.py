"""
Input Handlers - PRODUCTION BUILD (No Console Output)
Twitch Chat, Microphone, Screen Capture
"""

import os
import threading
import queue
import speech_recognition as sr
from PIL import ImageGrab, Image
import base64
from io import BytesIO
import socket


class TwitchChatHandler:
    def __init__(self, channel, oauth_token=None):
        """Initialize Twitch chat connection"""
        self.channel = channel.lower().replace('#', '')
        self.oauth_token = oauth_token or os.getenv('TWITCH_OAUTH_TOKEN')
        self.message_queue = queue.Queue()
        self.running = False
        self.connection = None
        self.thread = None

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

    def stop(self):
        """Stop listening to Twitch chat"""
        self.running = False
        if self.connection:
            try:
                self.connection.close()
            except:
                pass

    def _connect_and_listen(self):
        """Connect to Twitch IRC and listen for messages"""
        try:
            self.connection = socket.socket()
            self.connection.connect((self.server, self.port))

            if self.oauth_token:
                self.connection.send(f"PASS {self.oauth_token}\r\n".encode('utf-8'))
            else:
                self.connection.send(f"PASS oauth:your_token_here\r\n".encode('utf-8'))

            self.connection.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
            self.connection.send(f"JOIN #{self.channel}\r\n".encode('utf-8'))

            while self.running:
                try:
                    response = self.connection.recv(2048).decode('utf-8')

                    if response.startswith('PING'):
                        self.connection.send("PONG :tmi.twitch.tv\r\n".encode('utf-8'))

                    elif 'PRIVMSG' in response:
                        username = response.split('!')[0][1:]
                        message = response.split('PRIVMSG')[1].split(':')[1].strip()

                        self.message_queue.put({
                            'username': username,
                            'message': message
                        })

                except Exception:
                    if self.running:
                        break

        except Exception:
            pass

    def get_message(self):
        """Get next message from queue (non-blocking)"""
        try:
            return self.message_queue.get_nowait()
        except queue.Empty:
            return None

    def has_messages(self):
        """Check if there are pending messages"""
        return not self.message_queue.empty()


class MicrophoneHandler:
    def __init__(self):
        """Initialize microphone handler"""
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_available = False

        try:
            self.microphone = sr.Microphone()

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

            self.is_available = True

        except Exception:
            self.is_available = False

    def listen_once(self, timeout=10):
        """Listen for speech and return transcribed text"""
        if not self.is_available:
            return None

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return None
            except sr.RequestError:
                return None

        except sr.WaitTimeoutError:
            return None
        except Exception:
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


class ScreenCaptureHandler:
    def __init__(self):
        """Initialize screen capture handler"""
        self.last_capture = None

    def capture_screen(self, region=None):
        """Capture screenshot and return as base64 encoded image"""
        try:
            if region:
                screenshot = ImageGrab.grab(bbox=region)
            else:
                screenshot = ImageGrab.grab()

            max_size = (1024, 1024)
            screenshot.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

            self.last_capture = img_base64

            return f"data:image/png;base64,{img_base64}"

        except Exception:
            return None

    def get_last_capture(self):
        """Get the last captured screenshot"""
        if self.last_capture:
            return f"data:image/png;base64,{self.last_capture}"
        return None

    def capture_window(self, window_title):
        """Capture specific window (platform-specific)"""
        return self.capture_screen()


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