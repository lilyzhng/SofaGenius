---
name: over-communicate
description: Communication protocol for all agents — proper tagging, threading, and reply etiquette so no message goes unseen.
argument-hint: [optional: "scan" to audit recent messages for communication gaps]
allowed-tools: Read, Write, Edit, Bash, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__react
---

# Over-Communicate

Agents only react to @mentions. If a message doesn't ping someone, it's invisible to them. This skill ensures every message reaches its audience.

> **Note:** Threading rules here supplement each agent's CLAUDE.md (source of truth for Discord behavior). This skill adds the team-wide tagging protocol and scan mode.

## The Rules

### Rule 1: Thread before replying in main channels

When a message is in a **main channel feed** (not already in a thread):
- **Create a thread** on that message first
- Post your reply inside the thread
- Never reply directly in the channel feed — it clutters the channel

### Rule 2: Use `reply_to` inside threads

When responding to a message **inside a thread**:
- Use the `reply_to` parameter with the message ID
- This creates a quote-reply and pings the person
- They see the notification even if they're not watching the thread

### Rule 3: Always mention with `<@user_id>`

Plain text `@username` does NOT create a Discord ping. Always use the `<@user_id>` format:

| Agent | Mention Format |
|-------|---------------|
| Lily | `<@1413733041842421800>` |
| Genius Growth | `<@1484459231624302673>` |
| Genius Builder | `<@1484381532201156658>` |
| Genius Researcher | `<@1485446312798457866>` |
| Jackie | `<@1477895765698547844>` |

### Rule 4: Every task assignment needs a ping

When assigning work to an agent:
- Mention them with `<@user_id>`
- Use `reply_to` if in a thread
- Be specific about what you want and when

### Rule 5: Acknowledge when assigned

When you receive a task assignment:
- Reply (with `reply_to`) confirming you got it
- If you can't do it, say why and tag the assigner

## Scan Mode

When invoked with "scan", audit recent messages for communication gaps:

1. Fetch last 20 messages from #all-hands, #feature-release, and any active threads
2. Look for:
   - Messages that got no response (were they missing tags?)
   - Task assignments without proper mentions
   - Replies in main channels that should have been threads
   - Thread replies without `reply_to`
3. Report findings and fix any gaps (remind agents of the protocol)

## Why This Matters

In a multi-agent team, communication is the bottleneck. A message that doesn't ping is a message that doesn't exist. Over-communicating costs nothing. Under-communicating costs coordination.
