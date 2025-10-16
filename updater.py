"""
Auto-updater module for GitHub releases
Checks for updates and handles the update process
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# GitHub repo info
GITHUB_OWNER = "LaceEditing"
GITHUB_REPO = "tts-bot-releases"
CURRENT_VERSION = "1.3.0"


def parse_version(version_str):
    """Parse version string to tuple for comparison"""
    try:
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')
        return tuple(map(int, version_str.split('.')))
    except:
        return (0, 0, 0)


def check_for_updates():
    """Check GitHub releases for newer version"""
    try:
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
        req = Request(url, headers={'User-Agent': 'Python-App-Updater'})

        with urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())

        latest_version = data['tag_name'].lstrip('v')
        download_url = None

        # Find the .exe asset
        for asset in data['assets']:
            if asset['name'].endswith('.exe'):
                download_url = asset['browser_download_url']
                break

        if not download_url:
            return None

        current = parse_version(CURRENT_VERSION)
        latest = parse_version(latest_version)

        if latest > current:
            return {
                'version': latest_version,
                'url': download_url,
                'notes': data.get('body', 'No release notes available.')
            }

        return None

    except (URLError, json.JSONDecodeError, KeyError) as e:
        print(f"[Updater] Error checking for updates: {e}")
        return None


def download_update(download_url, progress_callback=None):
    """Download the new version"""
    try:
        req = Request(download_url, headers={'User-Agent': 'Python-App-Updater'})

        with urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('Content-Length', 0))

            # Create temp file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, 'chatbot_update.exe')

            downloaded = 0
            chunk_size = 8192

            with open(temp_file, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break

                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)

            return temp_file

    except Exception as e:
        print(f"[Updater] Error downloading update: {e}")
        return None


def apply_update(new_exe_path):
    """Apply the update by creating a batch script that replaces the exe"""
    try:
        current_exe = sys.executable

        # Create batch script in temp directory
        batch_script = os.path.join(tempfile.gettempdir(), 'update_chatbot.bat')

        batch_content = f"""@echo off
echo Updating chatbot...
timeout /t 2 /nobreak > nul
:retry
del "{current_exe}" 2>nul
if exist "{current_exe}" (
    timeout /t 1 /nobreak > nul
    goto retry
)
move /Y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo Update failed!
    pause
    exit /b 1
)
start "" "{current_exe}"
del "%~f0"
"""

        with open(batch_script, 'w') as f:
            f.write(batch_content)

        # Run batch script and exit current app
        subprocess.Popen(['cmd', '/c', batch_script],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        return True

    except Exception as e:
        print(f"[Updater] Error applying update: {e}")
        return False