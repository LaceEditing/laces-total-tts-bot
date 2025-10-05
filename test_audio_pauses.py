"""
Test Audio-Reactive Avatar System
Demonstrates pause detection and avatar switching
"""

import time
from pathlib import Path
import json

def test_audio_reactive_avatar():
    """Test the audio-reactive avatar with actual TTS"""
    print("=" * 70)
    print("AUDIO-REACTIVE AVATAR TEST")
    print("=" * 70)
    print()

    # Check configuration
    config_file = Path('chatbot_config.json')
    if not config_file.exists():
        print("❌ No config file found!")
        print("Please run the main app first to configure settings.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Check if images are configured
    speaking_path = config.get('speaking_image', '')
    idle_path = config.get('idle_image', '')

    if not speaking_path or not idle_path:
        print("❌ Avatar images not configured!")
        print("\n1. Go to the 'Avatar' tab in the main app")
        print("2. Select your speaking and idle images")
        print("3. Save settings and run this test again")
        return

    if not Path(speaking_path).exists() or not Path(idle_path).exists():
        print("❌ Avatar image files not found!")
        print(f"Speaking: {speaking_path}")
        print(f"Idle: {idle_path}")
        return

    print("✅ Avatar images configured")
    print(f"   Speaking: {Path(speaking_path).name}")
    print(f"   Idle: {Path(idle_path).name}")
    print()

    # Import TTS manager
    try:
        from tts_manager import TTSManager
    except ImportError:
        print("❌ Could not import tts_manager.py")
        print("Make sure you've replaced tts_manager.py with the enhanced version")
        return

    # Track avatar state
    avatar_state = {'current': 'idle'}
    switch_count = {'count': 0}

    def on_audio_start():
        """Called when audio starts"""
        print("\n🎤 [AUDIO START] → Switching to SPEAKING")
        avatar_state['current'] = 'speaking'
        switch_count['count'] += 1
        # In real app, this would update images/current_avatar.png

    def on_audio_pause():
        """Called when audio pauses"""
        print("   💤 [PAUSE] → Switching to IDLE")
        avatar_state['current'] = 'idle'
        switch_count['count'] += 1

    def on_audio_resume():
        """Called when audio resumes"""
        print("   🎤 [RESUME] → Switching to SPEAKING")
        avatar_state['current'] = 'speaking'
        switch_count['count'] += 1

    # Create TTS manager
    tts_service = config.get('tts_service', 'streamelements')
    tts_voice = config.get('elevenlabs_voice', 'Brian')

    print(f"TTS Service: {tts_service}")
    print(f"Voice: {tts_voice}")
    print()

    print("Creating TTS manager...")
    tts = TTSManager(service=tts_service, voice=tts_voice)

    # Set up callbacks
    tts.set_audio_callbacks(
        on_start=on_audio_start,
        on_pause=on_audio_pause,
        on_resume=on_audio_resume
    )

    print("✅ TTS manager ready with audio monitoring")
    print()

    # Test with a sample sentence with multiple pauses
    test_sentences = [
        "Hello! This is a test of the audio-reactive avatar system. "
        "Notice how the avatar switches to idle during pauses. "
        "Pretty cool, right? I think so!",

        "Short test. Multiple sentences. See the switches?",

        "This is a longer example with commas, periods, and other punctuation. "
        "The system detects these pauses automatically. "
        "No manual configuration needed!"
    ]

    print("=" * 70)
    print("STARTING TESTS")
    print("=" * 70)
    print()
    print("Watch the console output below to see when the avatar switches.")
    print("In the actual app, images/current_avatar.png will update in real-time!")
    print()
    print("-" * 70)

    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n[TEST {i}/{len(test_sentences)}]")
        print(f"Text: \"{sentence}\"")
        print()

        switch_count['count'] = 0

        # Speak the sentence
        tts.speak(sentence)

        print(f"\n✅ Test {i} complete - {switch_count['count']} avatar switches detected")
        print("-" * 70)

        if i < len(test_sentences):
            print("\nNext test in 2 seconds...")
            time.sleep(2)

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE!")
    print("=" * 70)
    print()
    print("What you should have seen:")
    print("  • Avatar switches to SPEAKING when audio starts")
    print("  • Avatar switches to IDLE during pauses (. , ; ? !)")
    print("  • Avatar switches back to SPEAKING when audio resumes")
    print()
    print("This creates a natural, responsive avatar that syncs with speech!")
    print()
    print("To use in the main app:")
    print("  1. Replace tts_manager.py with the enhanced version")
    print("  2. Replace chatbot_engine.py with the updated version")
    print("  3. Start the chatbot normally")
    print("  4. The avatar will now respond to actual speech pauses! ✨")
    print()

def quick_test():
    """Quick test without full configuration"""
    print("=" * 70)
    print("QUICK PAUSE DETECTION TEST")
    print("=" * 70)
    print()

    try:
        from tts_manager import TTSManager
    except ImportError:
        print("❌ Enhanced tts_manager.py not found")
        return

    print("Testing pause detection with simple text...")
    print()

    def show_pause(pause_info):
        """Display pause information"""
        pause_type = pause_info['type']
        pause_time = pause_info['time']
        pause_duration = pause_info['duration']

        if pause_type == 'sentence':
            symbol = "."
        elif pause_type == 'comma':
            symbol = ","
        else:
            symbol = "?"

        print(f"  {symbol} Pause at {pause_time:.2f}s (duration: {pause_duration:.1f}s)")

    tts = TTSManager(service='streamelements', voice='Brian')

    test_text = "Hello! This is a test. It has multiple sentences, and even commas. Cool?"

    print(f"Text: \"{test_text}\"")
    print("\nDetected pauses:")

    pauses = tts._find_text_pauses(test_text)

    for pause in pauses:
        show_pause(pause)

    print(f"\nTotal pauses detected: {len(pauses)}")
    print()
    print("In the full system, the avatar would:")
    print("  • Show SPEAKING at start")
    print(f"  • Switch to IDLE at each pause ({len(pauses)} times)")
    print("  • Switch back to SPEAKING after each pause")
    print("  • End on IDLE")
    print()

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("AUDIO-REACTIVE AVATAR TESTING SUITE")
    print("=" * 70)
    print()
    print("Choose a test:")
    print("  1. Full test with actual TTS and avatar switching")
    print("  2. Quick pause detection analysis (no audio)")
    print("  3. Both tests")
    print()

    choice = input("Enter choice (1/2/3): ").strip()
    print()

    if choice == '1':
        test_audio_reactive_avatar()
    elif choice == '2':
        quick_test()
    elif choice == '3':
        quick_test()
        print("\n" * 2)
        input("Press Enter to continue to full test...")
        print()
        test_audio_reactive_avatar()
    else:
        print("Invalid choice. Running quick test...")
        quick_test()