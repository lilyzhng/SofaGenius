---
name: active-tracker
description: Maintain a live task tracker in Discord and scratchpad. Post status in #all-hands, edit in place as tasks complete. Keeps the team informed without being asked.
argument-hint: [optional: "update" to refresh status, or "new" to create tracker]
allowed-tools: Read, Write, Edit, Bash, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__edit_message
---

# Active Task Tracker

Every agent maintains a live task tracker — a single Discord message in #all-hands that shows current status at a glance. Edit it in place as tasks complete. No one should have to ask "what are you working on?"

## Setup (one-time)

### 1. Create your scratchpad

```
agents/genius-{name}/scratchpad/active_tasks.md
```

### 2. Post your tracker in #all-hands

Post a message in #all-hands (`1485396264978878665`):

```
**{Agent Name} — Active Task Tracker** (updated {time} PT)

{current status — see format below}
```

Save this message ID — you'll edit it as tasks complete.

### 3. Create a thread on that message

Thread name: `{Agent Name} Task Tracker`

Detailed updates, briefs, and discussions go in the thread. The main message stays compact.

## Main Message Format

The main message is a **compact status snapshot**. Edit it in place — don't post new messages.

```
**{Agent Name} — Active Task Tracker** (updated {time} PT)

✅ {completed task — one line}
✅ {completed task — one line}
⏳ {in progress — one line}
🔜 {next up — one line}

**Blocked:**
- {what's blocking you — or "None"}
```

**Rules:**
- One line per task — no paragraphs
- Use emoji status: ✅ done, ⏳ in progress, 🔜 next, ❌ blocked
- Update the timestamp every time you edit
- Edit the SAME message — don't post new ones

## Thread Updates

When you complete a task, post a **brief** in the thread:

```
**Task N complete: {title}**
- What: {what you did — 1-2 sentences}
- Where: {PR number, file path, or link}
- Finding: {key result or decision — if applicable}
```

This gives detail for anyone who wants it, while the main message stays clean.

## Scratchpad Sync

Keep `agents/genius-{name}/scratchpad/active_tasks.md` in sync with your Discord tracker:

```markdown
# {Agent} — Active Tasks

## In Progress
### Task N: {title}
- [ ] subtask
- [x] completed subtask

## Completed Today
- [x] {task} — {brief result}

## Upcoming
- [ ] {next task}
```

The scratchpad persists across sessions. The Discord message is the live view.

## When to Update

- **After completing any task** — edit main message + post brief in thread
- **When starting a new task** — edit main message (move from 🔜 to ⏳)
- **When blocked** — edit main message + explain in thread
- **When picking up new work** — add to main message
- **At /hands-off and /debrief** — reference your tracker instead of writing from scratch

## Anti-Patterns

- **Don't just say "done"** — post a brief with what you did and where
- **Don't post status updates as new messages** — edit the main message
- **Don't let your tracker go stale** — if it's been >1 hour since an update, something's wrong
- **Don't wait to be asked** — update proactively after every task
- **Don't duplicate the thread in the main message** — main = compact snapshot, thread = details
