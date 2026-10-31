"""Stream VoiceStudio TTS straight to the speakers (no file, no media player).

Usage:
  python speak.py "text" [profile_id] [language] [speed]
  python speak.py --list-voices

Needs the VoiceStudio backend (auto-started if installed) and ffplay (ffmpeg) on PATH.

Environment (all optional):
  CLAUDE_VOICE_PROFILE   default voice profile id (else: first non-demo profile)
  CLAUDE_VOICE_LANGUAGE  default language (default: English)
  CLAUDE_VOICE_SPEED     default speed multiplier 0.5-2.0 (default: 1.0)
  OMNIVOICE_PORT         backend port (default: 3900)
  VOICESTUDIO_PROJECT    backend project dir, if not in the default app location
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request

TOOLS = os.path.dirname(os.path.abspath(__file__))
MARKER = os.path.join(TOOLS, ".backend_started_by_speak")
IS_WIN = os.name == "nt"

port = os.environ.get("OMNIVOICE_PORT", "3900")
base = f"http://127.0.0.1:{port}"


def backend_up():
    try:
        urllib.request.urlopen(base + "/health", timeout=2)
        return True
    except Exception:
        return False


def project_dir():
    """Locate the VoiceStudio backend project directory."""
    if os.environ.get("VOICESTUDIO_PROJECT"):
        return os.environ["VOICESTUDIO_PROJECT"]
    if IS_WIN:
        root = os.environ.get("APPDATA", "")
    elif sys.platform == "darwin":
        root = os.path.expanduser("~/Library/Application Support")
    else:
        root = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(root, "VoiceStudio", "runtime", "project")


def ensure_backend():
    """Start the installed app's backend hidden if it isn't answering."""
    if backend_up():
        return
    proj = project_dir()
    py = os.path.join(proj, ".venv", "Scripts" if IS_WIN else "bin", "python.exe" if IS_WIN else "python")
    if not os.path.exists(py):
        sys.exit(
            f"VoiceStudio backend is not running on port {port} and was not found at {proj}.\n"
            "Install and launch VoiceStudio once (see docs/setup.md), or set VOICESTUDIO_PROJECT."
        )
    kwargs = {}
    if IS_WIN:
        kwargs["creationflags"] = 0x08000000 | 0x00000008 | 0x00000200  # no window, detached, new group
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        [py, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", port],
        cwd=proj, env={**os.environ, "OMNIVOICE_PORT": port},
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    with open(MARKER, "w") as f:
        f.write(str(proc.pid))
    for _ in range(90):
        if backend_up():
            return
        time.sleep(2)
    sys.exit("VoiceStudio backend did not become ready in 180s")


def get_profiles():
    with urllib.request.urlopen(base + "/profiles", timeout=30) as r:
        return json.load(r)


def list_voices():
    for p in get_profiles():
        flag = " (demo)" if p.get("is_demo") else ""
        print(f"{p['id']}\t{p.get('name', '')}\t{p.get('kind', '')}\t{p.get('language', '')}{flag}")


def default_profile():
    profiles = get_profiles()
    real = [p for p in profiles if not p.get("is_demo")]
    pick = real or profiles
    if not pick:
        sys.exit("No voice profiles found. Create or clone a voice in VoiceStudio first.")
    return pick[0]["id"]


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    ensure_backend()
    if sys.argv[1] == "--list-voices":
        return list_voices()
    if not shutil.which("ffplay"):
        sys.exit("ffplay not found on PATH. Install ffmpeg (Windows: winget install Gyan.FFmpeg).")

    text = sys.argv[1]
    profile_id = (sys.argv[2] if len(sys.argv) > 2 else None) or os.environ.get("CLAUDE_VOICE_PROFILE") or default_profile()
    language = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("CLAUDE_VOICE_LANGUAGE", "English")
    speed = sys.argv[4] if len(sys.argv) > 4 else os.environ.get("CLAUDE_VOICE_SPEED", "1.0")

    form = {"text": text, "profile_id": profile_id, "language": language, "speed": speed, "stream": "true"}
    req = urllib.request.Request(base + "/generate", urllib.parse.urlencode(form).encode())

    player = None
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            msg = json.loads(line)
            kind = msg.get("type")
            if kind == "start":
                player = subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet",
                     "-f", "s16le", "-ar", str(msg["sample_rate"]), "-ch_layout", "mono", "-i", "-"],
                    stdin=subprocess.PIPE)
            elif kind == "chunk" and player:
                player.stdin.write(base64.b64decode(msg["pcm"]))
                player.stdin.flush()
            elif kind == "error":
                sys.exit(f"stream error: {msg}")
    if player:
        player.stdin.close()
        player.wait()


main()
