# -*- mode: python ; coding: utf-8 -*-
"""
AI Chatbot System - PyInstaller Build Specification
OPTIMIZED BUILD - Excludes unnecessary ML libraries
Target size: ~400-600MB (includes FFmpeg)
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# ========================================
# DATA FILES
# ========================================
datas = []

# Fonts (CRITICAL for UI)
if os.path.exists('fonts'):
    datas.append(('fonts', 'fonts'))
    font_files = [
        'fonts/BubblegumSans-Regular.ttf',
        'fonts/Quicksand-Regular.ttf',
        'fonts/Quicksand-Medium.ttf',
        'fonts/Quicksand-Bold.ttf',
    ]
    for font_file in font_files:
        if os.path.exists(font_file):
            datas.append((font_file, 'fonts'))
    print("✅ Including fonts folder in build")
else:
    print("⚠️ WARNING: fonts folder not found - custom fonts will not work!")

# Icon
if os.path.exists('icon.ico'):
    datas.append(('icon.ico', '.'))
    print("✅ Including icon.ico in build")
else:
    print("⚠️ WARNING: icon.ico not found")

# Config templates
if os.path.exists('personality_examples.json'):
    datas.append(('personality_examples.json', '.'))

# ElevenLabs data files
try:
    datas += collect_data_files('elevenlabs')
except Exception:
    pass

# Azure Speech SDK data files (if using Azure TTS)
try:
    datas += collect_data_files('azure.cognitiveservices.speech')
except Exception:
    pass

# Piper TTS data files (may include model + resources if the package ships them)
# Note: Piper often requires external model files or a runtime; if you keep models outside
# the package, add them explicitly to `datas` (e.g. ('piper_models/', 'piper_models'))
try:
    datas += collect_data_files('piper_tts')
except Exception:
    pass

# gTTS data files (if any)
try:
    datas += collect_data_files('gtts')
except Exception:
    pass

# python-dotenv (module data if applicable)
try:
    datas += collect_data_files('python_dotenv')
except Exception:
    # fallback: many installs don't need data files
    pass

# ========================================
# BINARIES (including FFmpeg)
# ========================================
binaries = []

# FFmpeg executables (CRITICAL for audio sensitivity meter)
if os.path.exists('ffmpeg.exe'):
    binaries.append(('ffmpeg.exe', '.'))
    print("✅ Including ffmpeg.exe in build (~70-90MB)")
else:
    print("❌ WARNING: ffmpeg.exe not found!")
    print("   Audio sensitivity meter will NOT work with MP3 files (ElevenLabs/StreamElements)")
    print("   Download from: https://www.gyan.dev/ffmpeg/builds/")

if os.path.exists('ffprobe.exe'):
    binaries.append(('ffprobe.exe', '.'))
    print("✅ Including ffprobe.exe in build (~70-90MB)")
else:
    print("❌ WARNING: ffprobe.exe not found!")
    print("   Download from: https://www.gyan.dev/ffmpeg/builds/")

# PyAudio binary
try:
    import pyaudio
    pyaudio_path = os.path.dirname(pyaudio.__file__)
    portaudio_file = os.path.join(pyaudio_path, '_portaudio.pyd')
    if os.path.exists(portaudio_file):
        binaries.append((portaudio_file, '.'))
        print("✅ Including PyAudio binary")
except Exception:
    pass

# ========================================
# RUNTIME HOOKS
# ========================================
runtime_hooks = []

# pydub runtime hook (sets up FFmpeg paths)
if os.path.exists('pyi_rth_pydub.py'):
    runtime_hooks.append('pyi_rth_pydub.py')
    print("✅ Including pydub runtime hook (connects FFmpeg to pydub)")
else:
    print("⚠️ WARNING: pyi_rth_pydub.py not found - audio analysis may fail!")

# ========================================
# HIDDEN IMPORTS (only what you need)
# ========================================
hiddenimports = [
    'pkg_resources',
    'setuptools._vendor.jaraco.text',
    'setuptools._vendor.jaraco.functools',
    'setuptools._vendor.jaraco.context',
    'setuptools._vendor.more_itertools',
    
    # GUI
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    
    # OpenAI
    'openai',
    'tiktoken',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    'tiktoken._educational',
    
    # ElevenLabs TTS
    'elevenlabs',
    'elevenlabs.client',
    'elevenlabs.conversational_ai.conversation',
    'elevenlabs.conversational_ai.default_audio_interface',
    
    # Azure TTS (comment out if not using)
    'azure',
    'azure.cognitiveservices',
    'azure.cognitiveservices.speech',
    
    # Audio processing
    'pygame',
    'pygame.mixer',
    'speech_recognition',   # package name is speech_recognition
    'pyaudio',              # ensure PyAudio is found at runtime
    'pydub',
    'pydub.utils',
    'pydub.playback',
    
    # gTTS (Google TTS)
    'gtts',
    
    # Piper TTS (explicitly include)
    'piper_tts',
    
    # Image processing
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageGrab',
    
    # Audio analysis for avatar
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'scipy',
    'scipy.io',
    'scipy.io.wavfile',
    
    # Utilities
    'keyboard',
    'requests',
    'json',
    'pathlib',
    'threading',
    'queue',
    'socket',
    'base64',
    'io',
    'time',
    'os',
    'sys',
    'dotenv',
    
    # Collect ElevenLabs/tiktoken/piper submodules (ensure dynamic imports are bundled)
    *collect_submodules('elevenlabs'),
    *collect_submodules('tiktoken'),
    *collect_submodules('piper_tts'),
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
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,  # Added runtime hooks here
    excludes=[
        # ============================================
        # MACHINE LEARNING (MASSIVE - 2GB+)
        # ============================================
        'torch',
        'torch.nn',
        'torch.optim',
        'torch.distributed',
        'torch.cuda',
        'torch.autograd',
        'torch.jit',
        'torch.onnx',
        'torchvision',
        'torchaudio',
        'tensorflow',
        'tensorflow.python',
        'keras',
        'transformers',
        'huggingface_hub',
        'timm',
        'onnxruntime',
        'onnx',
        
        # ============================================
        # DATA SCIENCE (500MB+)
        # ============================================
        'sklearn',
        'scikit-learn',
        'pandas',
        'pyarrow',
        'dask',
        
        # ============================================
        # COMPUTER VISION (500MB+)
        # ============================================
        'cv2',
        'opencv',
        'imageio',
        'moviepy',
        'av',
        'skimage',
        
        # ============================================
        # VIDEO/STREAMING
        # ============================================
        'yt_dlp',
        'decord',
        'librosa',
        
        # ============================================
        # JIT COMPILERS (200MB+)
        # ============================================
        'numba',
        'llvmlite',
        
        # ============================================
        # COQUI TTS (requires torch - exclude it)
        # If you need Coqui, remove it from excludes
        # ============================================
        'TTS',
        'TTS.api',
        'TTS.utils',
        
        # ============================================
        # SCIPY MODULES (keep only io.wavfile)
        # ============================================
        'scipy.stats',
        'scipy.optimize',
        'scipy.linalg',
        'scipy.sparse',
        'scipy.ndimage',
        # 'scipy.signal',  # May be needed for audio - test without first
        'scipy.integrate',
        'scipy.interpolate',
        'scipy.fft',
        'scipy.special',
        'scipy.spatial',
        
        # ============================================
        # ML FRAMEWORKS
        # ============================================
        'lightning',
        'pytorch_lightning',
        'hydra',
        
        # ============================================
        # GUI FRAMEWORKS (not needed)
        # ============================================
        'matplotlib',
        'matplotlib.pyplot',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        'kivy',
        
        # ============================================
        # WEB FRAMEWORKS
        # ============================================
        'flask',
        'django',
        'fastapi',
        'uvicorn',
        
        # ============================================
        # TESTING
        # ============================================
        'pytest',
        'unittest',
        'test',
        'tests',
        'testing',
        '_pytest',
        
        # ============================================
        # DOCUMENTATION
        # ============================================
        'sphinx',
        'docutils',
        
        # ============================================
        # NUMPY (keep core, exclude extras)
        # ============================================
        'numpy.f2py',
        'numpy.testing',
        'numpy.distutils',
        
        # ============================================
        # OTHER HEAVY STUFF
        # ============================================
        'PIL.ImageQt',
        'lib2to3',
        'xmlrpc',
        'pydoc',
        'IPython',
        'notebook',
        'jupyter',
    ],
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
    upx=True,  # Compress with UPX
    upx_exclude=[
        'vcruntime140.dll',
        'python313.dll',
        'python3.dll',
        'ffmpeg.exe',      # Don't compress FFmpeg (can cause issues)
        'ffprobe.exe',     # Don't compress FFprobe (can cause issues)
    ],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version_file=None,
    uac_admin=False,
    uac_uiaccess=False,
)

# ========================================
# BUILD SUMMARY
# ========================================
print("\n" + "=" * 60)
print("BUILD CONFIGURATION SUMMARY")
print("=" * 60)
print(f"Fonts included: {'✅' if os.path.exists('fonts') else '❌'}")
print(f"Icon included: {'✅' if os.path.exists('icon.ico') else '❌'}")
print(f"FFmpeg included: {'✅' if os.path.exists('ffmpeg.exe') else '❌'}")
print(f"FFprobe included: {'✅' if os.path.exists('ffprobe.exe') else '❌'}")
print(f"Runtime hook included: {'✅' if os.path.exists('pyi_rth_pydub.py') else '❌'}")
print("\nExpected build size: ~400-600MB (with FFmpeg)")
print("Audio sensitivity meter: " + ("✅ WILL WORK" if os.path.exists('ffmpeg.exe') else "❌ WON'T WORK"))
print("=" * 60 + "\n")
