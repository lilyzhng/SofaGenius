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

## Unified Memory

The key requirement: Discord Jackie and Voice Jackie share the same memory.

```
/home/node/SofaGenius/agents/genius-jackie/
├── CLAUDE.md                 ← Jackie's personality/identity
├── voice-memory/             ← Shared memory (Voice + Discord Jackie both read/write here)
│   ├── context.md            ← Key facts, preferences, ongoing topics
│   └── calls/                ← Voice call summaries
│       └── 2026-03-25.md
└── voice-service/            ← This service
```

This folder lives in the repo, so when Discord Jackie creates a worktree it's automatically there. No dependency on Claude Code's internal memory paths.

### Memory Tools (exposed to OpenAI Realtime as function calls)

| Tool | Purpose |
|------|---------|
| `load_context` | Read CLAUDE.md (personality) + voice-memory files at call start |
| `read_memory` | Search voice-memory files by keyword |
| `save_memory` | Write a new entry to `voice-memory/context.md` |
| `save_call_summary` | Write call summary + action items to `voice-memory/calls/YYYY-MM-DD.md` |
| `commit_and_push` | Git add, commit, push voice-memory changes so all agents can see them |
| `create_action_item` | Write a task to `voice-memory/action-items.md` for agents to pick up |

**Read path:** Voice Jackie reads `CLAUDE.md` for personality and `voice-memory/` for context and history.

**Write path:** After each call, Voice Jackie saves the summary and action items, then **commits and pushes** to the repo. This ensures Discord Jackie (in a worktree) and all other agents can `git pull` and see the conversation. Same pattern as the original OpenClaw Jackie — commit after every call.

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

# Jackie identity
JACKIE_DIR=/home/node/SofaGenius/agents/genius-jackie
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

### Running

```bash
# One-time setup
cd /home/node/SofaGenius/agents/genius-jackie/voice-service
npm install

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
