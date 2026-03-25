#!/usr/bin/env python3
"""Transcribe audio to text using faster-whisper (CPU-optimized).

Usage:
    python3 transcribe.py input.ogg
    python3 transcribe.py input.ogg --model base
    python3 transcribe.py input.ogg --model small

Prints the transcribed text to stdout.
Supports: .ogg, .mp3, .wav, .m4a, .webm, .flac (anything ffmpeg can decode)
"""

import sys
import os

VOICE_ENV = os.environ.get("VOICE_ENV", "/home/node/SofaGenius/.venv")
sys.path.insert(0, os.path.join(VOICE_ENV, "lib", "python3.12", "site-packages"))

from faster_whisper import WhisperModel


def transcribe(audio_path: str, model_size: str = "base"):
    if not os.path.exists(audio_path):
        print(f"Error: file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading {model_size} model...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"Transcribing {audio_path}...", file=sys.stderr)
    segments, info = model.transcribe(audio_path, beam_size=5)

    print(f"Detected language: {info.language} (probability {info.language_probability:.2f})", file=sys.stderr)

    full_text = ""
    for segment in segments:
        full_text += segment.text

    # Print transcription to stdout (clean, no metadata)
    print(full_text.strip())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    audio_path = sys.argv[1]
    model_size = "base"

    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model_size = sys.argv[idx + 1]

    transcribe(audio_path, model_size)


if __name__ == "__main__":
    main()
