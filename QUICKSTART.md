# ⚡ Quick Start Guide - 5 Minutes to Your First AI Chatbot!

This guide will get you up and running as fast as possible.

## 🎯 Absolute Beginner Path (Recommended)

### Step 1: Install Python (2 minutes)

1. Download Python 3.9+ from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Restart your computer after installation

### Step 2: Setup the Chatbot (2 minutes)

1. Download/clone this project to a folder
2. Open **Command Prompt** (Windows) or **Terminal** (Mac/Linux)
3. Navigate to the project folder:
   ```bash
   cd path/to/ai-chatbot-system
   ```

4. Run the setup script:
   ```bash
   python setup.py
   ```

5. Press `y` when asked to install dependencies

### Step 3: Get Your OpenAI API Key (1 minute)

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 4: Configure Your API Key (30 seconds)

1. Open the `.env` file in the project folder with Notepad
2. Replace `your-openai-api-key-here` with your actual key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. Save and close

### Step 5: Start Chatting! (30 seconds)

```bash
python integrated_app.py
```

1. Click the **"▶️ Start"** button
2. Type a message in the chat box
3. Press Enter - your AI will respond!

---

## 🚀 Quick Feature Tests

Once you're running, try these features:

### Test Voice Input
1. Make sure you're on the "💬 Chat" tab
2. Click the **"🎤 Listen"** button
3. Speak into your microphone
4. Wait for the transcription and AI response

### Test Text-to-Speech
- Your AI's responses will be spoken automatically
- By default, it uses **StreamElements** (free, no API key needed!)
- The voice will read the response aloud

### Customize Your AI
1. Go to **"🎭 Personality"** tab
2. Try this example personality:
   ```
   You are a friendly gaming companion named Nova. You're enthusiastic about video games and love helping gamers. Keep responses short and fun, using gaming references when appropriate.
   ```
3. Click **"💾 Save Personality"**
4. Restart the chatbot to apply changes

---

## 💰 Cost Information

### OpenAI Pricing (as of 2024)
- **GPT-4o:** ~$0.005 per chat message (very affordable!)
- **GPT-3.5-turbo:** ~$0.0005 per message (even cheaper!)
- Minimum credit: $5 (lasts a LONG time for personal use)

### Free Options
- **StreamElements TTS:** Completely free, no API key needed
- **Google Speech Recognition:** Free for mic input
- **Twitch Integration:** Free

### Optional Premium
- **ElevenLabs TTS:** Free tier available, or $5/month for premium voices
- **Azure TTS:** Pay-as-you-go pricing

---

## 🎮 Streamer Quick Setup

Perfect for Twitch/YouTube streamers:

### 1. Enable Twitch Chat
1. Get OAuth token: [https://twitchapps.com/tmi/](https://twitchapps.com/tmi/)
2. Add to `.env` file:
   ```
   TWITCH_OAUTH_TOKEN=oauth:your-token-here
   ```
3. In app, go to **"🎤 Inputs"** tab
4. Check "💬 Twitch Chat"
5. Enter your channel name

### 2. Add Avatar Images
1. Create two PNG images:
   - `speaking.png` - AI is talking (open mouth)
   - `idle.png` - AI is silent (closed mouth)
2. Go to **"🎮 Controls"** tab
3. Set the file paths
4. Images will appear on screen while streaming!

### 3. Setup OBS (Optional)
- Add the image files as a "Browser Source" or "Image"
- The images will switch automatically when the AI speaks

---

## 🔑 Essential Hotkeys

| Key | Action |
|-----|--------|
| **F4** | Toggle microphone recording (customizable) |
| **P** | Stop recording (customizable) |
| **Enter** | Send text message in chat |

Change these in the **"🎮 Controls"** tab!

---

## 🐛 Common First-Time Issues

### "OpenAI API Error"
- **Solution:** Make sure you added at least $5 credit to OpenAI
- Check your API key is correct in `.env` file

### "Microphone Not Working"
- **Windows:** Settings → Privacy → Microphone → Allow apps
- **Mac:** System Preferences → Security & Privacy → Microphone
- Test with Voice Recorder first

### "PyAudio Installation Failed"
- **Windows:** Download wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Install: `pip install PyAudio‑0.2.14‑cp39‑cp39‑win_amd64.whl`

### "ModuleNotFoundError"
- Run: `pip install -r requirements.txt`
- Make sure you're in the project folder

### "No Audio Output"
- Check your system volume
- Try StreamElements first (most reliable)
- For ElevenLabs, verify API key is correct

---

## 📝 First Conversation Ideas

Try these to test your chatbot:

**General Chat:**
```
You: "Hey, introduce yourself!"
You: "What can you help me with?"
You: "Tell me a fun fact"
```

**For Gamers:**
```
You: "What game should I play today?"
You: "Give me tips for Minecraft"
You: "Roast my gaming skills"
```

**For Streamers:**
```
You: "Help me come up with stream ideas"
You: "What should I name my channel?"
You: "Create a raid message"
```

---

## 🎨 Personality Templates

Copy these into the **Personality** tab:

### Gaming Buddy
```
You are Pixel, an energetic gaming AI who loves video games. You speak casually with gaming slang and emojis. Keep responses under 50 words. You're talking to a streamer and want to keep chat engaged and entertained.
```

### Study Companion
```
You are Study Buddy, a patient and encouraging AI tutor. You explain concepts clearly, break down complex topics, and celebrate learning progress. Keep responses concise and educational.
```

### Creative Partner
```
You are Muse, a creative AI who loves storytelling and art. You're imaginative, inspiring, and always ready to brainstorm. You speak poetically sometimes and encourage creative thinking.
```

### Chill Friend
```
You are Chill, a laid-back AI friend who's just here to hang out. You keep things casual, use humor, and are always supportive. Perfect for relaxed conversations and good vibes.
```

---

## 📚 Next Steps

Once you're comfortable with the basics:

1. **Read the Full README** - Learn about all features
2. **Experiment with Models** - Try GPT-4o vs GPT-3.5-turbo
3. **Try Different TTS Services** - Compare voice quality
4. **Enable Screen Capture** - Let AI see and comment on your screen
5. **Customize Hotkeys** - Make them comfortable for your workflow

---

## 🆘 Need Help?

1. Run the test script: `python test_system.py`
2. Check the **Troubleshooting** section in README.md
3. Review error messages carefully
4. Open an issue on GitHub with details

---

## 🎉 You're Ready!

You now have a fully functional AI chatbot system! 

**Start with simple text chat, then gradually enable more features as you get comfortable.**

Have fun! 🚀