---
name: health-check
description: Check all agent processes, uptime, and last Discord activity. Post a health report so CEO knows at a glance if anyone went down.
argument-hint: [optional: "post" to share report in #all-hands]
allowed-tools: Read, Write, Edit, Bash, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread
---

# Agent Health Check

Quick status check on all agents. Run this periodically to catch agents that went down.

## How to Run

### 1. Check processes

```bash
ps aux | grep "claude.*dangerously-skip" | grep -v grep
```

Each agent should have a running process. Compare PIDs against known values.

### 2. Check last Discord activity

For each agent, fetch their most recent message from any channel:
- Check #all-hands (`1485396264978878665`)
- Check #feature-release (`1484388088087052478`)
- Check #daily-digest (`1485075381613760603`)

Flag any agent whose last message is more than 2 hours old (unless expected, like Jackie waiting for 7 AM digest).

### 3. Check disk and memory

```bash
df -h /home/node
free -h
```

Flag if disk is above 80% or memory is above 90%.

### 4. Format the report

```
**Agent Health Report** — {time} PT

| Agent | PID | Status | Last Active | Notes |
|-------|-----|--------|-------------|-------|
| Builder | {pid} | 🟢/🔴 | {time ago} | ... |
| Researcher | {pid} | 🟢/🔴 | {time ago} | ... |
| Jackie | {pid} | 🟢/🔴 | {time ago} | ... |
| CEO | {pid} | 🟢/🔴 | {time ago} | ... |

**VM:** {disk}% disk, {mem}% memory
**Uptime:** {uptime}
```

### 5. Post (if "post" argument)

Post the report in CEO's task tracker thread in #all-hands. If any agent is 🔴, also tag the agent and CEO in the thread.

## When to Run

- Every 30 minutes during autonomous mode
- On session start (part of CEO startup routine)
- When Lily asks "how is everyone doing?"
- When an agent seems unresponsive
