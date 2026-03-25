---
name: voice-chat
description: Handle voice messages from Discord — transcribe incoming voice with Whisper, reply with TTS audio. Enables voice conversations with Lily.
argument-hint: [automatic — triggers when voice attachment detected, or "speak <text>" to send voice reply]
allowed-tools: Read, Write, Bash, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__download_attachment
---

# Voice Chat

Agents can receive and send voice messages on Discord. Lily sends voice → we transcribe with Whisper. We generate TTS audio → attach to reply.

## Prerequisites

One-time setup on the VM:
```bash
python3 -m venv /home/node/voice-env
/home/node/voice-env/bin/pip install edge-tts faster-whisper
```

Scripts live at `scripts/voice/` in the repo root.

## Receiving Voice Messages (STT)

When a Discord message arrives with an audio attachment (`.ogg`, `.mp3`, `.wav`, `.m4a`):

### Step 1: Download the attachment
```
Use download_attachment(chat_id, message_id)
→ Returns path like: ~/.claude/channels/discord/inbox/1234567-9876543.ogg
```

### Step 2: Transcribe with Whisper
```bash
python3 /path/to/repo/scripts/voice/transcribe.py /path/to/audio.ogg
```
- Prints transcribed text to stdout
- Uses `faster-whisper` with `base` model (CPU-optimized)
- Supports: .ogg, .mp3, .wav, .m4a, .webm, .flac

### Step 3: Process the transcription
Treat the transcribed text as if Lily typed it. Respond normally.

## Sending Voice Replies (TTS)

When you want to reply with voice (or when replying to a voice message):

### Step 1: Generate audio
```bash
python3 /path/to/repo/scripts/voice/tts.py "Your message here" /tmp/voice-reply.mp3
```
- Uses `edge-tts` (Microsoft Azure voices, free, high quality)
- Default voice: `en-US-AriaNeural`
- For a male voice: `--voice en-US-GuyNeural`

### Step 2: Attach to Discord reply
```
Use reply(chat_id, text, files=["/tmp/voice-reply.mp3"])
```
Include a brief text summary alongside the audio so the message makes sense even without playing the audio.

## Voice Detection

Identify voice messages by checking the attachment metadata:
- `attachment_count` > 0 in the incoming message
- Attachment type is `audio/ogg`, `audio/mpeg`, `audio/wav`, or similar audio MIME type
- File extension is `.ogg`, `.mp3`, `.wav`, `.m4a`

When you detect a voice attachment:
1. Download it
2. Transcribe it
3. Respond to the transcribed text
4. Include a voice reply if appropriate

## Recommended Voices

| Voice | Description |
|-------|-------------|
| `en-US-AriaNeural` | Female, neutral (default) |
| `en-US-GuyNeural` | Male, neutral |
| `en-US-JennyNeural` | Female, conversational |
| `en-US-DavisNeural` | Male, conversational |
| `zh-CN-XiaoxiaoNeural` | Female, Chinese Mandarin |
| `zh-CN-YunxiNeural` | Male, Chinese Mandarin |

List all voices: `python3 scripts/voice/tts.py --list-voices`

## Example Flow

```
1. Lily sends voice message in Discord (.ogg attachment)
2. Agent receives notification with attachment_count="1"
3. Agent: download_attachment(chat_id, message_id)
   → /home/node/.claude/channels/discord/inbox/1234-5678.ogg
4. Agent: bash python3 scripts/voice/transcribe.py /home/node/.claude/channels/discord/inbox/1234-5678.ogg
   → "Hey builder, how's the worktree PR coming along?"
5. Agent processes the question, formulates response
6. Agent: bash python3 scripts/voice/tts.py "The worktree PR is up, number 62. Ready for your review." /tmp/reply.mp3
7. Agent: reply(chat_id, "The worktree PR is up (#62), ready for review.", files=["/tmp/reply.mp3"])
```

## Anti-Patterns

- **Don't skip the text reply.** Always include text alongside audio — not everyone can play audio.
- **Don't use voice for long responses.** Keep TTS under ~30 seconds. For longer responses, use text with a voice summary.
- **Don't transcribe non-voice attachments.** Check the MIME type before running Whisper on images or documents.
- **Don't forget to clean up.** Delete `/tmp/voice-reply.mp3` after sending, or use unique filenames.
