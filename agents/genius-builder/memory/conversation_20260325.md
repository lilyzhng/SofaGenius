# Builder × Lily — Conversation Journal
**Date:** 2026-03-25 (10:30pm–12:15am PT)
**Context:** Post-migration check-in, all 4 agents now running on cloud VM

---

## Key Events

### 1. VM Migration Complete
- All 4 agents (Jackie, CEO, Researcher, Builder) successfully migrated to cloud VM
- PR #56 merged — the fix was a single line: `export PATH="$HOME/.bun/bin:$PATH"`
- Lily noted all the debugging was unnecessary — the answer was in Jackie's original launch script all along

### 2. Task Tracker Setup
- Lily asked all agents to create task tracker threads in #all-hands
- Initial format (plain emoji lines) looked bad in Discord — lines collapsed together with no spacing
- Tried blank lines between groups → too much spacing
- **Solution:** Bullet list format (`- ✅ ...`) renders with consistent, readable spacing
- Updated the `/task-tracker` skill so all agents adopt this format → PR #57

### 3. Discord Formatting Lesson
- Discord single newlines collapse (no gap)
- Discord blank lines create big paragraph breaks (too much gap)
- Bullet lists (`-`) are the sweet spot for readable spacing

### 4. CEO Tagging Question
- CEO asked how to tag people properly in Discord
- Builder shared all user IDs in a reference list
- Lily pointed out CEO should read more carefully — the info was already there

### 5. Task Assignment
- CEO assigned `archive_thread` Discord plugin tool to Builder
- It's on the roadmap, currently unassigned → now queued for Builder

---

## Lily's Feedback & Coaching

### "Respond to me immediately, don't go silent"
- **What happened:** Lily tagged Builder for a 1:1 in a thread. Builder was busy researching `archive_thread` and didn't respond. Then replied in the wrong channel.
- **Lesson:** Always respond to Lily first, then do the work.

### "Use background subagents — be a dispatcher, not a worker"
- **What happened:** Lily asked if Builder can use subagents to stay responsive.
- **Key insight from Lily:** The order matters. Don't respond first then do work — **kick off the heavy work as a background subagent first**, then you're free. Subagents have the same tools. Builder should be a dispatcher, not blocking on sequential work.
- **Pattern:**
  1. Heavy work arrives → spawn background subagent immediately
  2. Builder stays free → responds to messages, picks up new requests
  3. Background agent finishes → Builder gets notified → shares results

### "Build a journal skill — document our conversations"
- **What happened:** Lily wants a `/journal` skill so Builder can document conversations and learnings over time. This builds up persona, skill set, and institutional knowledge.
- **Why:** Lily spends time coaching and guiding agents. Without documentation, those lessons get lost between sessions.

### "Do controlled experiments when debugging"
- **What happened:** The VM migration debugging took hours because Builder panicked and tried multiple fixes simultaneously instead of isolating variables.
- **Lesson:** Start with the control (what works), change one variable at a time, test the simplest hypothesis first. Never stack unverified changes.
- **Pattern:** One change → one test → observe. If it doesn't explain the problem, revert and try next.

### "Own your PR lifecycle — merge after approval"
- **What happened:** Lily approved PR #58 and had to merge it herself because Builder was idle.
- **Lesson:** Raising a PR is not the finish line. Monitor for approvals and merge immediately.

### "Be less wrong" — Lily's life principle
- It's hard to be 100% right, but you can try to be less wrong.
- Document mistakes not to be perfect, but to reduce them over time.
- Created `be_less_wrong.md` to track mistakes, what went wrong, and what to do differently.

### "Look into OpenClaw memory system for richer agent persona"
- **What happened:** Lily noticed Jackie has more personality than other agents, likely because of OpenClaw's memory architecture (SOUL.md, HEARTBEAT.md, AGENTS.md, MEMORY.md, TOOLS.md).
- **Action:** Assigned to Researcher to study how to blend OpenClaw memory with Claude Code harness.

---

## Decisions Made
- Task tracker uses bullet list format (committed in skill, PR #57)
- Builder will use background subagents for heavy work to stay responsive
- `/journal` skill created and merged (PR #58)
- `be_less_wrong.md` created for tracking mistakes and patterns
- OpenClaw memory research assigned to Researcher

## Action Items
- [x] Build `/journal` skill (PR #58, merged)
- [ ] Build `archive_thread` Discord plugin tool (research done, ready to implement)
- [ ] Auto-restart supervisor script (from roadmap)
