# Architecture

## Components

| File | Role |
|---|---|
| `scripts/speak.py` | Client. Ensures the backend is up, POSTs text, pipes PCM to `ffplay`. |
| `scripts/voice_session_start.py` | SessionStart hook; emits `additionalContext` telling Claude to offer voice. |
| `scripts/stop_backend.py` | SessionEnd hook; kills the backend only if `.backend_started_by_speak` exists. |
| `examples/settings.hooks.json` | Hook and permission config to merge into Claude Code settings. |

## Streaming protocol

`POST http://127.0.0.1:3900/generate` (form fields: `text`, `profile_id`, `language`, `speed`, `stream=true`) returns NDJSON:

- `start`: carries `sample_rate`
- `chunk`: base64 `pcm`, 16-bit mono
- `done`: take saved to VoiceStudio history
- `error`: script exits with the message

Each chunk is piped to `ffplay -nodisp -autoexit -f s16le -ar <sr> -ch_layout mono -i -`, so playback starts after the first chunk. ffmpeg 8 removed `-ac` for ffplay; `-ch_layout mono` replaces it.

## Backend lifecycle

If `/health` doesn't answer, `speak.py` launches the VoiceStudio venv python (`-m uvicorn backend.main:app`) hidden and detached, writes its PID to `.backend_started_by_speak`, and waits up to 180 s. A backend you started yourself (the app) is never stopped by the hook.

## Design decisions

- **Don't use the MCP `generate_speech` tool**: it returns the whole clip as ~180k chars of base64, which blows the context limit.
- **Don't save a WAV and play it**: streaming gives faster time-to-first-audio and leaves no files.
- **Stdlib only**, so there is nothing to install.
- Run with `python -I` so a stray module in the working directory can't be imported.
