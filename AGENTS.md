# AGENTS.md: spoken replies for any agent

This repo gives an AI agent a spoken voice. The agent runs one shell command with a short version of its reply; a local [VoiceStudio](https://github.com/debpalash/VoiceStudio) backend synthesizes it and streams it to the speakers through `ffplay`. Nothing here is specific to Claude or to any model provider: any agent that can run a shell command can use it. The model or inference provider (Anthropic, OpenAI, Gemini, Ollama, LM Studio, vLLM, OpenRouter, ...) does not matter, because speech is generated locally.

Two audiences:

- **You are an agent working in this repo**: see [Working on this repo](#working-on-this-repo).
- **You are an agent (or a person configuring one) that should speak**: see [Speaking](#speaking-instructions-for-any-agent) and [Platform setup](#platform-setup).

## Speaking (instructions for any agent)

### Rules

1. In your **first reply** of a session, ask the user: "Want voice on this session?"
2. If they say **yes**: for every reply from then on, still write the full text, and also speak a short version (under about 60 words, plain sentences, no code, no markdown, no URLs read aloud) by running the command below.
3. If they say **no**: never mention voice again.
4. If the command fails, tell the user once and continue in text only. Do not retry in a loop.
5. Run it as a normal shell command and wait for it to finish; it returns when playback ends.

### Command

```
python -I <REPO>/scripts/speak.py "text to speak" [profile_id] [language] [speed]
python -I <REPO>/scripts/speak.py --list-voices
```

Replace `<REPO>` with the absolute path of this clone. Use forward slashes or quote the path. `-I` stops a stray module in the working directory from being imported. Escape or avoid double quotes inside the text.

| Setting | Arg | Env var | Default |
|---|---|---|---|
| Voice profile | 2 | `CLAUDE_VOICE_PROFILE` | first non-demo profile |
| Language | 3 | `CLAUDE_VOICE_LANGUAGE` | `English` |
| Speed (0.5-2.0) | 4 | `CLAUDE_VOICE_SPEED` | `1.0` |
| Backend port | - | `OMNIVOICE_PORT` | `3900` |
| Backend folder | - | `VOICESTUDIO_PROJECT` | app's default location |

The env vars are named `CLAUDE_VOICE_*` for historical reasons and work for every agent. The backend starts automatically on first use (this can take up to 180 s the first time).

### Copy-paste instruction block

Put this in the agent's instruction file (see the table below), with `<REPO>` filled in:

```
Voice mode: in your first reply, ask "Want voice on this session?". If the user says yes,
then for every reply, write the full text as usual and also speak a short version
(under 60 words, no code or markdown) by running:
    python -I <REPO>/scripts/speak.py "short spoken version"
If the user says no, never mention voice again. If the command fails, tell the user once
and continue in text.
```

## Platform setup

Prerequisites on the machine (any platform): Python 3.8+, ffmpeg (`ffplay` on PATH), VoiceStudio installed and launched once with a voice created. Full steps: [docs/setup.md](docs/setup.md). Verify with `python scripts/speak.py "Hello"`.

Then give the agent the instruction block and permission to run the command. The only platform-specific parts are *where* the instruction goes and *how* the command is allowed.

| Agent platform | Where the instruction block goes | Allow the command |
|---|---|---|
| **Claude Code** | Automatic: `python install.py` adds a SessionStart hook that injects it | Added to `permissions.allow` by `install.py` |
| **OpenAI Codex CLI** and other tools that read `AGENTS.md` | A project or user-level `AGENTS.md` (this file already works if the agent runs in this repo) | Approve once, or add a command rule per Codex's approval/sandbox settings |
| **Gemini CLI** | `GEMINI.md` (project or `~/.gemini/`) | Approve when prompted, or allow the shell tool for this command |
| **Cursor** | A rule file in `.cursor/rules/` (always-apply) | Allow-list the command in terminal settings |
| **GitHub Copilot (agent mode)** | `.github/copilot-instructions.md` | Approve the terminal command when prompted |
| **Windsurf** | `.windsurf/rules/` or global rules | Add to the command allow-list |
| **Cline / Roo Code** | `.clinerules` / custom instructions | Add to auto-approved commands |
| **Aider** | A `CONVENTIONS.md` loaded with `--read`; run with `/run` or let it suggest shell commands | Confirm per command |
| **OpenCode, Goose, Continue, Zed agent, others** | The tool's system-prompt or rules file | Allow the shell tool for this command |
| **Local models (Ollama, LM Studio, vLLM, llama.cpp server)** | Use through any agent above, or through your own loop (below) | n/a |

These locations follow each tool's usual conventions; check the tool's current docs if a file name has changed. If a platform has no instruction file at all, paste the block as the first message of the session.

### Agents with no shell tool: wrap it as a tool

If your framework only supports function/tool calling (OpenAI-compatible APIs, Ollama, LM Studio, custom loops), expose one tool that runs the command. Provider-agnostic definition:

```json
{
  "type": "function",
  "function": {
    "name": "speak",
    "description": "Speak a short summary of your reply aloud on the user's speakers. Under 60 words, plain sentences.",
    "parameters": {
      "type": "object",
      "properties": { "text": { "type": "string" } },
      "required": ["text"]
    }
  }
}
```

Handler (Python): run `subprocess.run(["python", "-I", "<REPO>/scripts/speak.py", text], check=False)` with `text` passed as an argument list element (never through a shell string), and return "ok" or the error output to the model.

### Agents on a different machine than the speakers

`speak.py` plays audio on the machine it runs on. If the agent runs remotely (SSH, container, cloud), the voice will play there, not at your desk. Run the agent on the machine with the speakers, or forward commands to it. The backend only listens on `127.0.0.1`.

## Working on this repo

- Python **standard library only**: do not add pip dependencies.
- Do not use the VoiceStudio MCP `generate_speech` tool for replies; it returns the whole clip as base64 and overflows context. Use `scripts/speak.py` (streaming).
- Do not save audio files or open a media player. Playback is a PCM pipe to `ffplay` (`-ch_layout mono`; ffmpeg 8 removed `-ac`).
- Never stop a backend you did not start: `stop_backend.py` only acts when `.backend_started_by_speak` exists.
- `install.py` edits Claude Code settings only; keep it idempotent and keep the `.bak` behavior. Hooks (`voice_session_start.py`, `stop_backend.py`) are Claude Code-specific; other platforms use the instruction block above.
- Protocol and rationale: [docs/architecture.md](docs/architecture.md). Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md).
- Update [CHANGELOG.md](CHANGELOG.md) for user-visible changes, and keep the vault copy at `C:\lanes vault\VoiceStudio\claude-voice` in sync.
- This repo holds no audio or voice data. Only clone voices you have the right to use.
