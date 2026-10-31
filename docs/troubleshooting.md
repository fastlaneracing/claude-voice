# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| "backend ... was not found" | VoiceStudio isn't installed/launched once, or lives elsewhere. See docs/setup.md; set `VOICESTUDIO_PROJECT`. |
| Connection refused | Backend not running and auto-start failed. Start the VoiceStudio app. |
| "No voice profiles found" | Create or clone a voice in VoiceStudio. |
| `BrokenPipeError` | `ffplay` exited early. Run the ffplay command by hand to see its error. |
| `ffplay` not found | `winget install Gyan.FFmpeg`, then restart the shell. |
| `stream error` | Read the printed message; often the model is still loading, so retry. |
| Silent but no error | Check the default audio device and the speed/profile args. |
| Backend left running | Only if SessionEnd didn't fire: `taskkill /PID <pid in .backend_started_by_speak> /T /F`. |
| Voice prompt never appears | Confirm the hooks are in `settings.json` and the paths are correct. |
