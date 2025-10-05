"""
Avatar Switching Test Script
Tests the avatar system independently to verify it works
"""

import time
import shutil
import os
from pathlib import Path

def test_avatar_switching():
    """Test avatar image switching"""
    print("=" * 60)
    print("AVATAR SWITCHING TEST")
    print("=" * 60)

    # Check for configured images
    import json
    config_file = Path('chatbot_config.json')

    if not config_file.exists():
        print("❌ No config file found!")
        print("Please run the main app first to configure your images.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    speaking_path = config.get('speaking_image', '')
    idle_path = config.get('idle_image', '')

    if not speaking_path or not idle_path:
        print("❌ No images configured!")
        print("\nPlease configure your avatar images in the app:")
        print("1. Go to the 'Avatar' tab")
        print("2. Select your speaking and idle images")
        print("3. Save settings and run this test again")
        return

    speaking_path = Path(speaking_path)
    idle_path = Path(idle_path)

    if not speaking_path.exists():
        print(f"❌ Speaking image not found: {speaking_path}")
        return

    if not idle_path.exists():
        print(f"❌ Idle image not found: {idle_path}")
        return

    print(f"✅ Found speaking image: {speaking_path.name}")
    print(f"✅ Found idle image: {idle_path.name}")
    print()

    # Create images folder
    images_folder = Path('images')
    images_folder.mkdir(exist_ok=True)
    output_path = images_folder / 'current_avatar.png'

    print("Testing avatar switching...")
    print("Watch the 'images/current_avatar.png' file")
    print("(Open it in an image viewer or add to OBS)")
    print()

    for cycle in range(3):
        print(f"\n--- Cycle {cycle + 1}/3 ---")

        # Switch to speaking
        print("Switching to SPEAKING... ", end='', flush=True)
        if output_path.exists():
            output_path.unlink()
        time.sleep(0.05)
        shutil.copy2(speaking_path, output_path)
        os.utime(output_path, None)
        print("✅")
        time.sleep(2)

        # Switch to idle
        print("Switching to IDLE... ", end='', flush=True)
        if output_path.exists():
            output_path.unlink()
        time.sleep(0.05)
        shutil.copy2(idle_path, output_path)
        os.utime(output_path, None)
        print("✅")
        time.sleep(2)

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print("\nDid the image switch correctly?")
    print("If YES: Your avatar system is working! ✅")
    print("If NO: Check these things:")
    print("  • Make sure you're viewing images/current_avatar.png")
    print("  • Try refreshing your image viewer")
    print("  • In OBS, check 'Unload image when not showing' is enabled")
    print()

def rapid_animation_test():
    """Test rapid switching for animation effect"""
    import json
    import random

    config_file = Path('chatbot_config.json')
    if not config_file.exists():
        print("❌ No config file found!")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    speaking_path = Path(config.get('speaking_image', ''))
    idle_path = Path(config.get('idle_image', ''))

    if not speaking_path.exists() or not idle_path.exists():
        print("❌ Images not configured!")
        return

    images_folder = Path('images')
    images_folder.mkdir(exist_ok=True)
    output_path = images_folder / 'current_avatar.png'

    print("\n" + "=" * 60)
    print("RAPID ANIMATION TEST")
    print("=" * 60)
    print("\nThis simulates audio-reactive mouth movement")
    print("Watch the avatar for 10 seconds...\n")

    start_time = time.time()
    while time.time() - start_time < 10:
        # Simulate speaking pattern
        if random.random() < 0.7:
            # Speaking (70% of time)
            if output_path.exists():
                output_path.unlink()
            shutil.copy2(speaking_path, output_path)
            os.utime(output_path, None)
            time.sleep(random.uniform(0.1, 0.3))
        else:
            # Brief idle (30% of time)
            if output_path.exists():
                output_path.unlink()
            shutil.copy2(idle_path, output_path)
            os.utime(output_path, None)
            time.sleep(random.uniform(0.05, 0.15))

    # End on idle
    if output_path.exists():
        output_path.unlink()
    shutil.copy2(idle_path, output_path)
    os.utime(output_path, None)

    print("Animation test complete!")
    print("Did it look like the avatar was talking? ✅")
    print()

if __name__ == '__main__':
    print("\nAVATAR SYSTEM TESTER")
    print("=" * 60)
    print("\nOptions:")
    print("1. Basic switching test (slow, easy to verify)")
    print("2. Rapid animation test (simulates talking)")
    print("3. Both tests")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        test_avatar_switching()
    elif choice == '2':
        rapid_animation_test()
    elif choice == '3':
        test_avatar_switching()
        rapid_animation_test()
    else:
        print("Invalid choice. Running basic test...")
        test_avatar_switching()