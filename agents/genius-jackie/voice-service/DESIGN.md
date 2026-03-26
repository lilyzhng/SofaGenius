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

Voice Jackie uses GPT-4o-realtime, Discord Jackie uses Claude. Different models, but same personality and memory — alignment comes from shared memory files, not model choice.

## Call Flow

### Inbound Call
1. Someone calls Jackie's Twilio number
2. Twilio POSTs to webhook → returns TwiML with `<Connect><Stream>` pointing to WebSocket
3. WebSocket opens → connects to OpenAI Realtime API
4. First thing: tool call to `load_context()` — reads Jackie's memory + system prompt
5. Bidirectional audio streams between Twilio ↔ OpenAI Realtime
6. On call end: tool calls to `save_call_summary()` + `create_action_item()` + `commit_and_push()` — saves summary, action items, and pushes to repo

### Outbound Call (future)
1. Jackie triggers outbound call (e.g., evening reflection at 10:45 PM PT)
2. Twilio REST API initiates call → same WebSocket flow once answered

## Memory — Two-Repo Approach

Personal conversations should stay private. Voice Jackie uses two repos:

| Repo | Visibility | Purpose |
|------|-----------|---------|
| `lilyzhng/SofaGenius` | Public | Voice service code, Jackie's CLAUDE.md personality |
| `lilyzhng/jackie-memory` | Private | Call summaries, action items, personal context |

### Layout on the VM

```
/home/node/jackie-memory/              ← clone of lilyzhng/jackie-memory (private)
├── calls/                             ← Voice call summaries
│   └── 2026-03-25.md
├── action-items.md                    ← Tasks from calls for agents to pick up
└── context.md                         ← Key facts, preferences, ongoing topics

/home/node/SofaGenius/agents/genius-jackie/
├── CLAUDE.md                          ← Jackie's personality/identity
├── private-memory -> /home/node/jackie-memory/   ← symlink (read-only for Discord Jackie)
└── voice-service/                     ← This service (code only, no personal data)
```

**Privacy guarantee:** Personal call content only ever gets pushed to the private `lilyzhng/jackie-memory` repo. The symlink lets Discord Jackie read the memories, but his git context is SofaGenius — commits from Discord Jackie go to the public repo, never touching private content.

### Memory Tools (exposed to OpenAI Realtime as function calls)

| Tool | Purpose |
|------|---------|
| `load_context` | Read CLAUDE.md (personality) + private memory files at call start |
| `read_memory` | Search private memory files by keyword |
| `save_memory` | Write a new entry to `context.md` in private repo |
| `save_call_summary` | Write call summary to `calls/YYYY-MM-DD.md` in private repo |
| `create_action_item` | Append a task to `action-items.md` in private repo |
| `commit_and_push` | Git add, commit, push to `lilyzhng/jackie-memory` (private) |

**Read path:** Voice Jackie reads `CLAUDE.md` from SofaGenius for personality, and `/home/node/jackie-memory/` for personal context and history.

**Write path:** After each call, Voice Jackie saves the summary and action items to `/home/node/jackie-memory/`, then **commits and pushes to `lilyzhng/jackie-memory`**. Discord Jackie can read these via the symlink. Same pattern as the original OpenClaw Jackie — commit after every call.

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
│   └── tools.ts              # Memory read/write + git commit tool definitions (~120 lines)
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

# Jackie identity + memory
JACKIE_DIR=/home/node/SofaGenius/agents/genius-jackie
JACKIE_MEMORY_DIR=/home/node/jackie-memory
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
  "voice": "alloy",
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

### One-Time Setup

```bash
# 1. Clone private memory repo
cd /home/node
git clone https://github.com/lilyzhng/jackie-memory.git jackie-memory

# 2. Symlink so Discord Jackie can read private memories
ln -s /home/node/jackie-memory /home/node/SofaGenius/agents/genius-jackie/private-memory

# 3. Install voice service
cd /home/node/SofaGenius/agents/genius-jackie/voice-service
npm install
```

### Running

```bash
# Run (alongside Jackie's Claude Code session)
node dist/index.js
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

1. **Tunnel provider** — Is Tailscale already on the VM, or should we use ngrok?
2. **Call recording** — Should we save audio recordings, or just text summaries?
3. **Auth** — Should we restrict who can call Jackie? (Caller ID allowlist, or open?)
