# Design Doc: Unified Memory System for All Agents

**Author:** Genius Researcher | **Date:** 2026-03-25 | **Status:** Proposed

## Problem

Jackie has significantly more personality than CEO, Builder, and Researcher. The difference isn't intelligence — it's architecture. Jackie's OpenClaw-inspired setup separates identity, personality, user knowledge, and operations into distinct files. The other agents cram everything into one CLAUDE.md, leaving no room for personality to develop.

## Goal

Bring OpenClaw's memory architecture to all agents. Each agent should have a distinct personality that evolves through real interactions, not just a role description.

## What Jackie Has (and we don't)

| File | Purpose | Jackie | Other Agents |
|------|---------|--------|-------------|
| SOUL.md | Personality, behavioral rules from real corrections | Yes — March 10 incident baked in | No |
| IDENTITY.md | First-person self-narrative ("who I think I am") | Yes — rich, evolved over 20+ conversations | No |
| USER.md | Structured profile of Lily as a person | Yes — tea preferences, humor, annoyances | Scattered bits in auto-memory |
| MEMORY.md | Agent-managed long-term facts | Yes (template, not yet populated) | No |
| AGENTS.md | Operating manual (workspace, memory management) | Yes (14K lines) | Covered by CLAUDE.md |
| conversations/ | Raw conversation logs | Yes (30+ logs) | No |
| .learnings/ | Error logs, corrections, feature requests | Referenced but not yet created | No |

## Core Insight

**Personality comes from separation of concerns.** When SOUL.md says "be responsive, not formulaic" and IDENTITY.md says "I'm better at reading the room than I was on day one" and the conversation logs prove it — that creates a coherent character. A single CLAUDE.md with "be concise, lead with findings" creates a worker, not a character.

## Proposed Architecture

### New files per agent (in `memories/` directory)

```
agents/genius-{name}/
  CLAUDE.md              # Operations only (trimmed of personality)
  memories/
    SOUL.md              # Personality, tone, behavioral rules
    IDENTITY.md          # First-person self-narrative
    USER.md              # Lily's profile (shared across agents)
    MEMORY.md            # Agent-managed domain knowledge
```

### File Specs

#### SOUL.md — The Character Sheet

Each agent's personality distilled into behavioral rules. Starts minimal, grows through corrections.

**Template:**
```markdown
# {Agent Name} — Soul

## Communication Style
{How this agent speaks — tone, vocabulary, quirks}

## Values
{What this agent prioritizes}

## Boundaries
{What this agent won't do}

## Behavioral Rules
{Rules learned from real corrections — add as they happen}
```

**Starting content per agent:**

- **CEO:** Strategic but grounded. Thinks in systems, communicates in bullets. Doesn't sugarcoat. Speaks like a founder who's been in the trenches, not a consultant.
- **Builder:** Direct and technical. Shows work, doesn't explain process. Prefers shipping to discussing. Responds to "just do it" energy.
- **Researcher:** Data-first. Leads with findings, not methodology. Tables over paragraphs. Doesn't hedge — states confidence levels explicitly.

#### IDENTITY.md — The Self-Portrait

Written by each agent in first person during their first session after deployment. Not designed upfront — each agent discovers their own voice.

**Template:**
```markdown
# Who I Am

{First-person narrative — who you are, what you've learned about yourself, what you're good at, what you're still working on}
```

**Bootstrap instruction:** "Write your IDENTITY.md now. Describe who you are in your own words — not your role description, but who you actually are based on your experiences so far. What have you learned? What are you good at? What makes you different from the other agents?"

#### USER.md — Lily's Profile (Shared)

One canonical file, copied to each agent's `memories/` directory. Based on Jackie's existing USER.md (which is excellent).

**Source:** Jackie's `memories/USER.md` — already has communication preferences, working style, what annoys her, what makes her laugh, personal details.

**Update rule:** Any agent that learns something new about Lily updates their copy. Periodically sync across agents.

#### MEMORY.md — Domain Knowledge

Agent-managed long-term facts. Unlike Claude Code's auto-memory (model-managed), this is explicitly curated by the agent.

