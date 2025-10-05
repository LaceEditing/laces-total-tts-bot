"""
Setup Script for AI Chatbot System
Easy configuration and environment setup
"""

import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file with template"""
    env_template = """# AI Chatbot System - Environment Variables
# Fill in your API keys below

# OpenAI API Key (Required)
# Get it from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your-openai-api-key-here

# ElevenLabs API Key (Optional - for high-quality TTS)
# Get it from: https://elevenlabs.io/
ELEVENLABS_API_KEY=your-elevenlabs-key-here

# Azure TTS (Optional)
# Get it from: https://portal.azure.com/
AZURE_TTS_KEY=your-azure-key-here
AZURE_TTS_REGION=eastus

# Twitch OAuth Token (Optional - for Twitch chat integration)
# Get it from: https://twitchapps.com/tmi/
# Format: oauth:yourtokenhere
TWITCH_OAUTH_TOKEN=oauth:your-token-here
"""

    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/n): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return

    with open(env_file, 'w') as f:
        f.write(env_template)

    print("✅ Created .env file! Please edit it with your API keys.")


def create_directories():
    """Create necessary directories"""
    dirs = ['audio_cache', 'images', 'logs']

    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✅ Created directory: {dir_name}/")


def create_example_config():
    """Create example configuration"""
    import json

    example_config = {
        "ai_name": "Buddy",
        "user_name": "User",
        "personality": "You are Buddy, a friendly and enthusiastic AI assistant. You love helping people and have a great sense of humor. Keep your responses concise and engaging.",
        "llm_model": "gpt-4o",
        "tts_service": "streamelements",
        "elevenlabs_voice": "rachel",
        "twitch_enabled": False,
        "twitch_channel": "",
        "mic_enabled": True,
        "screen_enabled": False,
        "hotkey_toggle": "F4",
        "hotkey_stop": "P",
        "speaking_image": "",
        "idle_image": ""
    }

    config_file = Path('chatbot_config.json')
    if not config_file.exists():
        with open(config_file, 'w') as f:
            json.dump(example_config, f, indent=4)
        print("✅ Created example chatbot_config.json")
    else:
        print("ℹ️  chatbot_config.json already exists")


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Error: Python 3.9 or higher is required!")
        print(f"   You are using Python {sys.version_info.major}.{sys.version_info.minor}")
        print("   Please upgrade Python from: https://www.python.org/downloads/")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
        return True


def install_dependencies():
    """Install required packages"""
    print("\n📦 Installing dependencies...")
    print("This may take a few minutes...\n")

    import subprocess

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n✅ All dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Error installing dependencies!")
        print("Please try manually: pip install -r requirements.txt")
        return False


def setup_guide():
    """Display setup guide"""
    guide = """
╔══════════════════════════════════════════════════════════════╗
║          🎙️  AI Chatbot System - Setup Complete!            ║
╚══════════════════════════════════════════════════════════════╝

📝 Next Steps:

1️⃣  Edit the .env file with your API keys:
   • OPENAI_API_KEY (Required for GPT models)
   • ELEVENLABS_API_KEY (Optional, for premium TTS)
   • Other keys as needed

2️⃣  Get your OpenAI API key:
   → Visit: https://platform.openai.com/api-keys
   → Add $5 credit to access GPT-4o

3️⃣  (Optional) Get ElevenLabs key for best voice quality:
   → Visit: https://elevenlabs.io/
   → Free tier available!

4️⃣  Run the application:
   → python integrated_app.py

🎯 Quick Start Tips:

• StreamElements TTS works without API keys (free!)
• Press F4 to activate microphone input
• Customize your AI personality in the Personality tab
• Test with text chat first before using voice

📚 Full documentation in README.md

🐛 Troubleshooting:
• PyAudio issues? See README.md for wheel downloads
• Microphone not working? Check system privacy settings
• Need help? Check the README or open an issue

Good luck and have fun! 🚀
"""
    print(guide)


def main():
    """Main setup process"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🎙️  AI Chatbot System - Setup Wizard                  ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # Check Python version
    if not check_python_version():
        return

    print("\n🔧 Setting up your chatbot environment...\n")

    # Create directories
    create_directories()

    # Create configuration files
    create_example_config()
    create_env_file()

    # Ask about installing dependencies
    print("\n" + "=" * 60)
    response = input("\n📦 Install Python dependencies now? (y/n): ")

    if response.lower() == 'y':
        install_dependencies()
    else:
        print("\nℹ️  Remember to run: pip install -r requirements.txt")

    # Show final guide
    print("\n" + "=" * 60)
    setup_guide()


if __name__ == '__main__':
    main()