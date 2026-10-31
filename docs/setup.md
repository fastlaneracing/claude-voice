# Setup from scratch (new machine)

Everything needed to get Claude speaking, starting from a clean machine. Tested on Windows 11; macOS/Linux paths are handled in the scripts but untested.

## Fast path (Windows)

```
powershell -ExecutionPolicy Bypass -File setup.ps1
```

`setup.ps1` installs whatever is missing (Python and ffmpeg via winget; VoiceStudio from its official GitHub release, SHA-256 verified), launches VoiceStudio once to build its backend, then runs `install.py`. Options: `-DryRun`, `-SkipVoiceStudio`, `-SkipHooks`, `-Profile`, `-Language`, `-Speed`. You still choose a speech model and create/clone a voice in the VoiceStudio app. The sections below are the manual equivalent.

## 1. Prerequisites

| Need | Install | Check |
|---|---|---|
| Python 3.8+ (stdlib only, no pip packages) | python.org or `winget install Python.Python.3` | `python --version` |
| ffmpeg (provides `ffplay`) | `winget install Gyan.FFmpeg` (mac: `brew install ffmpeg`) | `ffplay -version` |
| Claude Code | https://claude.com/claude-code | `claude --version` |
| VoiceStudio (the TTS engine) | Download from https://github.com/debpalash/VoiceStudio/releases/latest | see step 2 |

VoiceStudio is a separate, AGPL-3.0 project by its own authors; this repo only talks to its local HTTP API and does not include it. A GPU is strongly recommended for speed.

Open a **new** terminal after installing ffmpeg so PATH updates.

## 2. Install and prepare VoiceStudio

1. Install the release and launch it once. First launch creates the backend at:
   - Windows: `%APPDATA%\VoiceStudio\runtime\project`
   - macOS: `~/Library/Application Support/VoiceStudio/runtime/project`
   - Linux: `~/.config/VoiceStudio/runtime/project`
   (If yours is elsewhere, set `VOICESTUDIO_PROJECT` to that folder.)
2. Download a speech model when the app prompts you (Models page).
3. Create a voice: clone one from a clean reference recording (and only clone voices you have the right to use), or use Voice Design. The bundled "Demo Voice" works for a first test.
4. Confirm the backend answers: `curl http://127.0.0.1:3900/health`. You can close the app afterwards; `speak.py` starts the backend on demand.

## 3. Get this repo and install the hooks

```
git clone https://github.com/fastlaneracing/claude-voice.git
cd claude-voice
python install.py
```

`install.py` checks the prerequisites, backs up `~/.claude/settings.json` to `settings.json.bak`, and adds the hooks and permissions with correct absolute paths. Re-running is safe. Options: `--profile ID`, `--language LANG`, `--speed N` (stored as env vars in settings).

Prefer to do it by hand? Merge `examples/settings.hooks.json` and replace `<REPO>` with the clone path.

## 4. Pick your voice and test

```
python scripts/speak.py --list-voices          # id, name, kind, language
python scripts/speak.py "Hello from Claude"    # uses the first non-demo voice
python install.py --profile <id> --speed 1.3   # make a choice permanent
```

If a voice's saved language differs from what you want, pass it explicitly (the default is `English`).

## 5. Use it

Start a new Claude Code session. It asks "Want voice on this session?"; answer yes and replies are spoken (a short summary, under about 60 words) while the full text is still written.

Optional: register VoiceStudio's MCP server in Claude Code (`http://localhost:3900/mcp/`) to manage voices from chat. Do not use its `generate_speech` tool for playback (see architecture).

## Uninstall

```
python install.py --uninstall
```
