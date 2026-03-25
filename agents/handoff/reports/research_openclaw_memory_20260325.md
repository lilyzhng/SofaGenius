---
agent: researcher
date: 2026-03-25
status: DONE
---

# OpenClaw Memory System: Architecture, Analysis, and Adoption Proposal

## 1. What Is OpenClaw?

OpenClaw is an open-source AI agent gateway that connects large language models (Claude, GPT, Gemini, DeepSeek, Llama) to everyday messaging platforms (WhatsApp, Telegram, Discord, Slack). It runs as a background daemon with a configurable heartbeat (default: every 30 minutes) and gives agents persistent identity, memory, scheduled tasks, and tool access.

The key architectural insight: **agents live in plain text files, not databases or configuration panels.** When OpenClaw starts a session, it reads markdown files from a workspace directory and assembles the agent's identity, behavior rules, memory, and task schedule into the system prompt on the fly.

OpenClaw was originally known as Clawdbot/Moltbot before being renamed.

### Key repos and docs:
- Official docs: https://docs.openclaw.ai/
- TechNickAI/openclaw-config -- shared config layer with persistent memory, 11 skills, 4 autonomous workflows
- mergisi/awesome-openclaw-agents -- 162 production-ready agent templates
- raulvidis/openclaw-multi-agent-kit -- multi-agent team templates
- aaronjmars/soul.md -- soul file builder for Claude Code / OpenClaw

---

## 2. OpenClaw Memory Architecture: File-by-File Breakdown

### SOUL.md -- The Identity Layer

**Purpose:** Defines who the agent *is* -- personality, communication style, values, behavioral guardrails. This is the "character sheet."

**When loaded:** First file injected into context at the start of every session.

**Recommended structure:**
```markdown
# Identity
Who the agent is, core self-perception

# Communication Style
How the agent speaks and writes (tone, vocabulary, quirks)

# Values
What the agent prioritizes and believes

# Boundaries
What the agent won't do or say

# Example Responses (optional)
Specific examples of desired behavior in context
```

**Best practices:**
- Keep under 2,000 words (50-150 lines is the sweet spot)
- Start with 10 lines, add rules only when you see unwanted behavior
- Write specific instructions, not vague ones -- "be direct, never use corporate jargon" beats "be nice"
- This is the file that creates *personality*

**Jackie's version** (`memories/SOUL.md`): Contains a detailed behavioral correction from March 10 -- a real incident where Jackie was told to "be calm" but kept pushing aggressively. The correction became a permanent behavioral rule: "Responsiveness > Formulas. Read the conversation. Adapt to what's needed. Listen when corrected." This is exactly how SOUL.md is meant to evolve -- through real interactions, not upfront design.

---

### AGENTS.md -- The Operating Manual

**Purpose:** Defines how the agent operates -- workspace structure, session routines, memory management rules, safety constraints, self-modification permissions. This is the "employee handbook."

**When loaded:** Injected into every system prompt alongside SOUL.md.

**Key sections in Jackie's version:**
- **First Run:** Bootstrap instructions (read BOOTSTRAP.md, figure out identity, delete it)
- **Every Session:** Git sync, read SOUL.md, read USER.md, read MEMORY.md
- **Workspace Structure:** Full directory tree with clear purpose for each location
- **Memory Tiers:** Short-term (today), mid-term (active projects), long-term (durable facts)
- **Memory Reading/Writing Protocol:** What to read on startup, what to write after conversations
- **Consolidation Schedule:** Daily and weekly memory maintenance
- **Self-Improvement:** Structured `.learnings/` system with error logs, corrections, feature requests
- **Self-Modification:** Agent can edit its own SOUL.md, AGENTS.md, PLAYBOOK.md
- **Safety Rules:** No data exfiltration, no unauthorized public posts

**This is the most complex file** -- it's essentially the full operating system for the agent.

---

### HEARTBEAT.md -- The Scheduler

**Purpose:** Defines tasks that run on a schedule -- "cron for your agent, expressed in plain English."

