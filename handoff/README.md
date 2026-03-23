# Handoff Directory

This is the shared coordination layer between agents. Every agent reads and writes here.

## How It Works

1. **Each agent has a status file** (`{agent}-status.md`) that tracks what they're doing, what they finished, what's next, and what's blocking them.

2. **Agents read on session start.** Every agent's CLAUDE.md includes a "Session Start Routine" that reads all status files before doing anything else.

3. **Agents write on session end** (or after significant work). This ensures the next agent to wake up has full context.

4. **Specs and requests** go here too — CEO writes `spec_{topic}_{date}.md` for Builder, `research_{topic}_{date}.md` for Researcher, etc.

## Completion Status Protocol

Every task or handoff ends with one of:
- `DONE` — completed successfully
- `DONE_WITH_CONCERNS` — completed but flagging issues
- `BLOCKED` — can't proceed, need something
- `NEEDS_CONTEXT` — need more info from human or another agent

## File Naming Convention

- `{agent}-status.md` — agent's current status (updated each session)
- `spec_{topic}_{date}.md` — build spec from CEO to Builder
- `research_{topic}_{date}.md` — research request from CEO to Researcher
- `build_{topic}_{date}.md` — build update from Builder
- `findings_{topic}_{date}.md` — research report from Researcher
