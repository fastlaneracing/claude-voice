"""Install claude-voice into Claude Code: check prerequisites and merge the hooks.

Usage:
  python install.py [--profile ID] [--language LANG] [--speed N] [--settings PATH]
  python install.py --uninstall

Edits ~/.claude/settings.json (a .bak copy is written first). Safe to re-run.
"""
import argparse
import json
import os
import shutil
import sys
import urllib.request

REPO = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(REPO, "scripts").replace("\\", "/")


def ours(cmd):
    return SCRIPTS in cmd.replace("\\", "/")


def strip_ours(settings):
    hooks = settings.get("hooks", {})
    for event in list(hooks):
        hooks[event] = [g for g in hooks[event]
                        if not any(ours(h.get("command", "")) for h in g.get("hooks", []))]
        if not hooks[event]:
            del hooks[event]
    if not hooks:
        settings.pop("hooks", None)
    allow = settings.get("permissions", {}).get("allow", [])
    settings.get("permissions", {})["allow"] = [a for a in allow if not ours(a)]
    env = settings.get("env", {})
    for k in ("CLAUDE_VOICE_PROFILE", "CLAUDE_VOICE_LANGUAGE", "CLAUDE_VOICE_SPEED"):
        env.pop(k, None)
    if "env" in settings and not env:
        del settings["env"]


def check_prereqs():
    print("Prerequisites:")
    ok = True
    print(f"  python  {sys.version.split()[0]}")
    if shutil.which("ffplay"):
        print("  ffplay  found")
    else:
        ok = False
        print("  ffplay  MISSING - install ffmpeg (Windows: winget install Gyan.FFmpeg)")
    port = os.environ.get("OMNIVOICE_PORT", "3900")
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3)
        print(f"  VoiceStudio backend  running on :{port}")
    except Exception:
        print(f"  VoiceStudio backend  not running on :{port} (speak.py will try to auto-start it;"
              " install VoiceStudio and launch it once if not yet done - see docs/setup.md)")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--language")
    ap.add_argument("--speed")
    ap.add_argument("--settings", default=os.path.join(os.path.expanduser("~"), ".claude", "settings.json"))
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()

    settings = {}
    if os.path.exists(a.settings):
        with open(a.settings, encoding="utf-8") as f:
            settings = json.load(f)
        shutil.copy2(a.settings, a.settings + ".bak")
    strip_ours(settings)  # idempotent: remove old entries before re-adding

    if not a.uninstall:
        check_prereqs()
        py = f"python -I {SCRIPTS}"
        hooks = settings.setdefault("hooks", {})
        hooks.setdefault("SessionStart", []).append(
            {"hooks": [{"type": "command", "command": f"{py}/voice_session_start.py"}]})
        hooks.setdefault("SessionEnd", []).append(
            {"hooks": [{"type": "command", "command": f"{py}/stop_backend.py"}]})
        allow = settings.setdefault("permissions", {}).setdefault("allow", [])
        allow += [f"Bash({py}/speak.py *)", f"PowerShell({py}/speak.py *)"]
        env = {k: v for k, v in (("CLAUDE_VOICE_PROFILE", a.profile), ("CLAUDE_VOICE_LANGUAGE", a.language),
                                 ("CLAUDE_VOICE_SPEED", a.speed)) if v}
        if env:
            settings.setdefault("env", {}).update(env)

    os.makedirs(os.path.dirname(a.settings), exist_ok=True)
    with open(a.settings, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print(f"\n{'Removed claude-voice from' if a.uninstall else 'Installed claude-voice into'} {a.settings}")
    if not a.uninstall:
        print("Next: python scripts/speak.py --list-voices   then   python scripts/speak.py \"Hello\"")


main()