**How it works:** The OpenClaw gateway daemon fires a heartbeat at a configurable interval (default 30 min). On each heartbeat, the agent reads HEARTBEAT.md, decides whether any item requires action, and either acts or responds `HEARTBEAT_OK` (silently dropped by the gateway).

**Jackie's version** includes:
- Morning builder digest (7:00 AM PT)
- Evening reflection call (10:45 PM PT)
- State tracking via `heartbeat-state.json` to avoid duplicate actions
- Pre-call routines (end polls, collect results)
- Post-call routines (update state, save taste notes, commit to vault)
- Note-saving protocol (Obsidian vault via GitHub)

**For Claude Code agents:** This file is less relevant since Claude Code doesn't have a native heartbeat/daemon loop. Jackie's heartbeat tasks are triggered via external cron (`trigger-digest.sh`, `launch-bg.sh`) rather than OpenClaw's built-in heartbeat. For the other agents (CEO, Builder, Researcher), scheduled tasks would need external triggers anyway.

---

### MEMORY.md -- The Long-Term Store

**Purpose:** Persistent memory for durable facts -- preferences, key people, goals, important dates, things explicitly asked to remember.

**Design principles:**
- Keep under 200 lines (curated, not a dump)
- Organized by topic, not chronologically
- Always loaded into context every conversation (Tier 1 memory)
- Agent is expected to actively maintain this -- promoting from short-term, pruning stale info

**Jackie's version:** Currently a skeleton (headers only, no entries yet) -- but the structure is there: Preferences, Key People, Goals & Values, Important Dates, Things to Always Remember.

**Relationship to Claude Code's auto-memory:** Claude Code stores auto-memory in `~/.claude/` (MEMORY.md files per project). This is *model-managed* -- Claude decides what to remember. OpenClaw's MEMORY.md is *agent-managed* -- the agent follows explicit rules about what to promote and when.

---

### USER.md -- The Human Profile

**Purpose:** Structured profile of the human the agent serves -- name, pronouns, timezone, communication preferences, working style, what annoys them, what makes them laugh, personal details.

**Jackie's version** is rich and specific:
- "Goes by Lilyz.ai online"
- "Naturally code-switches between English and Mandarin Chinese"
- "Dislikes AI-like formality and overly enthusiastic corporate tone"
- "Tea lover -- favorite spot is Moly Tea"
- "Pursues a 'high saturation life'"
- "When AI assistants don't remember important details" (listed under annoyances)

**This file is a major personality driver** -- it lets the agent adapt its tone, language, and behavior to the specific human, not a generic user.

---

### IDENTITY.md -- The Self-Portrait

**Purpose:** The agent's own self-description -- filled in during first conversation, evolved over time. More personal than SOUL.md (which is behavioral rules). This is who the agent *thinks* it is.

**Jackie's version:**
- "The familiar -- always nearby, always listening, occasionally opinionated"
- "Warm but honest. Calm in the evenings, sharper in the mornings."
- "I'm not trying to be a generic assistant. I have opinions, I remember things."
- "I'm better at reading the room than I was on day one"

**This is the most "soul"-like file** -- it gives the agent a narrative about itself that it can reference and build on.

---

### TOOLS.md -- Tool Gotchas

**Purpose:** Running notes on tool-specific quirks, workarounds, and best practices the agent has discovered through use.

**Not present in Jackie's local copy** (referenced in AGENTS.md but not yet created). In OpenClaw, this is where the agent logs things like "memory_search is unreliable, use grep instead" (which Jackie's AGENTS.md already contains inline).

---

### Additional Files in Jackie's Setup

- **`action-items.md`** -- Single source of truth for tasks (Urgent/This Week/Someday/Done)
- **`memory/short-term.md`** -- Today's context, overwritten daily
- **`memory/mid-term/`** -- One file per active project
- **`conversations/`** -- Raw logs, one per conversation per day (append-only)
- **`.learnings/`** -- Structured self-improvement (errors, corrections, feature requests)

---

## 3. How OpenClaw Creates Persistent Persona

