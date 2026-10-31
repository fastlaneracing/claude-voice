"""VoiceStudio TTS adapter for Hermes's command-TTS provider.

Reads the text to speak from a file and writes the synthesized audio to an
output file, talking to the local VoiceStudio backend (OpenAI-compatible
``POST /v1/audio/speech``). Standard library only — no pip dependencies.

This is the bridge between Hermes (``tts.providers.<name>.command``) and the
VoiceStudio backend, so any agent can speak with a VoiceStudio voice.

Usage (driven by Hermes, but also callable directly):
  python vs_tts.py --input <text_file> --output <audio_file> [--voice NAME]
                   [--speed 1.0] [--base http://127.0.0.1:3900] [--model omnivoice]
                   [--play | --no-play]

Playback: by default the finished clip is played to the local speakers with
ffplay (the command returns when playback ends). Use --no-play for delivery
contexts where the audio file should just be returned.

Exit code 0 on success (audio written, non-empty); non-zero with a message on
stderr otherwise. The output file's extension picks the response format
(mp3/wav/ogg/flac/m4a/aac/opus/...).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("OMNIVOICE_PORT", "")
DEFAULT_BASE = f"http://127.0.0.1:{DEFAULT_BASE}" if DEFAULT_BASE else "http://127.0.0.1:3900"

# Formats the backend can emit; anything else falls back to mp3.
FORMATS = {"mp3", "wav", "ogg", "flac", "m4a", "aac", "amr", "opus"}


def _die(msg: str, code: int = 1) -> None:
    print(f"vs_tts: {msg}", file=sys.stderr)
    sys.exit(code)


def _post_json(base: str, path: str, payload: dict, timeout: float):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def _default_profile_id(base: str) -> str:
    """First non-demo voice profile (mirrors speak.py); '' if none."""
    try:
        with urllib.request.urlopen(base + "/profiles", timeout=15) as r:
            profiles = json.load(r)
    except Exception:
        return ""
    real = [p for p in profiles if not p.get("is_demo")]
    pick = (real or profiles) or []
    return pick[0]["id"] if pick else ""


def main() -> None:
    ap = argparse.ArgumentParser(description="VoiceStudio TTS adapter for Hermes")
    ap.add_argument("--input", required=True, help="path to the text file to speak")
    ap.add_argument("--output", required=True, help="path to write the audio file")
    ap.add_argument("--voice", default="", help="voice profile id/name (default: first non-demo)")
    ap.add_argument("--speed", default="", help="speed multiplier 0.5-2.0 (default: backend 1.0)")
    ap.add_argument("--base", default=DEFAULT_BASE, help="backend base URL")
    ap.add_argument("--model", default="omnivoice", help="engine/model id")
    ap.add_argument("--timeout", type=float, default=300.0, help="request timeout (s)")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--play", dest="play", action="store_true",
                     help="play the finished clip to the local speakers (default)")
    grp.add_argument("--no-play", dest="play", action="store_false",
                     help="only write the audio file, do not play it")
    ap.set_defaults(play=True)
    args = ap.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        _die(f"cannot read input {args.input}: {e}")
    if not text.strip():
        _die("input text is empty")

    voice = args.voice.strip() or _default_profile_id(args.base)
    if not voice:
        _die("no voice specified and no voice profile found on the backend")

    fmt = os.path.splitext(args.output)[1].lstrip(".").lower()
    if fmt not in FORMATS:
        fmt = "mp3"

    payload = {
        "model": args.model,
        "voice": voice,
        "input": text,
        "response_format": fmt,
    }
    if args.speed.strip():
        try:
            payload["speed"] = max(0.25, min(4.0, float(args.speed)))
        except ValueError:
            pass

    base = args.base.rstrip("/")
    try:
        urllib.request.urlopen(base + "/health", timeout=10).read()
    except Exception as e:
        _die(f"VoiceStudio backend is not reachable at {base} ({e}). "
             f"Start the VoiceStudio app/backend first.")
    try:
        status, body = _post_json(base, "/v1/audio/speech", payload, args.timeout)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        _die(f"HTTP {e.code} from {base}/v1/audio/speech: {detail or e.reason}")
    except Exception as e:
        _die(f"request to {base} failed: {e}")

    if status != 200 or not body:
        _die(f"backend returned {status} with {len(body)} bytes")

    out = args.output
    d = os.path.dirname(os.path.abspath(out))
    os.makedirs(d, exist_ok=True)
    with open(out, "wb") as f:
        f.write(body)
    if os.path.getsize(out) <= 0:
        _die("backend wrote an empty audio file")

    if args.play:
        ffplay = shutil.which("ffplay")
        if not ffplay:
            print("vs_tts: warning: ffplay not found; audio written but not played "
                  "(install ffmpeg, or pass --no-play)", file=sys.stderr)
        else:
            # Stream the finished file to the speakers; returns when playback ends.
            player = subprocess.Popen(
                [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", "-i", out])
            rc = player.wait()
            if rc != 0:
                print(f"vs_tts: warning: ffplay exited {rc}; audio file still valid: {out}",
                      file=sys.stderr)

    print(f"ok voice={voice} fmt={fmt} bytes={len(body)} -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
