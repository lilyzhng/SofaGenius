---
from: genius-ceo
to: genius-builder
created: 2026-03-22 17:26 PT
priority: medium
---

## Task: Add `create_thread` tool to Discord plugin

### Problem
Agents can't create threads in Discord. We can only reply inside existing threads (using `thread_id`) or do quote-replies (using `reply_to`). This means agents clutter the main channel feed with back-and-forth conversation.

### What's Needed
A new Discord plugin tool: `create_thread`

Parameters:
- `chat_id` (string, required) — the channel to create the thread in
- `message_id` (string, optional) — message to start the thread from (if creating thread from an existing message)
- `name` (string, required) — thread name
- `text` (string, optional) — initial message in the thread

Returns:
- `thread_id` — the new thread's channel ID, so the agent can continue replying in it

### Discord API Reference
- `POST /channels/{channel.id}/messages/{message.id}/threads` — create thread from message
- `POST /channels/{channel.id}/threads` — create thread without a message

### Where to Change
The Discord plugin code — wherever the other tools (reply, fetch_messages, react, etc.) are defined. Follow the same pattern.

### Why
Lily wants agents to always create threads for new topics to keep channels clean. Right now we document this rule in CLAUDE.md but can't actually follow it because the tool doesn't exist.

Status: NEEDS_CONTEXT — Builder needs to find the plugin source and add the tool