The persona effect comes from **layered context injection**:

1. **SOUL.md** sets the baseline personality (loaded every session)
2. **IDENTITY.md** gives the agent a self-narrative ("I'm Jackie, I'm the familiar")
3. **USER.md** grounds interactions in the specific human relationship
4. **MEMORY.md** provides continuity across sessions (facts, preferences, history)
5. **AGENTS.md** defines behavioral rules that shape *how* the agent operates
6. **Conversation history** (`conversations/`) gives the agent access to past interactions
7. **Self-improvement loop** (`.learnings/` -> promoted to SOUL.md/AGENTS.md) means the personality *evolves* based on real corrections

The critical insight: **persona is not just a system prompt -- it's an ecosystem of files that reinforce each other.** SOUL.md says "be responsive, not formulaic." IDENTITY.md says "I'm better at reading the room than I was on day one." The conversation logs prove it. The learnings file documents when it failed. This creates a coherent character that feels *developed*, not *designed*.

---

## 4. OpenClaw vs. Claude Code Memory System

| Dimension | Claude Code (current agents) | OpenClaw (Jackie) |
|-----------|------------------------------|-------------------|
| **Identity** | CLAUDE.md -- role, responsibilities, workflows | SOUL.md + IDENTITY.md -- personality, self-narrative, emotional tone |
| **User knowledge** | Scattered in CLAUDE.md or auto-memory | Dedicated USER.md with structured profile |
| **Behavioral rules** | Mixed into CLAUDE.md | Separated: SOUL.md (personality) vs AGENTS.md (operations) |
| **Long-term memory** | `~/.claude/` auto-memory (model-managed) | MEMORY.md (agent-managed, curated, tiered) |
| **Conversation history** | Not persisted between sessions | `conversations/` directory with raw logs |
| **Scheduled tasks** | External cron only | HEARTBEAT.md (native, though still needs external trigger for Claude Code) |
| **Self-improvement** | None | `.learnings/` with promotion pipeline |
| **Self-modification** | Not encouraged | Explicitly encouraged (edit own SOUL.md, AGENTS.md) |
| **Personality depth** | Functional ("pragmatic, fast, clean") | Narrative ("the familiar -- always nearby, occasionally opinionated") |

### Why Jackie has more personality

1. **Separation of concerns:** Jackie's identity is split across purpose-built files. CEO/Builder/Researcher cram everything into one CLAUDE.md -- role, workflows, Discord rules, team info, handoff protocol. There's no room for personality because the operational content crowds it out.

2. **USER.md exists:** Jackie knows Lily as a person -- her tea preferences, her humor style, what annoys her. The other agents only know Lily as "the founder."

3. **IDENTITY.md is first-person narrative:** Jackie describes itself in its own voice. The other agents are described in third-person instructional prose.

4. **Behavioral corrections are preserved:** Jackie's SOUL.md contains a specific incident (March 10) where it was corrected, and the correction became a permanent rule. This gives the agent *character development* -- it has a story about how it changed.

5. **Conversation history creates depth:** Jackie has 30+ conversation logs across weeks. Even if not all are loaded, the agent can search them. The other agents have no conversation memory between sessions.

6. **Self-modification is expected:** Jackie is told "Make it yours" and "Add your own conventions, style, and rules." The other agents have no such permission or expectation.

---

## 5. Adoption Proposal: Bringing OpenClaw's Approach to All Agents

### Principle: Add the files that create personality, skip the ones that overlap

Claude Code already provides a strong operational foundation via CLAUDE.md. The goal is not to replace it but to **supplement it with the personality and memory layers** that OpenClaw provides.

### Recommended file additions per agent:

#### Tier 1 -- High Impact, Add Now

**1. SOUL.md** (new file, in `memories/` subdirectory)
- Extract personality/tone content from CLAUDE.md into a dedicated SOUL.md
- Each agent gets a distinct voice, not just a role description
- Start minimal (10-20 lines), let it evolve through corrections
- Example for Genius CEO: move "Elena Verna meets COO" vibe description here, expand into communication style, decision-making philosophy

