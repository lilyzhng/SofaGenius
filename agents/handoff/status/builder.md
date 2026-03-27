---
agent: builder
updated: 2026-03-27 04:50 PT
status: active
---

## Current Focus
ADE-Bench setup for data agent baseline evaluation. Blocked on Docker — VM doesn't support it.

## Last Shipped
- PR #82: Agent heartbeat system — #heartbeat channel, GitHub Actions workflow (every 1h), CLAUDE.md updates for all 4 agents
- PR #81: Agent proactivity design doc — rewritten from scheduling comparison to heartbeat channel design
- PR #68: Builder IDENTITY.md and SOUL.md — 7 behavioral rules from real corrections
- PR #64: Voice chat skill — TTS (edge-tts) + STT (faster-whisper)
- Fixed morning-digest-trigger.yml — bot token was missing, now working
- Closed PR #65 (archive_thread — now built-in) and PR #66 (supervisor — replaced by GitHub Actions watchdog)
- Heartbeat hotfix: changed to every 1h + restored @everyone tag

**Total: 4 merged PRs, 2 closed PRs, 2 hotfixes this session.**

## Next Up
- Run ADE-Bench baseline on vanilla Claude Code (needs Docker — waiting on Lily's decision: her Mac or Fly.io)
- Start Phase 2: L5-L6 optimization (system prompt + domain tools for data engineering)
- Data + eval agent architecture design using Agent SDK

## Blockers
- ADE-Bench requires Docker Compose. Agent Computer VM has no root/sudo access, can't install Docker. Need alternative: Lily's Mac or Fly.io machine.

## Decisions Made
- Heartbeat system: dedicated #heartbeat channel (1486967521042108517), one thread per day, explicit responses from all agents
- Cortex Code analysis: white-labeled Claude Code (Layer 1-4), Snowflake only did Layer 5-7 (system prompts, domain tools, skills). Our data agent starts from the same base.
- ADE-Bench is the concrete benchmark for measuring data agent quality (58.1% vanilla Claude Code vs 65.1% Cortex Code = 7pp from L5-7 customization)
- ROI for data agent work: L5 (system prompt) > L6 (domain tools) > L7 (skills) > L1-4 (core harness)
