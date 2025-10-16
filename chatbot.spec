# -*- mode: python ; coding: utf-8 -*-
"""
AI Chatbot System - PyInstaller Build Specification
WORKING BUILD - Conservative excludes that won't break dependencies
Target size: ~300-500MB
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# ========================================
# DATA FILES
# ========================================
datas = []

# Fonts
if os.path.exists('fonts'):
    datas.append(('fonts', 'fonts'))
    print("Including fonts folder")

# Icon
if os.path.exists('icon.ico'):
    datas.append(('icon.ico', '.'))
    print("Including icon.ico")

# ElevenLabs data files
try:
    datas += collect_data_files('elevenlabs')
except:
    pass

# Groq data files
try:
    datas += collect_data_files('groq')
except:
    pass

# Azure Speech SDK data files
try:
    datas += collect_data_files('azure.cognitiveservices.speech')
except:
    pass

# ========================================
# BINARIES
# ========================================
binaries = []

# FFmpeg
if os.path.exists('ffmpeg.exe'):
    binaries.append(('ffmpeg.exe', '.'))
    print("Including ffmpeg.exe")

if os.path.exists('ffprobe.exe'):
    binaries.append(('ffprobe.exe', '.'))
    print("Including ffprobe.exe")

# PyAudio binary
try:
    import pyaudio
    pyaudio_path = os.path.dirname(pyaudio.__file__)
    portaudio_file = os.path.join(pyaudio_path, '_portaudio.pyd')
    if os.path.exists(portaudio_file):
        binaries.append((portaudio_file, '.'))
        print("Including PyAudio binary")
except:
    pass

# ========================================
# RUNTIME HOOKS
# ========================================
runtime_hooks = []

if os.path.exists('pyi_rth_pydub.py'):
    runtime_hooks.append('pyi_rth_pydub.py')
    print("Including pydub runtime hook")

# ========================================
# HIDDEN IMPORTS
# ========================================
hiddenimports = [
    # Core
    'pkg_resources',
    
    # GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.colorchooser',
    
    # OpenAI
    'openai',
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    
    # Groq + ALL DEPENDENCIES
    'groq',
    *collect_submodules('groq'),
    'httpx',
    'httpx._client',
    'httpx._config',
    'httpx._models',
    'httpx._types',
    'httpx._transports',
    'httpx._exceptions',
    'pydantic',
    'pydantic_core',
    'typing_extensions',
    'anyio',
    'sniffio',
    'h11',
    'certifi',
    'distro',
    
    # ElevenLabs
    'elevenlabs',
    'elevenlabs.client',
    'elevenlabs.core',
    *collect_submodules('elevenlabs'),
    
    # Azure TTS
    'azure',
    'azure.cognitiveservices',
    'azure.cognitiveservices.speech',
    
    # Audio
    'pygame',
    'pygame.mixer',
    'speech_recognition',
    'pyaudio',
    'pydub',
    'pydub.utils',
    
    # Numpy (minimal)
    'numpy',
    'numpy.core._multiarray_umath',
    
    # Scipy (only what we use)
    'scipy.io',
    'scipy.io.wavfile',
    
    # Image
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageGrab',
    
    # Utilities
    'keyboard',
    'requests',
    'dotenv',
]

# ========================================
# EXCLUDES (only safe exclusions)
# ========================================
excludes = [
    # Unused TTS services
    'TTS',
    'piper_tts',
    'gtts',
    
    # Heavy ML frameworks
    'torch',
    'tensorflow',
    'keras',
    'transformers',
    'onnxruntime',
    
    # Data science (not needed)
    'pandas',
    'sklearn',
    'matplotlib',
    
    # Computer vision
    'cv2',
    'opencv',
    
    # GUI frameworks we don't use
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'wx',
    
    # Web frameworks
    'flask',
    'django',
    'fastapi',
    
    # Testing
    'pytest',
    'unittest.mock',
    '_pytest',
    
    # Development tools
    'IPython',
    'notebook',
    'jupyter',
]

# ========================================
# ANALYSIS
# ========================================
a = Analysis(
    ['integrated_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LacesAIChatbot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'python313.dll',
        'python3.dll',
        'ffmpeg.exe',
        'ffprobe.exe',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

print("\n" + "=" * 60)
print("BUILD SUMMARY")
print("=" * 60)
print(f"Fonts: {'' if os.path.exists('fonts') else ''}")
print(f"Icon: {'' if os.path.exists('icon.ico') else ''}")
print(f"FFmpeg: {'' if os.path.exists('ffmpeg.exe') else ''}")
print("\nExpected size: ~300-500MB")
print("=" * 60 + "\n")