# Adding and switching voices

1. Create or clone the voice in the VoiceStudio app (or via its MCP tools: `clone_voice`, `design_voice`).
2. List ids: `python scripts/speak.py --list-voices`
3. Try it: `python scripts/speak.py "Testing" <profile_id>`
4. Make it the default: `python install.py --profile <profile_id>` (sets `CLAUDE_VOICE_PROFILE` in Claude Code settings), or export the variable yourself.

Notes:
- A profile's saved language may differ from English; `language` defaults to `English` explicitly, so pass a language as the third argument or set `CLAUDE_VOICE_LANGUAGE` for other voices.
- With no profile set, the first non-demo profile is used.
- Keep a personal list of your voices below if you like (ids are local to your VoiceStudio install, so they differ per machine):

| Name | profile_id | Notes |
|---|---|---|
| | | |
