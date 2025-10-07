
import os
import sys

# Ensure pydub can find ffmpeg in the PyInstaller bundle
if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    bundle_dir = sys._MEIPASS
    
    ffmpeg_path = os.path.join(bundle_dir, 'ffmpeg.exe')
    ffprobe_path = os.path.join(bundle_dir, 'ffprobe.exe')
    
    # Set environment variables for pydub
    if os.path.exists(ffmpeg_path):
        os.environ['FFMPEG_BINARY'] = ffmpeg_path
        print(f"[Runtime Hook]  Found bundled ffmpeg: {ffmpeg_path}")
    else:
        print(f"[Runtime Hook] ffmpeg.exe not found in bundle!")
    
    if os.path.exists(ffprobe_path):
        os.environ['FFPROBE_BINARY'] = ffprobe_path
        print(f"[Runtime Hook] Found bundled ffprobe: {ffprobe_path}")
    else:
        print(f"[Runtime Hook]  ffprobe.exe not found in bundle!")
else:
    # Running in development mode
    print("[Runtime Hook] Running in development mode (not bundled)")
