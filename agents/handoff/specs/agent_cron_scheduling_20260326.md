# Agent Proactivity — Design Doc

## Problem

Agents are **reactive** — they only act when tagged in Discord or triggered by an external cron. Lily has to drive everything: reminding agents to check tasks, following up on work, initiating reviews. This defeats the purpose of having autonomous agents.

**What we need:** Agents that self-initiate. They check for pending work, follow up on stale tasks, notice unanswered questions, and act without being prompted.

## What's Already Solved: External Scheduling

GitHub Actions handles reliable, time-based triggers:
- **agent-watchdog.yml** — hourly, restarts agents if down
- **morning-digest-trigger.yml** — daily 6:55 AM PT, tells Jackie to run digest

These are fire-and-forget alarm clocks. They work. No changes needed here.

## What's Missing: Internal Proactivity

External cron can say "do X at time Y." It can't say "notice that there's a pending spec and start working on it" or "realize Lily asked a question 2 hours ago and nobody answered."

Proactive behavior requires agents to **periodically assess their environment and decide what to do.** This is a heartbeat + judgment loop, not a task scheduler.

### Examples of Proactive Behavior

| Agent | Proactive Action | Trigger |
|-------|-----------------|---------|
| Builder | Check handoff/specs for new build requests, start working | Every 2-3 hours |
| Builder | Notice a PR has been approved, start next task | After PR events |
| CEO | Scan Discord for unanswered Lily questions, follow up | Every 1-2 hours |
| CEO | Check agent status files, do a check-in round | Every 3-4 hours |
| Researcher | See a new research request in handoff, start researching | Every 2-3 hours |
| Jackie | Check if digest was actually sent, retry if not | After scheduled digest time |

## Design: Agent Heartbeat Loop

### Architecture

Each agent gets an internal heartbeat — a periodic self-check that runs alongside normal operation. On each heartbeat, the agent:

1. **Reads its environment** — handoff files, Discord channels, task tracker, git status
2. **Identifies actionable items** — new specs, unanswered questions, stale tasks, completed dependencies
3. **Decides whether to act** — not every heartbeat produces work; judgment matters
4. **Acts or stays quiet** — do the work, or log "nothing to do" and wait

### Implementation: GitHub Actions + Agent Prompt

The simplest approach that works today — no new infrastructure needed.

**How it works:**
1. A GitHub Actions cron fires every 1 hour
2. It SSHs into the VM and sends a "heartbeat prompt" to each agent's Discord DM or a dedicated channel
3. The prompt tells the agent: "Check your environment and decide if there's anything you should be doing"
4. The agent reads handoff files, checks Discord, and either acts or responds "nothing pending"

```yaml
# .github/workflows/agent-heartbeat.yml
name: Agent Heartbeat
on:
  schedule:
    - cron: '0 * * * *'  # Every 1 hour
  workflow_dispatch:

jobs:
  heartbeat:
    runs-on: ubuntu-latest
    steps:
      - name: Ping agents to self-check
        env:
          BUILDER_BOT_TOKEN: ${{ secrets.BUILDER_BOT_TOKEN }}
        run: |
          ALL_HANDS="1485396264978878665"

          curl -sf -H "Content-Type: application/json" \
            -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
            -d '{"content": "🫀 **Heartbeat check.** All agents: read your handoff files, check for pending work, and act on anything outstanding. Report status in-thread."}' \
            "https://discord.com/api/v10/channels/${ALL_HANDS}/messages"
```

### Agent Heartbeat Behavior (per agent CLAUDE.md)

Each agent's CLAUDE.md gets a heartbeat section:

```markdown
## On Heartbeat
When you receive a heartbeat prompt:
1. Read agents/handoff/status/ — check for new specs or requests
2. Check your Discord channels for unanswered questions from Lily
3. Check git log for recently merged PRs that unblock your work
4. If anything is actionable, start working on it immediately
5. If nothing pending, reply briefly: "Nothing pending, standing by"
```

### Why This Over a Custom Daemon

| Approach | Pros | Cons |
|----------|------|------|
| GitHub Actions heartbeat | Zero new code, already proven, easy to adjust frequency | 1-hour minimum granularity (GitHub cron), requires Discord bot token |
| On-VM Node.js loop (croner) | Sub-minute granularity, can access local state directly | Another process to keep alive, coupling concerns |
| On-VM bash loop | Simplest possible implementation | Fragile, no error handling, resource waste |

**Recommendation:** Start with GitHub Actions heartbeat. It's the same pattern as our working watchdog and digest triggers. If we need faster response times later, add a croner-based loop on the VM.

## Proactivity Levels (Incremental Rollout)

### Already Working
These are already built and running:
- ✅ **PR approval → Discord notification** (`pr-approved-notify.yml`) — when Lily approves a PR, Jackie notifies the author in the #feature-release thread
- ✅ **Hourly agent restart** (`agent-watchdog.yml`) — SSHs into VM and restarts any agents that are down
- ✅ **Daily digest trigger** (`morning-digest-trigger.yml`) — pings Jackie at 6:55 AM PT to run the builder digest

### Level 1: Scheduled Self-Check (build this now)
- GitHub Actions heartbeat every 1 hour
- Agents check handoff files and Discord
- Act on anything obvious

### Level 2: Event-Driven Triggers (build next)
- Discord message detection → if Lily's question goes unanswered for 30 min, escalate
- Handoff file watcher → new spec file triggers the assigned agent
- Post-merge trigger → notify builder to pick up next task after a PR merges

### Level 3: Autonomous Planning (future)
- Agents maintain their own task queues
- End-of-session: agent writes "next session plan" to handoff
- Start-of-session: agent reads plan and executes without prompting
- Weekly self-review: agent evaluates its own output quality

## Open Questions

1. **Heartbeat frequency** — 2 hours feels right to start. Too frequent = noisy, too infrequent = Lily still waiting.
2. **Quiet hours** — should heartbeats pause overnight (11 PM - 7 AM PT)?
3. **Channel noise** — heartbeat responses in #all-hands could get spammy. Dedicated #heartbeat channel?
4. **Cost** — each heartbeat wakes up agents and uses API tokens. At 1-hour intervals this is ~24 checks/day per agent. Acceptable?
