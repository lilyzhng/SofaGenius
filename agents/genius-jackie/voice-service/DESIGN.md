# Jackie Voice Service — Design Doc

## Overview

A standalone Node.js service that gives Jackie phone call capability on Agent Computer. Uses Twilio for telephony and OpenAI Realtime API for speech-to-speech conversation — no separate STT/TTS pipeline needed.

Voice Jackie shares memory with Discord Jackie by reading/writing the same files on the VM.

## Architecture

```
Phone ←→ Twilio ←→ Webhook Server ←→ OpenAI Realtime API (GPT-4o)
                    (on jackie-chan VM)        ↕
                                          Tool calls
                                      (read/write memory)
```

**Why OpenAI Realtime instead of Claude?**
- Single WebSocket handles STT + reasoning + TTS — no orchestration needed
- Sub-500ms latency (all server-side at OpenAI)
- Native mu-law audio passthrough (Twilio's format) — no codec conversion
- Built-in VAD (voice activity detection) and barge-in support
- ~500 lines of code vs ~1500 for a multi-service pipeline

**Trade-off:** Voice Jackie uses GPT-4o-realtime, Discord Jackie uses Claude. Same personality and memory, different underlying model.

## Call Flow

### Inbound Call
1. Someone calls Jackie's Twilio number
2. Twilio POSTs to webhook → returns TwiML with `<Connect><Stream>` pointing to WebSocket
3. WebSocket opens → connects to OpenAI Realtime API
4. First thing: tool call to `load_context()` — reads Jackie's memory + system prompt
5. Bidirectional audio streams between Twilio ↔ OpenAI Realtime
6. On call end: tool call to `save_call_summary()` — writes summary to memory

### Outbound Call (future)
1. Jackie triggers outbound call (e.g., evening reflection at 10:45 PM PT)
2. Twilio REST API initiates call → same WebSocket flow once answered

## Unified Memory

The key requirement: Discord Jackie and Voice Jackie share the same memory.

```
# Claude Code memory (Discord Jackie reads/writes here)
~/.claude/projects/<project-hash>/memory/
├── MEMORY.md                 ← Memory index
├── user_*.md                 ← User memories
├── feedback_*.md             ← Feedback memories
└── project_*.md              ← Project memories

# Jackie's repo directory
/home/node/SofaGenius/agents/genius-jackie/
├── CLAUDE.md                 ← Jackie's personality/identity
├── voice-service/            ← This service
│   └── call-logs/            ← Voice call summaries (NEW)
│       └── 2026-03-25.md
└── ...
```

> **Note:** Claude Code stores memory at `~/.claude/projects/{project-hash}/memory/`, not inside the repo. The exact `{project-hash}` is derived from the working directory. Voice Jackie discovers this path at startup via `CLAUDE_MEMORY_PATH` env var.

### Memory Tools (exposed to OpenAI Realtime as function calls)

| Tool | Purpose |
|------|---------|
| `load_context` | Read CLAUDE.md (personality) + memory files at call start |
| `read_memory` | Search memory files by keyword |
| `save_memory` | Write a new memory entry (same format as Claude Code memories) |
| `save_call_summary` | Append call summary to `voice-service/call-logs/YYYY-MM-DD.md` |

**Read path:** Voice Jackie reads `~/.claude/projects/{project-hash}/memory/MEMORY.md` to know what Discord Jackie remembers. It also reads any memory files referenced there.

**Write path:** Voice Jackie writes call summaries to `voice-service/call-logs/`. For shared memories, it writes to Claude Code's memory directory in the same format. When Discord Jackie's Claude Code session starts, it picks up these files naturally.

## File Structure

```
agents/genius-jackie/voice-service/
├── package.json
├── tsconfig.json
├── .env.example              # Template for required env vars
├── src/
│   ├── index.ts              # Entry point — start webhook server (~30 lines)
│   ├── config.ts             # Env var loading + validation (~40 lines)
│   ├── webhook.ts            # HTTP server, TwiML responses (~120 lines)
│   ├── media-stream.ts       # WebSocket ↔ OpenAI Realtime bridge (~200 lines)
│   └── tools.ts              # Memory read/write tool definitions (~100 lines)
└── README.md                 # Setup & deployment instructions
```

**Total: ~500 lines of application code.**

## Configuration

### Environment Variables

```bash
# Twilio (existing account)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# OpenAI
OPENAI_API_KEY=sk-...

# Server
PORT=3334
PUBLIC_URL=https://...  # Set by tunnel or manual config

# Jackie identity
JACKIE_REPO_PATH=/home/node/SofaGenius/agents/genius-jackie
CLAUDE_MEMORY_PATH=/home/node/.claude/projects/<project-hash>/memory
```

### System Prompt (loaded from CLAUDE.md)

Voice Jackie uses the same `CLAUDE.md` personality as Discord Jackie, with a voice-specific preamble:

```
You are Jackie, Lily's always-on assistant. You are currently on a phone call.
Keep responses conversational and concise — this is voice, not text.
Match Lily's mixed Chinese/English style.
[... rest of CLAUDE.md personality ...]
```

### OpenAI Realtime Session Config

```json
{
  "model": "gpt-4o-realtime-preview",
  "modalities": ["text", "audio"],
  "voice": "TBD",              // see Open Questions #1
  "input_audio_format": "g711_ulaw",
  "output_audio_format": "g711_ulaw",
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "silence_duration_ms": 800
  },
  "tools": [...]
}
```

## Deployment on Agent Computer

### Public URL Exposure

The VM needs a public URL for Twilio webhooks. Options:

1. **ngrok** (simplest) — `ngrok http 3334`, free tier works for dev
2. **Tailscale Funnel** — if Tailscale is already on the VM, `tailscale funnel 3334`
3. **Agent Computer port forwarding** — check if the platform supports public ports

### Running

```bash
# One-time setup
cd /home/node/SofaGenius/agents/genius-jackie/voice-service
npm install

# Run (alongside Jackie's Claude Code session)
node dist/index.js
# With auto-restart (recommended for production):
# Add to Jackie's launch-bg.sh with a restart loop:
# while true; do node dist/index.js; sleep 5; done &
```

### Twilio Configuration

Point the Twilio phone number's webhook to:
```
POST https://<public-url>/voice/webhook
```

## Scope & Non-Goals

### In scope
- Inbound calls (someone calls Jackie)
- Memory read/write during calls
- Call summaries saved after each call

### Future (not in v1)
- Outbound calls (Jackie calls Lily at 10:45 PM)
- Cron-triggered calls
- Discord notification when a call happens
- Tool calls beyond memory (GitHub, email, calendar)

## Open Questions

1. **Voice selection** — Which OpenAI voice fits Jackie? Options: alloy, ash, ballad, coral, echo, shimmer, sage, verse. Need to test.
2. **Tunnel provider** — Is Tailscale already on the VM, or should we use ngrok?
3. **Call recording** — Should we save audio recordings, or just text summaries?
4. **Auth** — Should we restrict who can call Jackie? (Caller ID allowlist, or open?)
