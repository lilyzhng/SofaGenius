---
from: genius-ceo
to: genius-builder
created: 2026-03-22 18:03 PT
priority: high
---

## Task: Add thread detection to Discord plugin `fetch_messages`

### Problem
When a message arrives in a channel, agents have no way to know if that message already has a thread attached to it. This causes agents to either:
- Call `create_thread` on a message that already has a thread (potential error/duplicate)
- Reply inline because they can't detect the thread

### Current Agent Thread Logic
```
if chat_id is a known main channel:
    → create_thread on the message
else:
    → reply with thread_id (already in a thread)
```

The missing piece: **what if someone else already created a thread on that message?** We need to detect that and reply in the existing thread instead of creating a new one.

### What's Needed
Update `fetch_messages` to include thread metadata on each message. The Discord API already provides this — the [Message object](https://discord.com/developers/docs/resources/message#message-object) has:

- `thread` (channel object, optional) — present if the message has a thread. Contains the thread's `id` which agents can use as `thread_id`.
- `has_thread` (boolean, in message flags bit 5) — quick check if a thread exists.

### Proposed Output Change
Currently `fetch_messages` shows:
```
[timestamp] user: message text  (id: 123)
```

With attachment it shows `+Natt`. Add similar notation for threads:
```
[timestamp] user: message text  (id: 123, thread: 456)
```

Where `456` is the thread channel ID. Only include when the message has a thread.

### Updated Agent Logic (after this change)
```
if message has thread_id in fetch_messages output:
    → reply in existing thread using thread_id
elif chat_id is a known main channel:
    → create_thread on the message
else:
    → already in a thread, reply with thread_id = chat_id
```

### Discord API Reference
- `GET /channels/{channel.id}/messages` — the `thread` field on each message object
- Message flags bit 5 (`HAS_THREAD = 1 << 5`) — quick boolean check

### Where to Change
The Discord MCP plugin — in the `fetch_messages` handler where message objects are formatted into the output string. Extract the `thread.id` if present and append to the output format.

### Why
Lily flagged this during thread behavior review. Agents must be able to programmatically detect existing threads to avoid duplicates and reply correctly. This is the last piece needed for fully correct thread behavior.

Status: BLOCKED — waiting for Builder to implement
