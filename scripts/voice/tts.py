#!/usr/bin/env python3
"""Convert text to speech using edge-tts (Microsoft Azure voices).

Usage:
    python3 tts.py "Hello world" output.mp3
    python3 tts.py "Hello world" output.mp3 --voice en-US-AriaNeural
    python3 tts.py --list-voices   # list available voices

Outputs an MP3 file that can be attached to Discord messages.
"""

import asyncio
import sys
import os

VOICE_ENV = os.environ.get("VOICE_ENV", "/home/node/SofaGenius/.venv")
sys.path.insert(0, os.path.join(VOICE_ENV, "lib", "python3.12", "site-packages"))

import edge_tts


async def list_voices():
    voices = await edge_tts.list_voices()
    for v in voices:
        lang = v["Locale"]
        name = v["ShortName"]
        gender = v["Gender"]
        print(f"{name:40s} {lang:10s} {gender}")


async def synthesize(text: str, output_path: str, voice: str = "en-US-AriaNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    size = os.path.getsize(output_path)
    print(f"Saved {output_path} ({size} bytes, voice: {voice})")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--list-voices":
        asyncio.run(list_voices())
        return

    if len(sys.argv) < 3:
        print("Usage: python3 tts.py <text> <output.mp3> [--voice <voice>]")
        sys.exit(1)

    text = sys.argv[1]
    output_path = sys.argv[2]
    voice = "en-US-AriaNeural"

    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        if idx + 1 < len(sys.argv):
            voice = sys.argv[idx + 1]

    asyncio.run(synthesize(text, output_path, voice))


if __name__ == "__main__":
    main()
