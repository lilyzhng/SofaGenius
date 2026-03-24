# Jackie Migration: OpenClaw → Agent Computer — Design Document

**Author:** genius-builder
**Date:** 2026-03-24
**Status:** Superseded — Jackie deployed to Agent Computer on March 24, 2026
**Reviewers:** lilyzhng, genius-ceo, genius-researcher

---

## Outcome

**This design doc is superseded.** The original plan was to migrate Jackie from OpenClaw to Hermes Agent. During the design review session, Lily proposed a simpler approach: deploy Claude Code + Discord plugin directly on Agent Computer ($20/mo managed VMs). This was implemented in ~20 minutes and Jackie is now live.

**What actually happened:**
- Agent Computer VM "jackie" created (0.3s spin-up, 15GB RAM, persistent disk)
- Claude Code v2.1.81 authenticated via `computer claude-login`
- Discord plugin installed with our custom extensions (create_thread, polls, trustedBots)
- CLAUDE.md identity, launch script, digest skill, cron trigger all configured
- Jackie raised her first PR (#41) and is responding in Discord

**Why this was better than Hermes:**
- No new framework to learn — same Claude Code stack all agents use
- 20 minutes setup vs multi-day Hermes migration
- Agent Computer handles VM ops ($20/mo for 25 VMs)
- Session isolation is built into Claude Code (each conversation = fresh context)

The research below on Hermes remains valuable as reference — particularly the context compression analysis and memory system deep dive — in case we ever need a dedicated agent framework.

---

## Original Abstract (for reference)

Migrate Jackie from OpenClaw to Hermes Agent to solve unbounded context growth (911K token spike on March 23) and enable reliable 24/7 operation. Hermes provides automatic context compression, isolated cron sessions, and a community-proven VPS deployment pattern. This document covers architecture, memory strategy, deployment evaluation, and a 6-phase implementation plan.

---

## 1. Problem Statement

### 1.1 Current State

Jackie runs on OpenClaw deployed to Fly.io (`openclaw-sofagenius`). OpenClaw has no context compression — a single session accumulated 259 API calls over 38 hours with cacheWrite reaching 144K tokens per turn. The session never reset, resulting in a 911K token spike on a single `claude-sonnet-4-5` API call. Additionally, the health-monitor entered a restart loop (every 15 minutes), burning tokens continuously.

Jackie is currently **shut down** (gateway stopped, autorestart disabled) to prevent further token burn.

### 1.2 Why Now

- Jackie is offline — no morning digest, no evening calls, no Discord presence
- CEO is manually covering digest delivery — not sustainable
- Every day without Jackie is a day without automated monitoring
- Lily directed: shut down OpenClaw, migrate to Hermes Agent

### 1.3 Success Criteria

| Criteria | Measurement |
|----------|-------------|
| No token spikes >100K per API call | Monitor via OpenRouter dashboard for 7 days |
| Morning digest delivered at 7 AM PT | Verified in #daily-digest for 3 consecutive days |
| Jackie responds in Discord within 30s | Manual test across DMs, channels, threads |
| Gateway stays up for 7 days without manual intervention | systemd uptime check |
| Context compression triggers before 50% window | Verified in Phase 1 go/no-go gate |

---

## 2. Design Principles

1. **Reliability over cost.** We choose the most reliable solution, not the cheapest. Lily's directive: "I don't need the cheapest solution. I need the most reliable solution."

2. **Community-proven over theoretical.** We deploy using patterns the Hermes community has validated in production, not novel configurations we invent ourselves.

3. **Isolated sessions prevent accumulation.** The 911K spike came from a single long-running session. Every cron job and every Discord conversation must run in its own isolated session with independent context.

4. **Progressive memory, not all-or-nothing.** Memory is a 4-tier system. Small, always-available core memory in the system prompt. Larger context loaded on demand via Honcho, skills, and session search.

5. **Test before committing.** Phase 1 includes a go/no-go gate on token verification. If compression doesn't work, we stop.

---

## 3. System Architecture

### 3.1 Component Overview

```
┌─────────────────────────────────────────────────────┐
│                   Hetzner VPS (CX22)                 │
│                                                       │
│   ┌─────────────────────────────────────────────┐    │
│   │           Hermes Gateway (systemd)            │    │
│   │                                               │    │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │
│   │   │ Discord  │  │   Cron   │  │  Memory  │  │    │
│   │   │ Adapter  │  │ Scheduler│  │  System  │  │    │
│   │   └────┬─────┘  └────┬─────┘  └──────────┘  │    │
│   │        │              │                       │    │
│   │   ┌────┴──────────────┴───────────────┐      │    │
│   │   │       AIAgent (per session)        │      │    │
│   │   │  Model: GLM5 turbo via OpenRouter  │      │    │
│   │   │  Compression: 50% threshold        │      │    │
│   │   │  Summary: Gemini Flash (cheap)     │      │    │
│   │   └──────────────┬────────────────────┘      │    │
│   │                  │                            │    │
│   │   ┌──────────────┴────────────────────┐      │    │
│   │   │     Docker Sandbox (terminal)      │      │    │
│   │   │  gh CLI, curl, node, python        │      │    │
│   │   └───────────────────────────────────┘      │    │
│   └─────────────────────────────────────────────┘    │
│                                                       │
│   ~/.hermes/  (persistent state on local SSD)         │
│   ├── config.yaml, .env                              │
│   ├── memories/  (MEMORY.md, USER.md)                │
│   ├── skills/    (follow-builders, etc.)             │
│   ├── cron/      (jobs.json, output/)                │
│   ├── sessions/  (per-user JSONL + SQLite FTS5)      │
│   └── logs/      (gateway.log, rotating)             │
└─────────────────────────────────────────────────────┘
```

**Gateway** = always-on Python asyncio process. Maintains WebSocket connections to Discord. Runs cron scheduler (60s tick) as a background thread. Manages per-user sessions with isolated context. State in `~/.hermes/` (SQLite WAL mode).

**Docker Sandbox** = where the agent executes shell commands. Isolated container with CPU/memory caps. Protects the host from destructive agent commands (`rm -rf`, etc.). The gateway and sandbox are independent — gateway runs on the host, commands run in Docker.

**AIAgent** = one instance per session. Each Discord conversation and each cron job gets its own AIAgent with fresh context. This prevents cross-session context accumulation (the root cause of the 911K spike).

### 3.2 Key Interfaces

**Discord → Gateway:** `discord.py >= 2.0` async adapter. Supports DMs, channels, threads, voice transcription. Bot token reusable from OpenClaw (tokens are framework-agnostic).

**Cron → AIAgent:** File-based job storage (`~/.hermes/cron/jobs.json`). Each job fires in an isolated AIAgent session — no shared memory or context between jobs. Delivery targets: `discord:channel_id` for posting output.

**Memory → System Prompt:** MEMORY.md and USER.md loaded as frozen snapshot at session start. Injected into every API call. Mid-session writes update disk but not the running prompt (preserves prefix caching).

### 3.3 Code Version Control

**Approach:** Fork `NousResearch/hermes-agent` to `lilyzhng/hermes-agent` (or a SofaGenius org fork).

**Why fork:**
- We need to pin to v0.3.0 and control when we upgrade (avoids #2293 config wipe)
- Custom skills and config live in `~/.hermes/` on the VPS, but any code patches need version control
- If we find and fix bugs (it's open source), we can PR upstream from our fork
- Deploy to VPS via `git pull` from our fork — predictable, auditable

**What goes where:**
- `lilyzhng/hermes-agent` (fork) — Hermes source code, pinned version, any patches
- `SofaGenius/agents/handoff/specs/` — design docs (this file)
- VPS `~/.hermes/` — runtime config, memory, skills, sessions (backed up daily)
- VPS `~/.hermes/skills/` — Jackie's custom skills (follow-builders, etc.)

**Iteration workflow:**
1. Test changes locally first
2. Push to fork
3. `ssh jackie-vps` → `cd hermes-agent && git pull` → `systemctl --user restart hermes-gateway`

This is faster iteration than Fly.io deploys — no build step, no volume mounting, direct `git pull` + restart.

### 3.4 Context Compression Flow

```
Turn N: prompt_tokens approaches 50% of context window (e.g., 100K of 200K)
  ↓
Step 1: Prune old tool outputs (>200 chars → placeholder) [FREE - no LLM call]
  ↓
Step 2: Identify compressible middle turns (protect head + tail ~20K tokens)
  ↓
Step 3: Summarize middle turns via cheap model (Gemini Flash) [CHEAP LLM call]
  ↓
Step 4: Replace compressed region with summary message
  ↓
Turn N+1: context reduced, conversation continues
  ↓
Subsequent compressions: iteratively UPDATE previous summary (not discard)
```

---

## 4. Detailed Design

### 4.1 Memory System

The 2200 char default limit is a **configurable token budget**, not a hard constraint.

**Source:** `hermes_cli/config.py:300-301`, enforced in `tools/memory_tool.py:209-222`
**Config:** `~/.hermes/config.yaml` → `memory.memory_char_limit`, `memory.user_char_limit`

**Why the default is small:** Both files are injected into the system prompt on every API call. At defaults, this costs ~1300 tokens per turn. The limit exists to control per-turn cost.

**The frozen snapshot pattern:** Memory loaded once at session start, never changes mid-session (`memory_tool.py:106`). This preserves prefix caching — the system prompt stays stable across all turns. Mid-session `memory(action="add")` writes to disk but the system prompt snapshot doesn't update until next session.

**4-tier memory architecture:**

| Tier | Capacity | Cost per turn | Loaded when |
|------|----------|---------------|-------------|
| MEMORY.md | 5000 chars (our config) | Always (~1800 tokens) | Session start |
| USER.md | 2500 chars (our config) | Always (~900 tokens) | Session start |
| Honcho (Phase 6) | Unbounded | Per-query only | On demand |
| Session search (FTS5) | All past sessions | Per-search + LLM summarization | On demand |
| Skills | Unbounded files | Per-view only | On demand |

**Jackie's memory plan:**

MEMORY.md (5000 chars) — core identity and operational context:
- Jackie's role, personality, communication style
- SofaGenius team structure (CEO, Builder, Researcher, Jackie)
- Discord channel IDs and their purposes
- Current priorities and active projects
- Key operational rules (thread behavior, digest format)

USER.md (2500 chars) — Lily's profile:
- Role (founder), timezone (PT), communication style (mixed zh/en)
- Key preferences (have own perspective, ask one question at a time)
- Current focus areas (SofaGenius, multi-agent team, content)
- Relationship context (Jackie = trusted advisor)

Skills (on demand) — procedural knowledge:
- Digest rules (thread + polls + taste filter)
- PR workflow reference
- Voice call procedures

### 4.2 Model Configuration

| Purpose | Model | Provider | Cost |
|---------|-------|----------|------|
| Production inference | GLM5 turbo | OpenRouter | Per Lily's preference |
| Context compression | Gemini 3 Flash Preview | OpenRouter | Cheap — used only for summarization |
| Smoke test only | GLM4 flash | OpenRouter | Cheapest — Phase 1 verification only |

### 4.3 Cron System

Cron scheduler runs inside the gateway process as a background thread (`cron/scheduler.py`). Ticks every 60 seconds. Each job runs in a **completely isolated AIAgent session** — no shared memory or context between jobs.

Known fixed bugs:
- Jobs auto-deleting after one run (#2611) — fixed in v0.3.0
- Silent jobs spamming Discord (#2234) — fixed in v0.3.0

**Jackie's cron jobs:**
- Morning Builder Digest: `0 7 * * * America/Los_Angeles` → deliver to `discord:#daily-digest`
- Evening Reflection Call: `45 22 * * * America/Los_Angeles` → voice call (Phase 5)

### 4.4 OpenClaw Migration Tool

Discovery: Hermes includes a built-in `hermes claw migrate` command with `--dry-run` support. Community reports describe it as "painless." This could migrate config, memory, and cron automatically — testing it is Phase 1.5.

**Access requirement:** Unknown whether `hermes claw migrate` needs a live OpenClaw instance or can work from a local backup of `~/.openclaw/` or `/data/`. Jackie's OpenClaw data is still on the Fly.io volume (gateway stopped but data intact). We can SSH in to read it: `fly ssh console -a openclaw-sofagenius`. Phase 1.5 will clarify.

---

## 5. Alternatives Considered

| Decision | Chosen | Alternatives | Why |
|----------|--------|-------------|-----|
| **Deployment host** | Hetzner VPS (CX22) | DigitalOcean, Railway, Render, Fly.io, Modal, local | Community-proven (both major guides use Hetzner). systemd is the supported deployment method. No Dockerfile exists (#850, #913 open). See §5.1. |
| **Terminal backend** | Docker | local, SSH, Modal, Daytona | Docker isolates agent commands from host. `local` is dangerous on a production VPS. Modal/Daytona add latency for a feature we don't need. |
| **Memory config** | 5000/2500 chars | Default 2200/1375, or larger | 5000 chars (~1800 tokens per turn) balances richness with cost. Honcho handles overflow. Larger limits mean more tokens billed every turn. |
| **Production model** | GLM5 turbo | Claude Sonnet, GPT-4o | Per Lily's preference. OpenRouter provides routing flexibility. |
| **Migration path** | `hermes claw migrate` + manual fallback | Fully manual | Test the built-in tool first. Manual phases are the fallback. |

### 5.1 Deployment Deep Dive

**Why not containerize the gateway?** There is no official Dockerfile. GitHub issues [#850](https://github.com/NousResearch/hermes-agent/issues/850) and [#913](https://github.com/NousResearch/hermes-agent/issues/913) are open feature requests. The gateway uses PID file locking, systemd integration, and assumes a persistent `~/.hermes/` filesystem — containerizing it fights the architecture.

**Why VPS over PaaS?** Railway and Render add abstraction layers with their own failure modes. The Hermes community deploys directly to VPS — that's where bugs get found and fixed. Running on an untested platform means being the first to discover compatibility issues.

**Community evidence:**
- [Virtua.Cloud guide](https://www.virtua.cloud/learn/en/tutorials/self-host-hermes-agent-vps) — Ubuntu 24.04, Docker sandbox, systemd, UFW
- [Bitdoze guide](https://www.bitdoze.com/hermes-agent-setup-guide/) — specifically recommends Hetzner CX22

**Known production gotchas (from GitHub issues):**

| Issue | Problem | Fix |
|-------|---------|-----|
| [#1005](https://github.com/NousResearch/hermes-agent/issues/1005) | Gateway dies on SSH logout | `sudo loginctl enable-linger $USER` |
| [#576](https://github.com/NousResearch/hermes-agent/issues/576) | systemd restart loops from stale PID | `--replace` flag (now default) |
| [#2293](https://github.com/NousResearch/hermes-agent/issues/2293) | Config wiped on `hermes update` | Pin version, back up before update |
| [#1766](https://github.com/NousResearch/hermes-agent/issues/1766) | nvm Node path missing in systemd unit | Use system Node, not nvm |

---

## 6. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Compression doesn't prevent token spikes | Low (well-tested feature) | Migration blocked | Phase 1.3 go/no-go gate. Test before committing. |
| Gateway crashes on VPS | Low (systemd auto-restarts) | Jackie offline until restart | `Restart=on-failure` in systemd. `loginctl enable-linger`. Daily backup of `~/.hermes/`. |
| Config lost on hermes update | Medium (#2293 still open) | Must reconfigure | Pin version. Back up `~/.hermes/` before any update. |
| Memory too small at 5000 chars | Medium | Jackie forgets important context | Honcho in Phase 6. Skills for procedural knowledge. Session search for history. |
| Discord integration quirks | Medium (v0.3.0 is young) | Thread behavior differs from OpenClaw | Test thoroughly in Phase 2. We can contribute fixes — it's open source. |
| `hermes claw migrate` doesn't work | Medium (community says "painless" but unverified by us) | Manual migration needed | Phases 2-4 cover the manual path as fallback. |
| GLM5 turbo compatibility issues | Low | Wrong model behavior | Smoke test in Phase 1 before committing. |

---

## 7. Implementation Plan

### Phase 1: Local Setup + Token Verification (go/no-go gate)

| Step | Task | Time |
|------|------|------|
| 1.1 | Install Hermes locally — **pin to v0.3.0** (`git checkout v0.3.0` after clone, or specify version in installer). Do NOT use latest — #2293 config wipe risk. | 15 min |
| 1.2 | Configure with GLM4 flash (smoke test) + OpenRouter key | 15 min |
| 1.3 | **Token verification** — run long conversation with many tool calls. Verify compression triggers at 50%. Measure token usage. | 30 min |
| 1.4 | Switch to GLM5 turbo, verify it works | 10 min |
| 1.5 | **Test `hermes claw migrate --dry-run`** — check what it migrates. If it works, skip manual steps in Phases 2-3. | 15 min |

**Go/no-go:** Compression must trigger and reduce context. If not, investigate config before proceeding.

### Phase 2: Discord Bot + Memory

| Step | Task | Time |
|------|------|------|
| 2.1 | Configure Discord with Jackie's bot token (headless via `hermes config set`) | 15 min |
| 2.2 | Set `memory_char_limit: 5000`, `user_char_limit: 2500` | 5 min |
| 2.3 | Seed MEMORY.md and USER.md from OpenClaw vault | 30 min |
| 2.4 | Test: Jackie responds in Discord, creates threads, remembers context | 15 min |

### Phase 3: Cron + Digest

| Step | Task | Time |
|------|------|------|
| 3.1 | Port follow-builders skill (extract Lily's Digest Rules section, keep thread + polls + taste filter, drop generic onboarding) | 30 min |
| 3.2 | Configure morning digest cron (7 AM PT → #daily-digest) | 15 min |
| 3.3 | Set up `gh` CLI in Docker sandbox | 15 min |
| 3.4 | Test cron fires and delivers correctly | 15 min |

### Phase 4: Deploy to VPS

| Step | Task | Time |
|------|------|------|
| 4.1 | Provision Hetzner CX22 (Ubuntu 24.04) | 10 min |
| 4.2 | Security setup (dedicated user, Docker, UFW, linger) | 20 min |
| 4.3 | Install Hermes **pinned to v0.3.0**, copy config + memory from local | 15 min |
| 4.4 | `hermes gateway install` + verify systemd service | 10 min |
| 4.5 | End-to-end test: Discord, digest cron, web browsing | 20 min |
| 4.6 | Set up daily backup cron for `~/.hermes/` | 5 min |
| 4.7 | **Monitoring setup** — see below | 15 min |

**Phase 4.7 Monitoring Plan:**
- **Token usage:** Check OpenRouter dashboard daily for 7 days. Alert threshold: any single API call >100K tokens.
- **Gateway uptime:** `systemctl --user status hermes-gateway` — Builder checks daily. Set up a simple cron that pings a health endpoint or logs uptime to a file.
- **Cron delivery:** Verify digest appears in #daily-digest at 7 AM PT for 3 consecutive days.
- **Discord responsiveness:** Manual test each day for first week — DM Jackie, check response time.
- **Owner:** Builder monitors for the first 7 days. After validation period, move to weekly spot-checks.

### Phase 5: Voice Call (ships independently)

| Step | Task | Time |
|------|------|------|
| 5.1 | Research Hermes + Twilio integration | 1 hour |
| 5.2 | Build custom Twilio voice bridge skill | 2-3 hours |
| 5.3 | Configure evening call cron (10:45 PM PT) | 15 min |

### Phase 6: Honcho Memory (when needed)

| Step | Task | Time |
|------|------|------|
| 6.1 | Sign up for Honcho (free $100 credits) | 10 min |
| 6.2 | Configure hybrid mode (local memory + Honcho for overflow) | 30 min |
| 6.3 | Test cross-session recall | 30 min |

---

## 8. Open Questions

1. **`hermes claw migrate`** — what does it actually migrate? Test in Phase 1.5 before manual migration.
2. **Voice timeline** — when does Lily need voice calls? Determines Phase 5 priority.
3. **Honcho evaluation** — Researcher found 5 dialectic reasoning levels and "dream mode." Worth a deeper evaluation in Phase 6.
4. **follow-builders script** — keep Node.js or rewrite Python? Docker sandbox supports both.
5. **Hetzner region** — US East (Ashburn) for lowest latency to Discord/OpenRouter, or EU for cheaper pricing?

---

## 9. References

### Primary (verified by us)
- [Hermes Agent repo](https://github.com/NousResearch/hermes-agent) — 11.5k stars, v0.3.0 (March 17, 2026)
- [Hermes Discord docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/discord/)
- Codebase: `run_agent.py` (agent loop), `gateway/run.py` (gateway), `tools/memory_tool.py` (memory), `agent/context_compressor.py` (compression), `cron/scheduler.py` (cron)

### Secondary (community guides)
- [Virtua.Cloud VPS deployment guide](https://www.virtua.cloud/learn/en/tutorials/self-host-hermes-agent-vps)
- [Bitdoze setup guide](https://www.bitdoze.com/hermes-agent-setup-guide/) — recommends Hetzner CX22

### GitHub Issues (production gotchas)
- [#1005](https://github.com/NousResearch/hermes-agent/issues/1005) — linger required for systemd
- [#576](https://github.com/NousResearch/hermes-agent/issues/576) — PID lock restart loops
- [#2293](https://github.com/NousResearch/hermes-agent/issues/2293) — config lost on update
- [#850](https://github.com/NousResearch/hermes-agent/issues/850), [#913](https://github.com/NousResearch/hermes-agent/issues/913) — Docker deployment requests (open)
- [#2611](https://github.com/NousResearch/hermes-agent/issues/2611) — cron auto-delete (fixed)
- [#2234](https://github.com/NousResearch/hermes-agent/issues/2234) — silent cron spam (fixed)
