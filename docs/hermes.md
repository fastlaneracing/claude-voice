# Using with Hermes Agent

Hermes Agent (CLI, desktop, dashboard, or a messaging bot) can speak with any VoiceStudio voice, no plugins and no pip packages. It works through Hermes's **command TTS provider**: Hermes writes the text to a temp file, runs a shell command, and plays or delivers the audio file the command produces. `scripts/vs_tts.py` is the adapter that bridges Hermes to the local VoiceStudio backend (`POST /v1/audio/speech`).

## 1. Prerequisites

Same as the rest of this repo (see [setup.md](setup.md)):

- Python 3.8+ (stdlib only)
- ffmpeg on PATH (`ffplay`), so the finished clip can play
- VoiceStudio installed and launched once, with at least one voice created
- This repo cloned (example below uses `C:/devops/claude-voice`)
- Hermes Agent installed (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`, or its Windows installer)

Check the backend answers before wiring it in:

```
curl http://127.0.0.1:3900/health
```

Note: unlike `speak.py`, `vs_tts.py` does **not** auto-start the backend — keep the VoiceStudio app running, or start the backend yourself before Hermes speaks.

## 2. Configure the TTS provider

The config lives in Hermes's `config.yaml` (for this install: `%LOCALAPPDATA%\hermes\config.yaml`). Edit it with `hermes config` — hand-editing the YAML can corrupt the live gateway — or merge the block by hand.

```
hermes config set tts.provider voicestudio
hermes config set tts.providers.voicestudio.type command
hermes config set "tts.providers.voicestudio.command" "python -I C:/devops/claude-voice/scripts/vs_tts.py --input {input_path} --output {output_path} --voice lane --speed 1.7 --base http://127.0.0.1:3900"
hermes config set tts.providers.voicestudio.format mp3
hermes config set tts.providers.voicestudio.timeout 300
```

The same block as YAML (this is what the command above writes):

```yaml
tts:
  provider: voicestudio
  providers:
    voicestudio:
      type: command
      command: python -I C:/devops/claude-voice/scripts/vs_tts.py --input {input_path} --output {output_path} --voice lane --speed 1.7 --base http://127.0.0.1:3900
      format: mp3
      timeout: 300
```

Replace the path with your clone's path (forward slashes), `lane` with your profile id (`python scripts/speak.py --list-voices` to list), and `1.7` with the speed you like.

| Key | Meaning |
|---|---|
| `command` | The adapter command. `{input_path}` = text file Hermes wrote, `{output_path}` = file the adapter must write audio to. |
| `format` | `mp3` / `wav` / `ogg` / `flac` / `m4a` / `aac` / `amr` / `opus`. Must match what the command writes (the adapter takes the format from the output extension). |
| `voice` | Optional. Fills the `{voice}` placeholder if you prefer Hermes to hold the voice instead of hardcoding it in the command. |
| `speed` | Optional global speed; the adapter's `--speed` flag is the simplest way to set it. |
| `timeout` | Seconds before Hermes kills the command (default 120; raise it if a voice cold-start is slow). |
| `voice_compatible` | Optional `true` — converts the output to Opus/OGG so messaging platforms deliver a voice bubble instead of a file. |
| `env_passthrough` | Optional list of env var names to pass through the scrubbed subprocess env (not needed here; no keys are involved). |

## 3. Test

Direct (writes a file, plays it, returns when playback ends):

```
python -I C:/devops/claude-voice/scripts/vs_tts.py --input <any_text_file> --output test.mp3
python -I C:/devops/claude-voice/scripts/vs_tts.py --input <any_text_file> --output test.wav --no-play
```

`--no-play` skips ffplay (use it for delivery contexts where the file should just be returned).

Through Hermes, in a session:

```
/voice tts            # speak replies as voice
say "Hello from Hermes"   # or use the text_to_speech tool
```

## 4. Spoken replies for the agent

The config above gives Hermes the *ability* to speak. To make it actually speak its replies (a short summary, under about 60 words, while the full text is still written), add the voice rule from [AGENTS.md](../AGENTS.md) — "Copy-paste instruction block" — to Hermes's `SOUL.md` (or the profile's `SOUL.md`, for a per-profile behavior). The block already names `scripts/speak.py` as the command to run, so it works unchanged; the agent just needs permission to run that command in its terminal tool.

## Notes

- Delivery: on the CLI the clip is played locally; on messaging platforms (Telegram, Discord, ...) the file is delivered as an audio attachment unless `voice_compatible: true` converts it to a voice bubble.
- Long texts: Hermes splits input longer than the provider's `max_text_length` (default 5000 chars) into ordered chunks; each chunk runs the command once.
- The backend only listens on `127.0.0.1`, so Hermes must run on the machine with the speakers — or the command must be forwarded there.
- Do not point Hermes at VoiceStudio's MCP `generate_speech` tool instead; it returns the whole clip as base64 and overflows context (see [architecture.md](architecture.md)).
