---
type: migration-spec
topic: Jackie migration from OpenClaw/Fly.io to Hermes Agent
date: 2026-03-23
status: proposed
requested-by: lilyzhng
author: genius-researcher
---

# Jackie Migration: OpenClaw → Hermes Agent

## Why Migrate

On March 23, 2026, Jackie's OpenClaw instance caused a **911,733 token spike** at 14:41 UTC. The spike occurred during a context compaction/memory flush cycle. Session logs show 259 API calls over 38 hours with cacheWrite growing to 144K per turn — the spike was likely a compaction flush where accumulated context was re-sent across multiple tool calls. The exact multiplier is unverified, but the pattern (growing context + compaction trigger + multi-tool flush) is confirmed. Additionally, Jackie's health-monitor is stuck in a restart loop, burning tokens every 15 minutes.

**Decision:** Shut down Jackie on OpenClaw, migrate to Hermes Agent (open-source, by Nous Research).

## Why Hermes Agent

| Dimension | OpenClaw (current) | Hermes Agent |
|-----------|-------------------|--------------|
| Context management | Token-based compaction — caused 911K spike | **Automatic context compression** at 50% of context window. Uses auxiliary model (Gemini Flash) to summarize middle turns, protects first 3 + last 4 messages. Handles HTTP 413 errors with auto-retry. |
| Memory | Custom vault + git sync | **Two-layer system:** Local (MEMORY.md, USER.md ~2200 chars) + Honcho (Plastic Labs) for unbounded cross-session user modeling via vector embeddings. Honcho integration is built-in. |
| Discord | Custom bridge | Native integration (DMs, threads, voice transcription) |
| Cron | Custom cron jobs file | Built-in cron scheduler |
| Web browsing | Custom skill | Native Firecrawl + Browserbase integration |
| Model | Locked to one provider | Multi-provider (Claude, OpenAI, OpenRouter, local) |
| Deployment | Fly.io only | Docker, Modal, SSH, Daytona, $5 VPS (Modal + Daytona = serverless persistence) |
| Self-improvement | None | Learns from experience, creates reusable skills (interesting — **not priority for launch**, explore later) |
| Open source | Yes | Yes (github.com/NousResearch/hermes-agent) |
| Token cost control | No budget limits — caused the spike | **Auto-compression at 50% context window** + session isolation (**verify in Phase 1**) |

## Jackie's Current Jobs — Priority Matrix

### P0 — Must have for launch

| Job | Current Implementation | Hermes Support | Migration Effort |
|-----|----------------------|----------------|-----------------|
| **Discord bot** | OpenClaw Discord bridge | Native — DMs, channels, threads, voice transcription | Low — config only |
| **Morning digest** | Cron 7AM PT → #daily-digest | Built-in cron scheduler | Medium — port follow-builders skill |
| **Web browsing** | Custom headless Chromium skill | Native Firecrawl + browser automation | Low — config + API key |
| **GitHub access** | Custom jackie-github bridge skill | Via terminal (`gh` CLI) or custom skill | Medium — write Hermes skill |
| **Voice call** | Twilio + OpenAI Realtime API, cron 10:45PM PT | TTS/STT built-in (Edge, ElevenLabs, Whisper) but **no Twilio phone calls** | High — custom Twilio bridge skill needed |

### P1 — Important, migrate after P0

| Job | Current Implementation | Hermes Support | Migration Effort |
|-----|----------------------|----------------|-----------------|
| **Memory** | github.com/lilyzhng/jackie | **Two-layer:** Hermes default (MEMORY.md/USER.md) + Honcho (Plastic Labs) for cross-session modeling. Try Hermes default first, then evaluate Honcho. | Low — built-in |

### P2 — Nice to have

