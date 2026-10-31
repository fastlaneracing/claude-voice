# claude-voice

Give Claude Code a spoken voice. Replies are synthesized by a local
[VoiceStudio](https://github.com/debpalash/VoiceStudio) backend (voice cloning / TTS) and streamed
straight to the speakers through `ffplay`. No audio file is written and no media player opens.
Python standard library only; nothing to `pip install`.

## How it works

```
Claude Code --runs--> scripts/speak.py --POST /generate (stream=true)--> VoiceStudio backend :3900
                                                                              | NDJSON: start / chunk (base64 PCM) / done
                      ffplay  <-- raw s16le PCM pipe -------------------------+
```

Claude Code hooks make it automatic:

- **SessionStart** -> `voice_session_start.py` tells Claude to ask "Want voice on this session?" and, if yes, speak a short summary of each reply.
- **SessionEnd** -> `stop_backend.py` stops the backend, but only if `speak.py` started it.

## Quick start

Needs Python 3, ffmpeg (`ffplay`), Claude Code, and VoiceStudio with a voice. Full walkthrough: **[docs/setup.md](docs/setup.md)**.

Windows, one command (installs Python, ffmpeg and VoiceStudio if missing, then adds the hooks):

```
git clone https://github.com/fastlaneracing/claude-voice.git && cd claude-voice
powershell -ExecutionPolicy Bypass -File setup.ps1     # add -DryRun to preview
```

Or, if the prerequisites are already installed:

```
python install.py                               # adds hooks to ~/.claude/settings.json
python scripts/speak.py --list-voices
python scripts/speak.py "Hello from Claude"
```

## Usage

```
python scripts/speak.py "text" [profile_id] [language] [speed]
python scripts/speak.py --list-voices
```

| Setting | Arg | Env var | Default |
|---|---|---|---|
| Voice profile | 2 | `CLAUDE_VOICE_PROFILE` | first non-demo profile |
| Language | 3 | `CLAUDE_VOICE_LANGUAGE` | `English` |
| Speed (0.5-2.0) | 4 | `CLAUDE_VOICE_SPEED` | `1.0` |
| Backend port | - | `OMNIVOICE_PORT` | `3900` |
| Backend folder | - | `VOICESTUDIO_PROJECT` | app's default location |

`python install.py --profile ID --speed 1.3` stores these in Claude Code's settings. `python install.py --uninstall` removes everything it added.

## Docs

- [docs/setup.md](docs/setup.md): install on a new machine
- [docs/architecture.md](docs/architecture.md): protocol and design decisions
- [docs/adding-voices.md](docs/adding-voices.md): adding or switching voices
- [docs/troubleshooting.md](docs/troubleshooting.md)
- [CHANGELOG.md](CHANGELOG.md)

## Notes

- Tested on Windows 11. macOS/Linux code paths exist but are untested.
- This repo contains no audio and no voice data. Only clone voices you have the right to use.
- VoiceStudio is a separate project (AGPL-3.0). This repo only calls its local HTTP API.

## License

MIT
