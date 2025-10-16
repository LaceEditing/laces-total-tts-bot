"""
Auto-updater module for GitHub releases
Checks for updates and handles the update process
"""

import os
import sys
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# GitHub repo info - UPDATE THESE
GITHUB_OWNER = "LaceEditing"  # Replace with your GitHub username
GITHUB_REPO = "tts-bot-releases"  # Replace with your repo name
CURRENT_VERSION = "1.2.0"  # Matches VERSION_NUMBER in integrated_app.py


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

        # Look for .zip or .exe file
        for asset in data['assets']:
            if asset['name'].endswith('.zip') or asset['name'].endswith('.exe'):
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
            is_zip = download_url.endswith('.zip')
            temp_file = os.path.join(temp_dir, 'chatbot_update.zip' if is_zip else 'chatbot_update.exe')

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

            # If it's a zip, extract the exe
            if is_zip:
                extract_dir = os.path.join(temp_dir, 'chatbot_update_extracted')
                os.makedirs(extract_dir, exist_ok=True)

                with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)

                # Find the main exe file (exclude utilities like ffmpeg)
                excluded_exes = ['ffmpeg.exe', 'ffprobe.exe', 'ffplay.exe']
                exe_candidates = []

                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.exe') and file.lower() not in [e.lower() for e in excluded_exes]:
                            full_path = os.path.join(root, file)
                            file_size = os.path.getsize(full_path)
                            exe_candidates.append((full_path, file_size))

                if not exe_candidates:
                    print("[Updater] No main exe found in zip file (only utilities found)")
                    return None

                # Use the largest exe (main app is typically much larger than utilities)
                exe_file = max(exe_candidates, key=lambda x: x[1])[0]
                print(f"[Updater] Found main exe: {os.path.basename(exe_file)} ({exe_candidates[0][1] / (1024*1024):.1f} MB)")

                return exe_file

            return temp_file

    except Exception as e:
        print(f"[Updater] Error downloading update: {e}")
        return None


def apply_update(new_exe_path):
    """Apply the update by creating a VBScript that replaces the exe"""
    try:
        current_exe = sys.executable
        exe_name = os.path.basename(current_exe)

        # Create VBScript in temp directory
        vbs_script = os.path.join(tempfile.gettempdir(), 'update_chatbot.vbs')

        # VBScript just updates the exe and notifies user
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Wait for app to close
WScript.Sleep 3000

' Kill any remaining processes
On Error Resume Next
WshShell.Run "taskkill /F /IM {exe_name} /T", 0, True
On Error Goto 0

' Wait again
WScript.Sleep 2000

' Delete old exe with retry
For i = 1 To 10
    On Error Resume Next
    FSO.DeleteFile "{current_exe}", True
    On Error Goto 0
    
    If Not FSO.FileExists("{current_exe}") Then
        Exit For
    End If
    
    WScript.Sleep 500
Next

' Wait for deletion
WScript.Sleep 1000

' Move new exe
On Error Resume Next
FSO.MoveFile "{new_exe_path}", "{current_exe}"
On Error Goto 0

' Verify it worked and show message
If FSO.FileExists("{current_exe}") Then
    MsgBox "Update complete! Please restart the application.", vbInformation + vbOKOnly, "Update Successful"
Else
    MsgBox "Update failed. Please try again or download manually.", vbCritical + vbOKOnly, "Update Failed"
End If

' Cleanup
On Error Resume Next
FSO.DeleteFile WScript.ScriptFullName, True
On Error Goto 0
'''

        with open(vbs_script, 'w') as f:
            f.write(vbs_content)

        # Run VBScript completely detached
        subprocess.Popen(
            ['wscript.exe', vbs_script],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return True

    except Exception as e:
        print(f"[Updater] Error applying update: {e}")
        return False