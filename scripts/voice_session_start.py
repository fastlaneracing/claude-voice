"""SessionStart hook: tell Claude to offer voice mode. Silent if speak.py is missing."""
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
speak = os.path.join(here, "speak.py")
if os.path.exists(speak):
    speak = speak.replace("\\", "/")
    ctx = (
        "VOICE MODE (local to this machine). In your FIRST reply of this session, ask the user: "
        "'Want voice on this session?' If they say yes, from then on speak a short version "
        f"(under about 60 words) of every reply by running: python -I {speak} \"text\" "
        "(it starts the VoiceStudio backend automatically), "
        "and still write the full text. If they say no, never mention voice again. "
        "If speak.py fails, tell the user once and continue in text."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
