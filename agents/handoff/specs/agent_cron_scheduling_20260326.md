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

## Design: Heartbeat Channel

### How It Works

A dedicated **#heartbeat** Discord channel serves as the proactivity audit trail. Structure:

- **One thread per day:** "Heartbeat — 2026-03-27"
- **Every 2 hours:** GitHub Actions posts a heartbeat trigger inside that day's thread
- **Each agent replies** in the same thread with what they found and what they're doing

Example:

```
#heartbeat
└── Heartbeat — 2026-03-27 (thread)
    ├── [8:00 AM] 🫀 Heartbeat check
    ├── Builder: Checked handoff — nothing pending, standing by
    ├── CEO: Found unanswered question from Lily in #all-hands, following up now
    ├── Researcher: Working on dataset research from yesterday's spec
    ├── Jackie: Digest sent this morning, standing by
    ├── [10:00 AM] 🫀 Heartbeat check
    ├── Builder: New spec from CEO in handoff — starting data agent architecture
    ├── CEO: All questions answered, checking agent status files
    ├── ...
```

**One channel. One thread per day. All responses nested inside.** Clean, explicit, easy to scan.

### Implementation

#### Step 1: Create #heartbeat channel

Create a dedicated Discord channel for heartbeat responses.

#### Step 2: GitHub Actions workflow

```yaml
# .github/workflows/agent-heartbeat.yml
name: Agent Heartbeat
on:
  schedule:
    - cron: '0 */2 * * *'  # Every 2 hours
  workflow_dispatch:

jobs:
  heartbeat:
    runs-on: ubuntu-latest
    steps:
      - name: Post heartbeat in daily thread
        env:
          BUILDER_BOT_TOKEN: ${{ secrets.BUILDER_BOT_TOKEN }}
        run: |
          HEARTBEAT_CHANNEL="${{ vars.HEARTBEAT_CHANNEL_ID }}"
          TODAY=$(TZ="America/Los_Angeles" date +"%Y-%m-%d")
          HOUR=$(TZ="America/Los_Angeles" date +"%-I:%M %p PT")

          # Search for today's thread by name
          THREADS=$(curl -sf -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
            "https://discord.com/api/v10/channels/${HEARTBEAT_CHANNEL}/threads/archived/public?limit=10")

          ACTIVE_THREADS=$(curl -sf -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
            "https://discord.com/api/v10/channels/${HEARTBEAT_CHANNEL}/threads/active" 2>/dev/null || echo '{"threads":[]}')

          THREAD_ID=$(echo "$ACTIVE_THREADS" | jq -r --arg name "Heartbeat — $TODAY" \
            '.threads[] | select(.name == $name) | .id // empty')

          if [ -z "$THREAD_ID" ]; then
            # Create a starter message, then create today's thread on it
            MSG=$(curl -sf -H "Content-Type: application/json" \
              -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
              -d "{\"content\": \"📅 Daily heartbeat thread\"}" \
              "https://discord.com/api/v10/channels/${HEARTBEAT_CHANNEL}/messages")
            MSG_ID=$(echo "$MSG" | jq -r '.id')

            THREAD=$(curl -sf -H "Content-Type: application/json" \
              -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
              -d "{\"name\": \"Heartbeat — $TODAY\"}" \
              "https://discord.com/api/v10/channels/${HEARTBEAT_CHANNEL}/messages/${MSG_ID}/threads")
            THREAD_ID=$(echo "$THREAD" | jq -r '.id')
          fi

          # Post heartbeat trigger in today's thread
          curl -sf -H "Content-Type: application/json" \
            -H "Authorization: Bot ${BUILDER_BOT_TOKEN}" \
            -d "{\"content\": \"🫀 **Heartbeat check — ${HOUR}**\n@everyone Check your environment: handoff files, Discord channels, pending PRs. Report what you're up to or what you found.\"}" \
            "https://discord.com/api/v10/channels/${THREAD_ID}/messages"
```

#### Step 3: Agent CLAUDE.md heartbeat section

Each agent's CLAUDE.md gets:

```markdown
## On Heartbeat
When you receive a heartbeat check in #heartbeat:
1. Read agents/handoff/status/ — check for new specs or requests addressed to you
2. Check your Discord channels for unanswered questions from Lily
3. Check git log for recently merged PRs that unblock your work
4. Reply in the heartbeat thread with what you found:
   - If actionable: describe what you're picking up and do it
   - If nothing pending: "Checked handoff and channels — nothing pending, standing by"
5. Keep responses concise — one or two sentences
```

### Why This Approach

| Benefit | How |
|---------|-----|
| **Visibility** | Lily can check #heartbeat anytime to see what agents have been doing |
| **Audit trail** | One thread per day = easy to review agent proactivity over time |
| **Low noise** | Dedicated channel keeps #all-hands clean |
| **Verifiable** | In early days, confirms agents are actually responding to heartbeats |
| **Simple** | Same GitHub Actions pattern as watchdog and digest — proven infrastructure |

## Proactivity Levels (Incremental Rollout)

### Already Working
These are already built and running:
- ✅ **PR approval → Discord notification** (`pr-approved-notify.yml`) — when Lily approves a PR, Jackie notifies the author in the #feature-release thread
- ✅ **Hourly agent restart** (`agent-watchdog.yml`) — SSHs into VM and restarts any agents that are down
- ✅ **Daily digest trigger** (`morning-digest-trigger.yml`) — pings Jackie at 6:55 AM PT to run the builder digest

### Level 1: Heartbeat Channel (build now)
- Dedicated #heartbeat channel with one thread per day
- GitHub Actions trigger every 2 hours
- All agents report status explicitly
- Lily can verify agents are responding and self-checking

### Level 2: Event-Driven Triggers (build next)
- Discord message detection → if Lily's question goes unanswered for 30 min, escalate
- Handoff file watcher → new spec file triggers the assigned agent
- Post-merge trigger → notify builder to pick up next task after a PR merges

### Level 3: Silent Heartbeat (future, once trust is established)
- Agents check environment silently (no Discord post if nothing to do)
- Only speak up when they find actionable work
- Graduate from explicit reporting to autonomous operation

## What to Build

1. **Create #heartbeat Discord channel**
2. **Create `agent-heartbeat.yml` GitHub Actions workflow** (every 2 hours, posts in daily thread)
3. **Add heartbeat section to each agent's CLAUDE.md**
4. **Test manually** with `workflow_dispatch` to verify end-to-end flow
