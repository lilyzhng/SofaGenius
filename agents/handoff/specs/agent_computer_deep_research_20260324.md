# Agent Computer Platform Evaluation — Design Document

**Author:** genius-researcher
**Date:** 2026-03-24
**Status:** Draft
**Reviewers:** lilyzhng, genius-ceo, genius-builder

---

## Abstract

Evaluate Agent Computer (agentcomputer.ai) as the hosting platform for SofaGenius agents. Jackie was deployed on Agent Computer in 20 minutes on March 24 — this doc assesses whether we should scale to all agents and what capabilities/limitations the platform has beyond what we used tonight.

---

## 1. Problem Statement

### 1.1 Current State

Jackie is now running on Agent Computer after the OpenClaw shutdown (911K token spike). Builder deployed her in ~20 minutes using the managed worker pattern. Other agents (CEO, Builder, Researcher) still run locally on Lily's machine — they only exist when Lily launches a terminal session.

### 1.2 Why Now

- Jackie's successful deployment proves the platform works for our stack (Claude Code + Discord plugin)
- The Hermes migration plan (PR #37) was superseded — Agent Computer solved the same problem faster
- Lily wants a full evaluation: what can this platform actually do beyond what we used tonight?

### 1.3 Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Always-on agents (Jackie + Researcher) run on Agent Computer | Verified by deploying Researcher alongside Jackie. CEO/Builder stay local. |
| Agents survive VM restarts | Test: restart VM, verify process resumes |
| Context compression works (no 911K repeats) | Monitor token usage for 7 days |
| Cost is predictable | $20/mo covers 25 VMs — verify no hidden overage |
| DX supports fast iteration | Measure time to deploy a config change |

---

## 2. Design Principles

1. **Use what's working, not what's theoretical.** Jackie is already running on Agent Computer. Don't migrate to something else unless Agent Computer fails.

2. **Understand the platform before scaling.** We jumped on Agent Computer fast. Before putting all 4 agents on it, we need to understand limits, failure modes, and costs.

3. **Reliability over features.** We don't need every feature — we need the agents to stay up and respond.

---

## 3. System Architecture

### 3.1 What Agent Computer Provides

Based on docs, CLI exploration, and Builder's hands-on deployment:

```
┌─────────────────────────────────────────────────┐
│              Agent Computer Platform              │
│                                                   │
│   ┌───────────────────────────────────────────┐  │
│   │         Managed Worker VM                  │  │
│   │                                            │  │
│   │   Ubuntu + Python 3.12 + Node 22 + Git    │  │
│   │   Claude Code pre-installed                │  │
│   │   ~15GB RAM, ~30GB persistent disk         │  │
│   │   SSH (port 443), VNC, Web terminal        │  │
│   │   Live CPU/memory/disk metrics             │  │
│   │                                            │  │
│   │   ┌────────────┐  ┌───────────────────┐   │  │
│   │   │ Claude Code │  │ Discord Plugin    │   │  │
│   │   │ (agent)    │  │ (channels)        │   │  │
│   │   └────────────┘  └───────────────────┘   │  │
│   │                                            │  │
│   │   ~/.claude/  (persistent config)          │  │
│   │   ~/SofaGenius/  (repo clone)              │  │
│   └───────────────────────────────────────────┘  │
│                                                   │
│   × 25 VMs per $20/mo plan                       │
│   Spin-up: ~0.3 seconds                          │
│   Persistent disk survives restarts               │
│   Shared or isolated filesystem modes             │
└─────────────────────────────────────────────────┘
```

### 3.2 Access Methods

| Method | How | Use Case |
|--------|-----|----------|
| SSH | `computer ssh AGENT_NAME` or `ssh -p 443 NAME@ssh.agentcomputer.ai` | Config, debugging, file transfer |
| Web terminal | `computer open AGENT_NAME` | Quick access in browser |
| VNC desktop | Enabled per-VM | Visual desktop if needed |
| CLI | `computer agent watch/status/sessions` | Session monitoring |
| API | REST API (documented, key required) | Automation |

### 3.3 Key Interfaces

**Agent Computer → Claude Code:** Pre-installed. `computer claude-login` authenticates via browser OAuth.

**Claude Code → Discord:** Standard Discord plugin installed in `~/.claude/plugins/`. Our custom fork with create_thread/polls can be piped via SSH (no SCP — this is a known limitation).

**Cron → Agent:** No built-in cron. Builder uses an external trigger (Discord @mention via bot token + curl). Alternative: VM-level cron job that runs `claude --message "..."` directly.

---

## 4. Detailed Design

### 4.1 What We Know (verified by Builder's deployment)

| Feature | Status | Evidence |
|---------|--------|----------|
| VM creation | Works — 0.3s spin-up | Builder created Jackie's VM |
| Claude Code pre-installed | Works | `computer claude-login` succeeded |
| Persistent disk | Works — survives restarts | Confirmed by Builder |
| SSH access | Works on port 443 | Builder used for all config |
| Discord plugin | Works with custom fork | Jackie is live on Discord |
| ~15GB RAM, ~30GB disk | Confirmed | Builder observed during setup |
| 25 VMs per $20/mo | Stated on pricing page | Only 1 used so far |
| Live metrics | Docs say CPU/memory/disk available | Not yet tested by us |

### 4.2 What We Don't Know Yet (needs testing)

| Question | Why It Matters | How to Test |
|----------|---------------|-------------|
| **Process auto-restart** | If Claude Code crashes, does it auto-recover? | Kill process, observe behavior |
| **Context compression** | Agent Computer uses Claude Code, not Hermes. Does Claude Code handle context? | Run long conversation, monitor tokens |
| **Multiple agents on one plan** | Can we run CEO, Builder, Researcher, Jackie on separate VMs? | Create 4 VMs, deploy all agents |
| **VM idle behavior** | Does VM sleep when idle? Does it stay up 24/7? | Leave running, check uptime after 24h |
| **Disk persistence across updates** | Platform updates may reset filesystem | Check after platform update cycle |
| **Plugin persistence** | Builder flagged: plugin may be overwritten on restart | Test restart, verify plugin survives |
| **Cron scheduling** | No built-in cron. External trigger works but is fragile. | Test VM-level crontab as alternative |
| **Monitoring/alerting** | Can we get alerts if a VM goes down? | Check dashboard, API |
| **Rate limits** | API calls, SSH connections — any limits? | Stress test |
| **Data sovereignty** | Where are VMs hosted? Important for Lily's data. | Check docs or ask vendor |

### 4.3 Context Compression — Critical Unknown (UNVERIFIED)

Agent Computer runs **Claude Code**, not Hermes Agent. Claude Code compresses conversation context for interactive CLI use, but **we do not know if it compresses context in Discord bot mode** (long-running sessions with many tool calls).

**This is unverified.** The 911K spike happened because OpenClaw had no compression in a long-running bot session. We cannot assume Claude Code handles this — Discord bot sessions behave differently from interactive CLI sessions.

**Required: 24-hour monitoring test before declaring this solved.**
- Run Jackie on Agent Computer for 24 hours with active Discord interaction
- Monitor token usage via OpenRouter dashboard
- Check: does context grow unbounded, or does compression trigger?
- If context grows unbounded → we have the same problem as OpenClaw and need a different solution

**This test is the Phase 1.3 go/no-go gate.** Do not scale to additional agents until this passes.

### 4.4 Gotchas Discovered During Jackie's Setup (from Builder's PR #39)

| Gotcha | Description | Workaround |
|--------|-------------|-----------|
| No SCP | Can't use `scp` to copy files — only SSH with pipe | `cat file | ssh ... 'cat > target'` |
| Self-mention | Bot can't @mention itself to trigger actions | Use different bot token for triggers |
| SSH quoting | Complex commands need careful quoting through SSH | Use heredoc or script files |
| Plugin auto-update | Plugin may be overwritten on platform update | Need to re-apply custom fork after updates |

---

## 5. Alternatives Considered

| Decision | Chosen | Alternatives | Why |
|----------|--------|-------------|-----|
| **Platform** | Agent Computer | Hermes on Hetzner VPS, Fly.io, local | Agent Computer works — Jackie deployed in 20 min. Same Claude Code stack we already use. Hermes would require framework migration. |
| **Multiple VMs vs one** | Separate VM per agent | All agents on one VM | Isolation — one agent crashing doesn't take down others. 25 VMs included in $20/mo plan. |
| **Cron** | External Discord trigger | VM-level crontab, GitHub Actions | Discord trigger works but is fragile (needs another bot token). VM crontab is more reliable — **recommend testing this**. |

---

## 6. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Plugin overwritten on platform update | Medium | Jackie loses Discord access until re-applied | Monitor for updates, script the plugin install, alert if plugin missing |
| No process auto-restart | Medium | Claude Code crashes, Jackie goes offline | Test crash recovery. If no auto-restart, add supervisor loop in launch.sh |
| Token spikes like OpenClaw | Low (Claude Code has compression) | Cost spike, session breakdown | Monitor via OpenRouter dashboard. Set up token budget alerts. |
| Vendor lock-in | Medium | If Agent Computer shuts down or raises prices | Our agents are Claude Code + Discord plugin — portable to any Ubuntu VM. Migration = copy `~/.claude/` + clone repo. |
| Platform is new/unproven | Medium | Unexpected downtime, bugs | We're early adopters. Keep rollback plan (Hetzner VPS from PR #37). |
| 30GB disk fills up | Low | Agent can't write files | Monitor disk usage. Clean up old sessions periodically. |

---

## 7. Implementation Plan

### Phase 1: Validate Jackie's deployment (next 1 hour)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 1.1 | Test process crash recovery — kill Claude Code, see if it restarts | Builder | 15 min |
| 1.2 | Test plugin persistence — restart VM, verify Discord plugin survives | Builder | 15 min |
| 1.3 | Run long conversation to verify context compression | Researcher | 30 min |

**Go/no-go:** All 3 tests pass → proceed to Phase 2.

### Phase 2: Deploy Researcher as second always-on agent (next 1 hour)

Only Jackie and Researcher are candidates for always-on Agent Computer VMs. CEO and Builder stay local/session-based per Lily's direction — they work best when launched during active sessions, not running 24/7.

| Step | Task | Owner | Time |
|------|------|-------|------|
| 2.1 | Create VM for Researcher | Builder | 10 min |
| 2.2 | Deploy Researcher using PR #39 guide | Builder | 20 min |
| 2.3 | Test Jackie + Researcher responding in Discord simultaneously | All | 15 min |

**Go/no-go:** Both agents respond correctly, no interference. CEO/Builder deployment deferred — evaluate later if needed.

### Phase 3: Production hardening (today)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 3.1 | Set up VM-level crontab for digest + evening call triggers | Builder | 30 min |
| 3.2 | Add supervisor loop for auto-restart if needed | Builder | 30 min |
| 3.3 | Set up monitoring alerts (token usage, uptime) | Researcher | 30 min |

### Phase 4: Evaluate platform capabilities (this week)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 4.1 | Test shared filesystem mode between agent VMs | Researcher | 30 min |
| 4.2 | Test Agent Computer API for automation | Researcher | 30 min |
| 4.3 | Evaluate ACP (Agent Computer Protocol) for inter-agent communication | Researcher | 1 hour |
| 4.4 | Document findings in follow-up report | Researcher | 30 min |

---

## 8. Open Questions

1. **Process auto-restart** — does Agent Computer's managed worker handle crash recovery? Builder to test in Phase 1.1.
2. **Plugin persistence** — does the Discord plugin survive VM restarts and platform updates? Builder to test in Phase 1.2.
3. **VM-level crontab** — can we install and run crontab on managed workers? Or is it restricted? Builder to test.
4. **Data location** — where are VMs hosted? US? EU? Matters for latency to Discord/OpenRouter.
5. **ACP protocol** — "Agent Computer Protocol" is mentioned in docs. What does it enable for inter-agent communication?
6. **Image customization** — can we save a custom image with our fork of the Discord plugin pre-installed? Docs mention "image sources" but details are thin.
7. **Shared filesystem** — docs mention shared home at `/home/node`. Can agents share files directly? This could replace git-based handoffs.

---

## 9. References

### Primary (verified by us)
- https://www.agentcomputer.ai/ — Product page
- https://www.agentcomputer.ai/pricing — $20/mo for 25 VMs
- https://www.agentcomputer.ai/docs — Documentation
- https://www.agentcomputer.ai/docs/machines — Machine management
- https://www.agentcomputer.ai/docs/agents — Agent sessions
- Builder's setup guide (PR #39) — tested end-to-end with Jackie
- Agent Computer CLI v0.1.13 — explored locally

### Related (from earlier research)
- Agent Computer persistent sandbox research (PR #30) — initial landscape evaluation
- Jackie migration spec (PR #33) — requirements that Agent Computer now fulfills
- Hermes migration design doc (PR #37) — superseded by Agent Computer for Jackie, useful reference for framework comparison