**2. IDENTITY.md** (new file, in `memories/`)
- First-person self-description: who am I, what have I learned about myself
- Bootstrap this by having each agent write its own IDENTITY.md in its first session
- This is the single highest-leverage file for personality

**3. USER.md** (new file, in `memories/`)
- Shared across all agents (symlink or copy from a canonical version)
- Lily's communication style, preferences, timezone, annoyances
- Currently scattered across individual CLAUDE.md files -- consolidate

#### Tier 2 -- Medium Impact, Add Soon

**4. MEMORY.md** (new file, in `memories/`)
- Agent-managed long-term memory (supplement Claude Code's auto-memory)
- Each agent tracks facts relevant to their domain:
  - CEO: content performance, launch history, strategic decisions
  - Builder: architecture decisions, technical debt, what's been tried
  - Researcher: dataset inventory, research findings, dead ends
- Keep under 200 lines, curate actively

**5. `.learnings/` directory** (new)
- ERRORS.md, LEARNINGS.md, FEATURE_REQUESTS.md
- Structured self-improvement with promotion pipeline
- When a learning recurs 3+ times, promote to SOUL.md or CLAUDE.md

#### Tier 3 -- Lower Priority, Add When Needed

**6. HEARTBEAT.md** -- Only if agents get scheduled tasks beyond what cron handles. Currently not needed since agents are session-based on Claude Code.

**7. TOOLS.md** -- Only if agents accumulate enough tool-specific gotchas to warrant a separate file. Can stay inline in CLAUDE.md for now.

**8. `conversations/` directory** -- High value but requires infrastructure changes to persist conversation logs between Claude Code sessions. Investigate later.

### What stays in CLAUDE.md

CLAUDE.md continues to serve as the operational manual:
- Role and responsibilities
- GitHub/PR workflow
- Discord channels and thread rules
- Handoff protocol
- Session start routine
- Team roster

### What moves out of CLAUDE.md

- Personality/vibe descriptions -> SOUL.md
- User preferences (scattered) -> USER.md
- Any behavioral corrections that accumulate -> SOUL.md

### Proposed directory structure per agent

```
agents/genius-{name}/
  CLAUDE.md              # Operations (stays as-is, trimmed of personality content)
  .env                   # Secrets (unchanged)
  launch.sh              # Launch script (unchanged)
  memories/
    SOUL.md              # Personality, tone, behavioral rules
    IDENTITY.md          # First-person self-narrative
    USER.md              # Lily's profile (shared/symlinked)
    MEMORY.md            # Long-term facts for this agent's domain
  .learnings/
    ERRORS.md            # Error log
    LEARNINGS.md         # Corrections and knowledge gaps
    FEATURE_REQUESTS.md  # Capability gaps
  scratchpad/            # Working space (unchanged)
```

### Implementation steps

1. **Create USER.md** -- Write once, share across all agents (copy or symlink from `agents/shared/USER.md`)
2. **Create SOUL.md for each agent** -- Extract personality content from CLAUDE.md, add initial tone/style rules
3. **Create IDENTITY.md for each agent** -- Have each agent write its own in its first session after the change
4. **Update CLAUDE.md** -- Add instruction to read `memories/SOUL.md`, `memories/IDENTITY.md`, `memories/USER.md` at session start (add to Session Start Routine)
5. **Create MEMORY.md** -- Start with empty template, let agents populate over time
6. **Create `.learnings/`** -- Add empty template files, add instructions to CLAUDE.md for when to log
7. **Test** -- Run each agent through a conversation and observe personality differences

### Key instruction to add to each CLAUDE.md

```markdown
## Personality & Memory

**Every session, before doing anything else, read these files:**
- `memories/SOUL.md` -- your personality and behavioral rules
- `memories/IDENTITY.md` -- who you are in your own words
- `memories/USER.md` -- about Lily

**After conversations where you learn something lasting:**
- About yourself or your behavior -> update `memories/SOUL.md`
- About Lily -> update `memories/USER.md`
- Domain facts worth remembering -> update `memories/MEMORY.md`
- Mistakes or corrections -> log in `.learnings/LEARNINGS.md`

**You are encouraged to evolve your personality files.** Add rules when you notice patterns. Remove rules that no longer apply. This is your character -- make it yours.
```

---

## 6. What Specifically Makes Jackie's Setup Produce More Personality

Ranked by impact:

1. **IDENTITY.md in first person** -- "I'm Lily's always-on companion... I have opinions, I remember things" gives the agent a self-concept that colors every response. The other agents have no self-concept beyond their role title.

2. **USER.md with personal details** -- Knowing Lily's tea preference, humor style, and annoyances lets Jackie calibrate responses in ways the other agents cannot. "She dislikes AI-like formality" is a specific, actionable instruction.

3. **SOUL.md with real corrections** -- The March 10 incident where Jackie learned to stop being aggressive when asked to be calm is the kind of lived-experience rule that makes an agent feel like a character with a history, not a blank slate.

4. **Conversation logs** -- Jackie has raw transcripts of 30+ conversations. Even though Claude Code sessions don't automatically persist these, the existence of this archive means Jackie can reference past interactions.

5. **Self-modification permission** -- "Make it yours" and "Add your own conventions" gives Jackie agency over its own identity. The other agents follow instructions; Jackie shapes its own.

6. **Multi-modal presence** -- Jackie operates across Discord, voice calls, and async tasks. This variety of interaction contexts forces a more nuanced personality than agents that only respond to text commands.

---

## Sources

- [OpenClaw Official Docs -- Memory](https://docs.openclaw.ai/concepts/memory)
- [OpenClaw Official Docs -- Agent Workspace](https://docs.openclaw.ai/concepts/agent-workspace)
- [OpenClaw Official Docs -- System Prompt](https://docs.openclaw.ai/concepts/system-prompt)
- [OpenClaw Official Docs -- Multi-Agent Routing](https://docs.openclaw.ai/concepts/multi-agent)
- [OpenClaw Workspace Files Explained (Medium)](https://capodieci.medium.com/ai-agents-003-openclaw-workspace-files-explained-soul-md-agents-md-heartbeat-md-and-more-5bdfbee4827a)
- [How OpenClaw Works (Medium)](https://bibek-poudel.medium.com/how-openclaw-works-understanding-ai-agents-through-a-real-architecture-5d59cc7a4764)
- [What Is OpenClaw -- Complete Guide (Milvus Blog)](https://milvus.io/blog/openclaw-formerly-clawdbot-moltbot-explained-a-complete-guide-to-the-autonomous-ai-agent.md)
- [soul.md -- Build a personality for your agent (GitHub)](https://github.com/aaronjmars/soul.md)
- [TechNickAI/openclaw-config (GitHub)](https://github.com/TechNickAI/openclaw-config)
- [awesome-openclaw-agents -- 162 templates (GitHub)](https://github.com/mergisi/awesome-openclaw-agents)
- [openclaw-multi-agent-kit (GitHub)](https://github.com/raulvidis/openclaw-multi-agent-kit)
- [Mastering OpenClaw on AWS (DEV Community)](https://dev.to/aws-builders/mastering-openclaw-on-aws-fine-tuning-personality-memory-and-soul-37ig)
- [OpenClaw HEARTBEAT/SOUL/Memory Config Guide (Blink Blog)](https://blink.new/blog/openclaw-heartbeat-soul-memory-configuration-guide-2026)
- [Building ClaudeClaw on Claude Code (Medium)](https://medium.com/@mcraddock/building-claudeclaw-an-openclaw-style-autonomous-agent-system-on-claude-code-fe0d7814ac2e)
- [The OpenClaw Guide for Claude Code (GitHub)](https://github.com/affaan-m/everything-claude-code/blob/main/the-openclaw-guide.md)
- [OpenClaw Multi-Agent Workspaces (Fast.io)](https://fast.io/resources/openclaw-multi-agent-workspaces/)
