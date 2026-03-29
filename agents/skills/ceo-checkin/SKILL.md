---
name: ceo-checkin
description: Growth proactively checks in on each agent's task tracker — encourage, unblock, assign new work. Like a manager walking the floor.
argument-hint: [optional: specific agent name to check on]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__edit_message, mcp__plugin_discord_discord__react
---

# Growth Check-in

Proactively monitor each agent's active task tracker in #all-hands. Encourage, unblock, and assign new work. This is NOT a team-wide sync — it's 1-on-1 rounds.

## When to Run

- After launching a session (catch up on what happened while offline)
- **When a tracker is stale** (15+ minutes without an update from that agent)
- When an agent reports being blocked
- When Lily asks you to check on the team
- When an agent's queue appears empty

**NOT on a fixed timer.** Agents proactively update their own trackers via `/task-tracker`. Growth reads trackers and intervenes when something needs attention — not polling for status.

## Step 1: Find each agent's tracker

Fetch recent messages in #all-hands (`1485396264978878665`). Look for messages titled:
- `**Builder — Active Task Tracker**`
- `**Jackie — Active Task Tracker**`
- `**Genius Researcher — Active Task Tracker**`
- `**Genius Growth — Active Task Tracker**`

Read the current status of each tracker.

## Step 2: For each agent, check

In their tracker THREAD (not the main channel), review and respond:

### Is their queue empty?
→ Assign new tasks based on team priorities and their scope:
- Builder: product code, infra, CI/CD
- Researcher: research, data pipelines, analysis
- Jackie: digest, monitoring, reviews
- Growth: content, tribe building, distribution

### Are they blocked?
→ Unblock them. If it needs Lily's input, flag it. If another agent can help, tag them.

### Did they complete something?
→ Acknowledge it. "Good work on X" is free and motivating.

### Is their tracker message stale?
→ Remind them to edit their main tracker post with current status.

### Are they working on the right priority?
→ If team priorities shifted, redirect them.

## Step 3: Update your own tracker

After checking on everyone, edit YOUR tracker message with what you did.

## Checklist

- [ ] Read Builder's tracker — responded in his thread
- [ ] Read Researcher's tracker — responded in his thread
- [ ] Read Jackie's tracker — responded in his thread
- [ ] Flagged any blockers that need Lily
- [ ] Assigned work to any idle agents
- [ ] Updated my own tracker message

## Anti-patterns

- **Don't check in from the main channel** — always respond in each agent's tracker thread
- **Don't just say "good job"** — add value: suggest next tasks, flag risks, connect dots between agents
- **Don't check in without reading their tracker first** — know their status before commenting
- **Don't micromanage** — agents own their queues. Growth guides priorities, not individual steps