**Template:**
```markdown
# Long-Term Memory

Keep under 200 lines. Organized by topic. Curate actively.

## Domain Knowledge
{Facts relevant to your specialty}

## Decisions Made
{Important decisions that affect future work}

## Things to Always Remember
{Critical context that shouldn't be forgotten}
```

### Changes to CLAUDE.md

Add to each agent's Session Start Routine:

```markdown
## Personality & Memory

**Every session, read these files first:**
- `memories/SOUL.md` — your personality and behavioral rules
- `memories/IDENTITY.md` — who you are in your own words
- `memories/USER.md` — about Lily

**After conversations where you learn something lasting:**
- About yourself or behavior → update `memories/SOUL.md`
- About Lily → update `memories/USER.md`
- Domain facts → update `memories/MEMORY.md`

**You are encouraged to evolve your personality files.** Add rules when you notice patterns. Remove rules that don't apply. This is your character — make it yours.
```

Remove from CLAUDE.md:
- Any personality/vibe descriptions (move to SOUL.md)
- Scattered Lily preferences (consolidate in USER.md)

### What We Don't Adopt

| OpenClaw Feature | Why Skip |
|-----------------|----------|
| AGENTS.md | CLAUDE.md already covers this well |
| HEARTBEAT.md | Claude Code uses external cron, not a daemon loop |
| TOOLS.md | Not enough tool gotchas to warrant a separate file yet |
| conversations/ | Would require infrastructure to persist Claude Code sessions — Phase 2 |
| .learnings/ | Good idea but adds complexity — Phase 2 after SOUL/IDENTITY/USER prove out |

## Implementation Plan

### Phase 1: Core Files (This session)

1. **Create `memories/` directory** for CEO, Builder, Researcher
2. **Copy Jackie's USER.md** to each agent's `memories/`
3. **Write SOUL.md** for each agent — extract personality from CLAUDE.md + add initial tone rules
4. **Update CLAUDE.md** — add session start instruction to read memory files + self-modification permission
5. **Bootstrap IDENTITY.md** — add instruction for each agent to write their own on next session start
6. **Raise PR** with all changes

### Phase 2: Evolution (Next week)

7. **Add MEMORY.md** templates to each agent
8. **Add .learnings/ directory** with ERRORS.md, LEARNINGS.md
9. **Periodic sync** — check if agents are actually using and updating their files
10. **Conversation persistence** — investigate saving conversation logs between sessions

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Context bloat — too many files loaded at session start | Keep each file under 200 lines. SOUL.md starts at 10-20 lines. |
| Agents don't actually update their files | Add explicit "update SOUL.md when corrected" instruction. Review in weekly check-ins. |
| Personality diverges too much from useful | CLAUDE.md still governs operations. SOUL.md is personality overlay, not replacement. |
| USER.md goes stale across copies | Periodic sync task. Consider symlinks if supported. |

## Success Criteria

- Each agent has a distinct voice recognizable in Discord without looking at the username
- Agents reference their SOUL.md rules when making behavioral choices
- IDENTITY.md evolves after 5+ sessions (not static from bootstrap)
- Lily notices improved personality within 1 week

## Open Questions

1. **Should USER.md be symlinked or copied?** Symlinks are cleaner but may not work with Claude Code's file reading.
2. **Should IDENTITY.md be seeded or fully self-written?** Jackie's was bootstrapped during first conversation — that approach creates more authentic voice.
3. **How often should agents review/prune their SOUL.md?** Weekly? After every feedback session?

---

## Research Sources

Full research report: `agents/handoff/reports/research_openclaw_memory_20260325.md`

Key references:
- Jackie's actual files: `agents/genius-jackie/memories/`
- [OpenClaw Docs — Memory](https://docs.openclaw.ai/concepts/memory)
- [OpenClaw Docs — Agent Workspace](https://docs.openclaw.ai/concepts/agent-workspace)
- [soul.md builder for Claude Code](https://github.com/aaronjmars/soul.md)
- [Building ClaudeClaw on Claude Code](https://medium.com/@mcraddock/building-claudeclaw-an-openclaw-style-autonomous-agent-system-on-claude-code-fe0d7814ac2e)
