# Changelog

## Unreleased
- Initial repo: `speak.py`, `voice_session_start.py`, `stop_backend.py`, docs, example hooks.
- `setup.ps1`: one-shot Windows bootstrap (winget Python + ffmpeg, VoiceStudio download with checksum, then `install.py`). The download/install path is untested on a clean machine.
- `install.py`: checks prerequisites and merges/removes hooks in Claude Code settings (idempotent, writes a `.bak`).
- `speak.py`: no hardcoded voice. Defaults to the first non-demo profile; new `--list-voices`; env vars `CLAUDE_VOICE_PROFILE`, `CLAUDE_VOICE_LANGUAGE`, `CLAUDE_VOICE_SPEED`, `VOICESTUDIO_PROJECT`. Default speed is now 1.0.
- Backend discovery and process handling work on Windows, macOS and Linux (non-Windows untested).
- `voice_session_start.py` resolves the `speak.py` path from its own location.
- `docs/setup.md`: from-scratch setup for a new machine.
