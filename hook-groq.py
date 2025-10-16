# hook-groq.py
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hiddenimports = collect_all('groq')
datas += copy_metadata('groq')
datas += copy_metadata('httpx')

# Explicitly add groq.types to avoid conflicts
hiddenimports += ['groq.types', 'groq.types.model']