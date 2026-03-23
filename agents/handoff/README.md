# Handoff Directory

This is the shared coordination layer between agents. Every agent reads and writes here.

## Structure

```
handoff/
├── status/       ← agent status files (read every session)
│   ├── builder.md
│   ├── ceo.md
│   ├── researcher.md
│   └── jackie.md
├── specs/        ← build/research specs (CEO → agents)
├── reports/      ← completed work summaries (agents → CEO)
└── README.md
```

## How It Works

1. **Each agent has a status file** (`status/{agent}.md`) that tracks what they're doing, what they finished, what's next, and what's blocking them.

2. **Agents read on session start.** Every agent's CLAUDE.md includes a "Session Start Routine" that reads all status files before doing anything else.

3. **Agents write on session end** (or after significant work). This ensures the next agent to wake up has full context.

4. **Specs and requests** go in `specs/` — CEO writes `spec_{topic}_{date}.md` for Builder, `research_{topic}_{date}.md` for Researcher, etc.

5. **Reports** go in `reports/` — completed work summaries from agents back to CEO.

## Completion Status Protocol

Every task or handoff ends with one of:
- `DONE` — completed successfully
- `DONE_WITH_CONCERNS` — completed but flagging issues
- `BLOCKED` — can't proceed, need something
- `NEEDS_CONTEXT` — need more info from the founder or another agent

## File Naming Convention

- `status/{agent}.md` — agent's current status (updated each session)
- `specs/spec_{topic}_{date}.md` — build spec from CEO to Builder
- `specs/research_{topic}_{date}.md` — research request from CEO to Researcher
- `reports/build_{topic}_{date}.md` — build update from Builder
- `reports/findings_{topic}_{date}.md` — research report from Researcher
