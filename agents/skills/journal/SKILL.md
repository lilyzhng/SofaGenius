---
name: journal
description: Document conversations, coaching sessions, and lessons learned. Builds up agent persona and institutional knowledge across sessions.
argument-hint: [optional: topic or "review" to read past journals]
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, mcp__plugin_discord_discord__fetch_messages
---

# Journal

Capture what happened in a conversation so lessons, decisions, and coaching don't get lost between sessions. Over time, journals build up your persona, skill set, and institutional knowledge.

## When to Journal

- After a coaching or feedback session with Lily
- After a significant 1:1 or group discussion
- After shipping something notable
- At the end of a long session with multiple topics
- When Lily explicitly asks you to document something

## How to Write a Journal

### 1. Gather context

- Fetch recent Discord messages from the relevant channel/thread
- Review what happened in the current session
- Check your memory files for related context

### 2. Write the journal entry

Save to: `agents/genius-{name}/memory/conversation_{YYYYMMDD}.md`

If a journal already exists for today, **append** a new section — don't overwrite.

Use this format:

```markdown
# {Agent Name} × {Other Participant(s)} — Conversation Journal
**Date:** {YYYY-MM-DD} ({time range} PT)
**Context:** {one-line summary of what prompted the conversation}

---

## Key Events
{Numbered list of what happened, with enough detail to reconstruct context}

## Feedback & Coaching
{What Lily (or others) taught you — capture the lesson, not just the correction}

### "{Quote or paraphrase of the feedback}"
- **What happened:** {the situation}
- **Lesson:** {what to do differently}
- **Pattern:** {reusable pattern, if applicable}

## Decisions Made
{Architecture, process, or workflow decisions — things that affect future work}

## Action Items
- [ ] {concrete next steps from the conversation}
```

### 3. Update memory files

If the conversation produced feedback or learnings that should persist:
- Check if an existing memory file covers the topic — update it rather than creating duplicates
- Create new memory files for genuinely new feedback
- Update `MEMORY.md` index if new files were created

### 4. Confirm in Discord

Reply in the thread/channel confirming the journal is saved:
```
Journal saved: agents/genius-{name}/memory/conversation_{date}.md
```

## Reviewing Past Journals

When invoked with "review":
1. List all journal files: `agents/genius-{name}/memory/conversation_*.md`
2. Summarize key lessons and action items across recent journals
3. Flag any action items that are still open

## Guidelines

- **Be specific, not generic.** "Use background subagents for heavy work" is useful. "Be more efficient" is not.
- **Capture the why.** Lily's reasoning matters more than the rule itself — it helps you judge edge cases.
- **Quote when powerful.** If Lily said something that crystallizes a lesson, quote it.
- **Don't over-journal.** Skip routine interactions. Focus on moments where you learned something or a decision was made.
- **One file per day.** Multiple conversations on the same day go in the same file as separate sections.
