"""Stop the VoiceStudio backend only if speak.py started it (SessionEnd hook)."""
import os
import signal
import subprocess

marker = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backend_started_by_speak")
if os.path.exists(marker):
    pid = open(marker).read().strip()
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(int(pid), signal.SIGTERM)
        except (ProcessLookupError, ValueError, PermissionError):
            pass
    os.remove(marker)
