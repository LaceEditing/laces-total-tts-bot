# 🎙️ AI Chatbot System

A comprehensive AI chatbot system inspired by DougDoug's Babagaboosh, featuring a beautiful lavender-themed GUI and extensive customization options.

![Chatbot Demo](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### 🤖 Multiple LLM Models
- GPT-4o
- GPT-4o-mini
- GPT-4-turbo
- GPT-3.5-turbo

### 🔊 Text-to-Speech Services
- **ElevenLabs** - High-quality AI voices with extensive customization
- **StreamElements** - Free TTS service (no API key required!)
- **Coqui TTS** - Open-source, runs locally
- **Azure TTS** - Microsoft's neural voices

### 📥 Multiple Input Methods
- **🎤 Microphone** - Voice conversation via speech recognition
- **💬 Twitch Chat** - Read and respond to Twitch messages
- **🖥️ Screen Capture** - Vision-enabled responses using GPT-4o

### 🎨 User Interface
- Beautiful lavender-themed GUI
- Easy-to-use tabs for different settings
- Real-time chat display
- Hotkey support for hands-free operation
- Avatar images with speaking/idle states

### ⚙️ Customization
- Custom AI personality and system prompts
- Configurable AI and user names
- Memory and conversation context
- Adjustable response settings
- Image overlay for streaming

## 📋 Prerequisites

- Python 3.9 or higher
- Windows, macOS, or Linux
- Microphone (for voice input)
- API keys for desired services

## 🚀 Installation

### 1. Clone or Download This Project

```bash
git clone https://github.com/yourusername/ai-chatbot-system.git
cd ai-chatbot-system
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note for Windows users:** If PyAudio fails to install, download the appropriate wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install it:

```bash
pip install PyAudio‑0.2.14‑cp39‑cp39‑win_amd64.whl
```

### 3. Set Up API Keys

You'll need to set up environment variables for the services you want to use.

#### Windows (Command Prompt):
```cmd
setx OPENAI_API_KEY "your-openai-key-here"
setx ELEVENLABS_API_KEY "your-elevenlabs-key-here"
setx AZURE_TTS_KEY "your-azure-key-here"
setx AZURE_TTS_REGION "eastus"
setx TWITCH_OAUTH_TOKEN "oauth:your-twitch-token"
```

#### macOS/Linux (bash):
```bash
export OPENAI_API_KEY="your-openai-key-here"
export ELEVENLABS_API_KEY="your-elevenlabs-key-here"
export AZURE_TTS_KEY="your-azure-key-here"
export AZURE_TTS_REGION="eastus"
export TWITCH_OAUTH_TOKEN="oauth:your-twitch-token"
```

**Alternatively**, create a `.env` file in the project directory:

```env
OPENAI_API_KEY=your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
AZURE_TTS_KEY=your-azure-key-here
AZURE_TTS_REGION=eastus
TWITCH_OAUTH_TOKEN=oauth:your-twitch-token
```

## 🔑 Getting API Keys

### OpenAI
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create an account and add $5 minimum credit
3. Generate an API key

### ElevenLabs (Optional)
1. Sign up at [ElevenLabs](https://elevenlabs.io/)
2. Go to Profile → API Keys
3. Generate an API key
4. Find voice IDs in the Voice Library

### StreamElements (Free, No Key Needed!)
- StreamElements TTS works without any API key
- Just select it in the TTS settings

### Azure TTS (Optional)
1. Create an [Azure account](https://azure.microsoft.com/)
2. Create a Speech Services resource
3. Get your key and region

### Twitch (Optional)
1. Go to [Twitch Chat OAuth Generator](https://twitchapps.com/tmi/)
2. Generate an OAuth token
3. Format: `oauth:yourtokenhere`

## 🎮 Usage

### Starting the Application

```bash
python integrated_app.py
```

### Basic Workflow

1. **Configure Settings**
   - Set your AI name and personality in the "Personality" tab
   - Choose your preferred LLM model in "Setup"
   - Select TTS service in "TTS" tab
   - Enable/disable input sources in "Inputs"

2. **Start the Chatbot**
   - Click the "▶️ Start" button
   - The status will change to "🟢 Running"

3. **Interact**
   - **Text Chat**: Type in the chat box and press Enter
   - **Voice**: Press F4 (or your custom hotkey) to start recording
   - **Twitch**: Messages will be processed automatically

### Hotkeys

- **F4** - Toggle microphone recording (default, customizable)
- **P** - Stop recording (customizable)

### Customizing Your AI

```
Example Personality Prompt:

You are Buddy, a cheerful and enthusiastic AI assistant who loves helping people with their projects. You have a passion for technology and gaming. You speak in a friendly, casual tone and occasionally use gaming references. You are talking to a streamer named Alex.

Keep your responses concise and engaging, suitable for a live stream environment.
```

## 📁 Project Structure

```
ai-chatbot-system/
├── integrated_app.py       # Main application with GUI
├── chatbot_engine.py       # Core chatbot logic
├── llm_manager.py          # LLM/OpenAI integration
├── tts_manager.py          # Text-to-speech handlers
├── input_handlers.py       # Input processing (mic, Twitch, screen)
├── requirements.txt        # Python dependencies
├── chatbot_config.json     # Auto-generated config file
└── audio_cache/            # Temporary audio files
```

## 🎨 Avatar Setup

1. Create two PNG images:
   - **Speaking image** - Shows when AI is talking
   - **Idle image** - Shows when AI is silent

2. Set paths in the "Controls" tab

3. Images will appear as overlay in bottom-right corner

## 🔧 Advanced Configuration

### Using Multiple TTS Voices (ElevenLabs)

Popular ElevenLabs voice IDs:
- `rachel` - Natural female voice
- `drew` - Natural male voice
- `clyde` - Friendly male voice
- `domi` - Energetic female voice

### Custom System Prompts

The system prompt defines your AI's personality. Be specific:

```
Good: "You are Sparky, an energetic robot who speaks in short, punchy sentences. You love science and making people laugh."

Bad: "You are helpful."
```

### Screen Capture with Vision

When enabled, the AI can see your screen and comment on it:

```
User: "What do you see on my screen?"
AI: "I can see you're playing Minecraft! That's a cool build you're working on."
```

## 🐛 Troubleshooting

### Microphone Not Working
- Check Windows Privacy Settings → Microphone
- Ensure your microphone is set as default device
- Test with Windows Voice Recorder

### PyAudio Installation Fails
- Download pre-built wheel for your Python version
- Use `pip install <wheel-file>`

### OpenAI API Errors
- Verify you have credits ($5+ required for GPT-4o)
- Check API key is correct
- Ensure you're using the right model name

### Twitch Not Connecting
- Verify OAuth token format: `oauth:yourtokenhere`
- Check channel name (no # symbol needed)
- Ensure caps lock is off for channel name

### ElevenLabs No Audio
- Verify API key is set correctly
- Check you have available characters in your quota
- Try using StreamElements as an alternative (no key needed)

## 🎯 Tips for Best Results

1. **Keep responses concise** - Add "Keep responses under 50 words" to your system prompt for faster, stream-friendly responses

2. **Use StreamElements for free testing** - Great for development before committing to paid services

3. **Customize hotkeys** - Choose keys that won't conflict with your games/apps

4. **Test personality prompts** - Experiment with different personalities in the Chat tab before going live

5. **Monitor token usage** - Longer conversations use more tokens; consider resetting periodically

## 🌟 Example Use Cases

### Streaming Companion
- Responds to Twitch chat
- Comments on gameplay via screen capture
- Interactive storytelling

### Voice Assistant
- Hands-free coding companion
- Study buddy with voice interaction
- Creative writing partner

### Character Roleplay
- D&D dungeon master
- Game character simulation
- Educational personas

## 📝 Credits

- Inspired by [DougDoug's Babagaboosh](https://github.com/DougDougGithub/Babagaboosh)
- Built with OpenAI, ElevenLabs, and open-source tools
- Designed for ease of use and extensibility

## 📄 License

MIT License - Feel free to use, modify, and distribute!

## 🤝 Contributing

Contributions welcome! Some ideas:
- Additional TTS services
- More input methods (Discord, YouTube chat)
- Better avatar animation
- Mobile app version

## 📧 Support

Having issues? Check the troubleshooting section or open an issue on GitHub!

---

**Enjoy your AI chatbot! 🎉**