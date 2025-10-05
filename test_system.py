"""
System Test Script
Tests all components of the AI Chatbot System
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_imports():
    """Test if all required packages are installed"""
    print_header("Testing Python Packages")

    required_packages = {
        'openai': 'OpenAI',
        'tiktoken': 'Tiktoken',
        'speech_recognition': 'SpeechRecognition',
        'pygame': 'Pygame',
        'keyboard': 'Keyboard',
        'PIL': 'Pillow',
        'requests': 'Requests'
    }

    optional_packages = {
        'elevenlabs': 'ElevenLabs',
        'azure.cognitiveservices.speech': 'Azure Speech',
        'TTS': 'Coqui TTS'
    }

    all_passed = True

    # Test required packages
    print("\n📦 Required Packages:")
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} - NOT INSTALLED")
            all_passed = False

    # Test optional packages
    print("\n📦 Optional Packages:")
    for package, name in optional_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ⚠️  {name} - Not installed (optional)")

    return all_passed


def test_api_keys():
    """Test if API keys are configured"""
    print_header("Testing API Keys")

    # Try to load from .env file
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file found and loaded")
    else:
        print("⚠️  No .env file found (will use system environment variables)")

    keys_to_check = {
        'OPENAI_API_KEY': ('OpenAI', True),
        'ELEVENLABS_API_KEY': ('ElevenLabs', False),
        'AZURE_TTS_KEY': ('Azure TTS', False),
        'TWITCH_OAUTH_TOKEN': ('Twitch', False)
    }

    print("\n🔑 API Keys Status:")

    openai_configured = False

    for key, (name, required) in keys_to_check.items():
        value = os.getenv(key)
        if value and value != f'your-{key.lower().replace("_", "-")}-here':
            print(f"  ✅ {name} - Configured")
            if key == 'OPENAI_API_KEY':
                openai_configured = True
        else:
            if required:
                print(f"  ❌ {name} - NOT CONFIGURED (Required!)")
            else:
                print(f"  ⚠️  {name} - Not configured (optional)")

    return openai_configured


def test_openai_connection():
    """Test OpenAI API connection"""
    print_header("Testing OpenAI Connection")

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key.startswith('your-'):
        print("❌ OpenAI API key not configured")
        print("   Please set OPENAI_API_KEY in your .env file")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        print("🔄 Testing API connection...")

        # Simple test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test successful' and nothing else"}],
            max_tokens=10
        )

        result = response.choices[0].message.content
        print(f"✅ OpenAI API working! Response: {result}")
        return True

    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False


def test_microphone():
    """Test microphone access"""
    print_header("Testing Microphone")

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()

        print("🎤 Checking for microphone...")
        mic_list = sr.Microphone.list_microphone_names()

        if not mic_list:
            print("❌ No microphones found!")
            return False

        print(f"✅ Found {len(mic_list)} microphone(s):")
        for i, mic in enumerate(mic_list):
            print(f"   {i}: {mic}")

        # Test default microphone
        print("\n🔄 Testing default microphone access...")
        with sr.Microphone() as source:
            print("✅ Microphone access successful!")
            print("   (Audio will be calibrated when you start the app)")

        return True

    except Exception as e:
        print(f"❌ Microphone test failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Check system privacy settings for microphone access")
        print("   • Ensure a microphone is connected and enabled")
        print("   • On Windows, check 'Settings > Privacy > Microphone'")
        return False


def test_tts():
    """Test TTS (StreamElements - no API key needed)"""
    print_header("Testing Text-to-Speech")

    try:
        import requests

        print("🔄 Testing StreamElements TTS (free, no API key needed)...")

        url = "https://api.streamelements.com/kappa/v2/speech"
        params = {
            'voice': 'Brian',
            'text': 'Testing text to speech'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            print("✅ StreamElements TTS working!")
            print("   You can use TTS without any API keys!")
            return True
        else:
            print(f"⚠️  StreamElements returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False


def test_config_file():
    """Test configuration file"""
    print_header("Testing Configuration")

    config_file = Path('chatbot_config.json')

    if config_file.exists():
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)

            print("✅ Configuration file found and valid")
            print(f"\n📋 Current Settings:")
            print(f"   AI Name: {config.get('ai_name', 'Not set')}")
            print(f"   LLM Model: {config.get('llm_model', 'Not set')}")
            print(f"   TTS Service: {config.get('tts_service', 'Not set')}")
            return True

        except Exception as e:
            print(f"❌ Configuration file error: {e}")
            return False
    else:
        print("⚠️  No configuration file found")
        print("   A default config will be created when you run the app")
        return True


def run_all_tests():
    """Run all system tests"""
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║       🧪 AI Chatbot System - System Tester                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    results = {
        'Packages': test_imports(),
        'API Keys': test_api_keys(),
        'Configuration': test_config_file(),
        'Microphone': test_microphone(),
        'TTS': test_tts()
    }

    # Only test OpenAI if API key is configured
    if results['API Keys']:
        results['OpenAI Connection'] = test_openai_connection()

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n📊 Results: {passed}/{total} tests passed\n")

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    # Recommendations
    print("\n" + "=" * 60)
    print("💡 Recommendations:\n")

    if not results['Packages']:
        print("  ⚠️  Install missing packages: pip install -r requirements.txt")

    if not results.get('API Keys'):
        print("  ⚠️  Configure your OpenAI API key in .env file")
        print("     Get your key from: https://platform.openai.com/api-keys")

    if not results.get('Microphone'):
        print("  ⚠️  Fix microphone issues before using voice features")

    if all(results.values()):
        print("  ✅ All systems ready! You can start the chatbot:")
        print("     python integrated_app.py")
    else:
        print("  ⚠️  Fix the issues above before starting the chatbot")

    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()