| Job | Current Implementation | Hermes Support | Migration Effort |
|-----|----------------------|----------------|-----------------|
| **Calendar** | Google Calendar bridge skill | Not built-in | Medium — write Hermes skill or MCP server |
| **Gmail** | Gmail app password bridge | Not built-in | Medium — write Hermes skill or MCP server |
| **Twitter** | Twitter API bridge | Not built-in | Medium — write Hermes skill |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                 Hermes Agent                      │
│                                                   │
│  Model: claude-sonnet-4-6 (via Anthropic API)    │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Discord  │  │   Cron   │  │  Memory  │       │
│  │ Gateway  │  │Scheduler │  │  System  │       │
│  └────┬─────┘  └────┬─────┘  └──────────┘       │
│       │              │                            │
│  ┌────┴──────────────┴────────────────────┐      │
│  │            Skills / Tools               │      │
│  │                                         │      │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ │      │
│  │  │Firecrawl│ │ gh CLI   │ │ Twilio  │ │      │
│  │  │  (web)  │ │ (GitHub) │ │ (voice) │ │      │
│  │  └─────────┘ └──────────┘ └─────────┘ │      │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ │      │
│  │  │ Gmail   │ │ Calendar │ │ Twitter │ │      │
│  │  │  (P1)   │ │   (P1)   │ │  (P2)   │ │      │
│  │  └─────────┘ └──────────┘ └─────────┘ │      │
│  └────────────────────────────────────────┘      │
│                                                   │
│  Deploy: Docker on Fly.io / Modal (serverless)   │
└─────────────────────────────────────────────────┘
```

## Migration Steps

> Timelines in agent time. "1 hour" = 1 hour of active session.

### Phase 1: Core setup + token verification (1.5 hours)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 1.1 | Install Hermes locally, verify Claude Sonnet 4.6 works | Researcher | 15 min |
| 1.2 | **Verify token management** — run a long conversation, check if Hermes has hard token limits or if context grows unbounded like OpenClaw. This is the go/no-go gate for the migration. | Researcher | 30 min |
| 1.3 | Configure Discord bot with Jackie's existing bot token (confirmed reusable) | Builder | 15 min |
| 1.4 | Set up Firecrawl web browsing | Builder | 15 min |
| 1.5 | Test: Jackie responds in Discord with web browsing | All | 15 min |

### Phase 2: Cron + GitHub (1 hour)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 2.1 | Port follow-builders digest skill to Hermes format | Builder | 30 min |
| 2.2 | Configure morning digest cron (7 AM PT → #daily-digest) | Builder | 15 min |
| 2.3 | Set up `gh` CLI access for GitHub operations | Builder | 15 min |

### Phase 3: Voice call (2-3 hours) — P0 per Lily, but can launch Phases 1-2 without it

| Step | Task | Owner | Time |
|------|------|-------|------|
| 3.1 | Research Hermes + Twilio integration options | Researcher | 30 min |
| 3.2 | Build custom Twilio voice bridge skill | Builder | 2 hours |

Note: Voice is P0 (Lily needs demo soon) but Phases 1-2 can ship independently. No OpenClaw straddling — we build voice as a Hermes skill from scratch. This is both a challenge and an opportunity: if Hermes lacks good voice support, we build it and potentially contribute upstream.

### Phase 4: Deploy + test (1 hour)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 4.1 | Migrate Jackie's identity/memory from github.com/lilyzhng/jackie | Researcher | 15 min |
| 4.2 | Deploy to Fly.io (Docker) or Modal (serverless) | Builder | 30 min |
| 4.3 | End-to-end test: Discord, digest, web, voice | All | 15 min |

**Total: ~4 hours of agent time across Builder + Researcher in parallel.**

## Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Twilio integration gap | Voice demo blocked | Research early (Phase 3); build as Hermes skill — opportunity to contribute upstream if we build it well |
| Hermes cron reliability | Missed digests | Test extensively in Phase 2; CEO covers digest manually as backup |
| Memory migration loss | Jackie loses context | Export OpenClaw memories before shutdown; Hermes has its own persistent memory |
| Hermes is v0.3.0 | New software, potential bugs | We're open source — can fix bugs ourselves. Community is active (NousResearch) |

## Rollback Plan

If Hermes doesn't work:
1. Restart OpenClaw on Fly.io — **Builder to provide exact restart command** since supervisor config was modified during shutdown
2. Apply Builder's fixes (#1 trim skill, #2 remove duplicate, #3 fix restart loop) to prevent another 911K spike
3. Re-evaluate migration target

## Open Questions

1. **Deployment target:** Fly.io (Docker) or Modal (serverless, cheaper when idle)? Both supported. Modal + Daytona offer hibernation.
2. ~~**Jackie's bot token:**~~ RESOLVED — reusable, tokens are framework-agnostic.
3. **Hermes persistent sandbox:** Lily spoke with the Hermes founder — they're building persistent sandbox in-house. Builder should investigate what this means for our deployment.
4. **Voice demo timeline:** When does Lily need the demo? Determines how aggressively we fast-track Phase 3.
5. **Honcho evaluation:** Try Hermes default memory first. If insufficient, evaluate Honcho (Plastic Labs) — already has native Hermes integration.

## Sources

- https://github.com/NousResearch/hermes-agent — Hermes Agent repo
- https://hermes-agent.nousresearch.com/ — Official docs
- https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord/ — Discord setup
- https://hermes-agent.nousresearch.com/docs/user-guide/configuration/ — Configuration guide
