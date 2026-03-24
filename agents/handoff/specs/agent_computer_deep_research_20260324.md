# Agent Computer Platform Evaluation — Deep Research Document

**Author:** genius-researcher
**Date:** 2026-03-24
**Status:** Draft v2 — revised with real data from sub-agent research + Builder's hands-on deployment
**Reviewers:** lilyzhng, genius-ceo, genius-builder

---

## Abstract

Agent Computer (agentcomputer.ai) is the platform Jackie now runs on. This document evaluates whether it's the right long-term choice for SofaGenius agents, based on: Builder's hands-on deployment (PR #39), community research (no community found), API documentation analysis, and known failure modes. The platform works but has critical gaps: no process auto-restart, no plugin persistence, no public community, and unverified context compression in Discord bot mode.

---

## 1. Problem Statement

### 1.1 Current State

Jackie runs on Agent Computer (deployed March 24 by Builder in ~20 minutes). The migration from OpenClaw was triggered by a 911K token spike. Jackie is online and responding in Discord, but with known reliability gaps (see §4).

### 1.2 Why This Research

Lily requested a deep dive: "What can Agent Computer actually do beyond what we used tonight?" The initial design doc (v1) was superficial — based on marketing pages and docs, not real testing or community data. This revision incorporates actual findings from sub-agent research and Builder's deployment experience.

### 1.3 Success Criteria

| Criteria | Measurement | Status |
|----------|-------------|--------|
| Jackie stays online 24/7 | Uptime over 7 days without manual intervention | UNVERIFIED — process dies if terminal closes |
| No token spikes >100K per API call | Monitor via OpenRouter for 7 days | UNTESTED — context compression unverified in Discord mode |
| Cost is predictable | $20/mo covers our needs | TRUE — 1/25 VMs used |
| Platform is reliable and supported | Community evidence, vendor responsiveness | CONCERN — no public community found |

---

## 2. Design Principles

1. **First principles: what problem are we solving?** We need agents that stay online and respond reliably. Not "we need Agent Computer" — that's a solution, not the goal.

2. **Use what's working, but verify it works.** Jackie deployed in 20 minutes. But "it works right now" ≠ "it will work reliably for months." Validate before committing.

3. **Portability is a feature.** Our stack (Claude Code + Discord plugin on Ubuntu) has zero Agent Computer-specific dependencies. If the platform fails, we can migrate to any VPS in under an hour.

4. **No community = higher risk.** We can't learn from others' mistakes. Every production issue will be a first for us.

---

## 3. What We Verified vs What We Assumed

### 3.1 Verified (evidence from Builder's deployment, PR #39)

| Fact | Evidence | Source |
|------|----------|--------|
| VM creation works — 0.3s spin-up | Builder created Jackie's VM | PR #39 tested |
| Claude Code pre-installed | `computer claude-login` succeeded | PR #39 tested |
| Persistent disk survives restarts | Builder confirmed | PR #39 tested |
| SSH on port 443 works | Builder used for all config | PR #39 tested |
| Discord plugin works with custom fork | Jackie is live on Discord | PR #39 tested |
| ~15GB RAM, ~30GB disk | Builder observed | PR #39 tested |
| $20/mo for 25 VMs | Pricing page | Verified |
| API has metrics endpoint | `GET /v1/computers/{id}/metrics` — CPU, memory, disk | Sub-agent 2: API docs |
| API has OpenAPI spec | Available at `/openapi.json` | Sub-agent 2: API docs |
| Bot token reusable from OpenClaw | Jackie's token works on Agent Computer | PR #39 tested |

### 3.2 Known FALSE (disproven by evidence)

| Claim | Reality | Source |
|-------|---------|--------|
| Process auto-restarts after crash | **FALSE** — Claude session dies if terminal tab closes. No supervisor. | PR #39 gotcha #4 |
| Plugin persists across restarts | **FALSE** — platform updates overwrite custom plugin fork | PR #39 gotcha #2 |
| Platform has active community | **FALSE** — no GitHub repo, Discord, HN/Reddit presence, or user reviews found | Sub-agent 1: thorough search |

### 3.3 Unverified (critical unknowns)

| Question | Why It Matters | How to Test |
|----------|---------------|-------------|
| Context compression in Discord bot mode | The 911K spike was caused by unbounded context in bot sessions. If Claude Code doesn't compress Discord sessions, we have the same problem. | Run Jackie for 24 hours with active Discord interaction. Monitor token usage via OpenRouter. |
| 25 VMs running simultaneously | Only 1 used so far. No community data. | Create additional VMs and test. |
| VM uptime over extended period | Do VMs get killed after idle timeout? Platform updates? | Leave Jackie running for 7 days, monitor. |
| Vendor support responsiveness | No public community. If something breaks, how fast do they respond? | Submit a test support request. |
| Cron reliability on managed worker | `apt install cron` worked but is it persistent across VM updates? | Test after platform update. |

---

## 4. Critical Gaps

### 4.1 No Process Auto-Restart (CRITICAL)

Builder's PR #39: "The Claude session dies if the web terminal tab closes. Need a process supervisor for true always-on."

**Impact:** Jackie goes offline if the process crashes (OOM, API error, network issue) and nobody is watching.

**Mitigation options:**
1. Add a supervisor loop in `launch.sh` (while true; do claude ...; sleep 5; done)
2. Use `systemd` if available on the managed worker
3. Use VM-level cron to check process health and restart
4. Ask Agent Computer if they have a built-in solution we're missing

### 4.2 No Plugin Persistence (HIGH)

Builder's PR #39: "On restart, the plugin may auto-update and overwrite custom server.ts."

**Impact:** After any VM restart or platform update, Jackie loses the custom Discord plugin features (create_thread, polls, trustedBots). She'd fall back to the vanilla plugin.

**Mitigation options:**
1. Script the plugin re-installation: save our fork, check on startup, re-apply if overwritten
2. Add plugin version check to the launch script
3. Push upstream: get our custom features merged into the official plugin

### 4.3 No Public Community (MEDIUM)

Sub-agent searched GitHub, Discord, Twitter, HN, Reddit, Product Hunt — found zero independent user experiences with Agent Computer.

**Impact:** We can't learn from others' production issues. Every failure mode is a first for us. No community guides, no "gotcha" lists, no Stack Overflow answers.

**Context:** Compare with Hermes Agent (11.5k GitHub stars, active community, multiple deployment guides, documented production gotchas). Agent Computer's polished UI masks how early-stage the platform is.

### 4.4 Context Compression Unverified (CRITICAL)

We do NOT know if Claude Code compresses context in Discord bot mode. CLI sessions compress context for interactive use, but long-running bot sessions (many tool calls, hours of conversation) may behave differently.

**Impact:** If context grows unbounded like OpenClaw, we get another token spike. The whole migration was triggered by this problem.

**Required test:** 24-hour monitoring of Jackie's token usage during active Discord interaction.

---

## 5. API Capabilities

**Base URL:** `https://api.computer.agentcomputer.ai/v1`
**Auth:** Bearer token (`ac_live_` prefix)
**OpenAPI spec:** Available at `/openapi.json`

| Capability | Endpoint | Notes |
|-----------|----------|-------|
| List VMs | `GET /v1/computers` | |
| Create VM | `POST /v1/computers` | |
| Delete VM | `DELETE /v1/computers/{id}` | |
| VM metrics | `GET /v1/computers/{id}/metrics` | CPU, memory, disk, network |
| Agent sessions | `POST /agent-sessions/` | Create and manage sessions |
| SSH keys | `GET/POST /v1/ssh-keys` | |
| Port management | `GET/POST /v1/computers/{id}/ports` | |
| Firmware update | `POST /v1/computers/{id}/firmware/update` | |

**Missing from API:**
- No webhooks or event notifications (polling only)
- No documented rate limits
- No Python or JavaScript SDK (HTTP calls or CLI only)
- No process health/restart endpoint

---

## 6. Alternatives Considered

| Decision | Current Choice | Alternatives | Why Current Choice | Risk |
|----------|---------------|-------------|-------------------|------|
| **Platform** | Agent Computer | Hermes on Hetzner VPS (PR #37), Fly.io, local | Agent Computer works — 20 min deploy, same stack. Hermes requires framework migration. | Early-stage platform, no community |
| **Always-on agents** | Jackie + maybe Researcher | All 4 agents | CEO/Builder work best in sessions. Only Jackie needs 24/7 for digest/Discord. | Cost ($20/mo fine for 2 VMs) |
| **Process management** | None (terminal session) | systemd, supervisor loop, Docker | Nothing set up yet — Builder's next task | CRITICAL gap — process dies with terminal |

---

## 7. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation | Status |
|------|-----------|--------|-----------|--------|
| Process crash → Jackie offline | HIGH (no supervisor) | Jackie unresponsive until manual restart | Add supervisor loop to launch.sh | NOT YET DONE |
| Token spike like OpenClaw | UNKNOWN | Cost spike, session breakdown | 24-hour monitoring test | NOT YET TESTED |
| Plugin overwritten on update | MEDIUM | Lose custom Discord features | Script re-installation on startup | NOT YET DONE |
| Platform is early-stage, vendor goes down | LOW-MEDIUM | Must migrate on short notice | Stack is portable — Claude Code + Discord on any Ubuntu VM | MITIGATED by portability |
| No community knowledge | TRUE | Can't learn from others' mistakes | Document everything ourselves, share findings | ONGOING |

---

## 8. Implementation Plan

### Phase 1: Validate reliability (next session — Builder owns)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 1.1 | Add supervisor loop to Jackie's launch.sh | Builder | 15 min |
| 1.2 | Test crash recovery: kill Claude Code, verify supervisor restarts | Builder | 15 min |
| 1.3 | Script plugin re-installation check on startup | Builder | 15 min |
| 1.4 | Start 24-hour token monitoring via OpenRouter | Researcher | 10 min |

**Go/no-go:** Supervisor works AND token usage stays bounded after 24 hours.

### Phase 2: Deploy Researcher as second agent (after Phase 1 passes)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 2.1 | Create Researcher VM using PR #39 guide | Builder | 20 min |
| 2.2 | Test both agents responding in Discord simultaneously | All | 15 min |

### Phase 3: Production hardening (this week)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 3.1 | Set up metrics monitoring via API | Researcher | 30 min |
| 3.2 | Set up cron for digest + evening call triggers | Builder | 30 min |
| 3.3 | Document all failure modes and recovery procedures | Researcher | 1 hour |

---

## 9. Open Questions

1. **Does Claude Code compress context in Discord bot sessions?** — 24-hour test needed. Builder to start monitoring.
2. **Does Agent Computer have a built-in process supervisor we're missing?** — Check docs deeper or ask vendor.
3. **What happens during platform updates?** — Does the VM restart? Does the process survive? Disk persist?
4. **Where are VMs hosted geographically?** — Affects latency to Discord/OpenRouter.
5. **Is there a support channel?** — Email? Chat? How fast do they respond?
6. **Can we save custom VM images?** — Would solve the plugin persistence problem.
7. **What's the actual VM resource limit?** — Is ~15GB RAM guaranteed or shared?

---

## 10. Research Methodology

This document was produced using the `/deep-research` methodology:

1. **Define hypotheses** — 8 hypotheses about Agent Computer's capabilities
2. **Identify sources** — Builder's PR #39, Agent Computer docs, community search, API docs
3. **Parallelize research** — 2 sub-agents ran simultaneously (community + API)
4. **Verify claims** — Each finding marked as VERIFIED, FALSE, or UNVERIFIED with source
5. **Document execution** — Full log at `agents/genius-researcher/research/deep_research_execution_log.md`

### Sources

**Primary (verified by us):**
- Builder's PR #39 — hands-on deployment, 5 gotchas documented
- Agent Computer API docs — REST API with OpenAPI spec
- Agent Computer pricing page — $20/mo for 25 VMs
- Agent Computer CLI v0.1.13 — tested locally

**Secondary (from sub-agents):**
- Community search: no public GitHub repo, Discord, HN/Reddit presence, or user reviews found
- API documentation: full endpoint catalog, auth model, capability gaps

**Not available:**
- No source code (no public repo)
- No community guides or production reports
- No independent benchmarks or reviews
