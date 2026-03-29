---
name: debrief
description: Agents debrief — report what shipped during autonomous mode, sync Lily on progress. Runs after any autonomous period, not just mornings.
argument-hint: [optional: date, defaults to today]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__react
---

# Debrief

**When:** After any autonomous period — could be morning, midday, or any time Lily returns. Not tied to a specific time.
**Purpose:** Summarize what agents shipped during autonomous mode (since the last `/hands-off`). Sync Lily on progress and what needs her input.
**Key output:** What's ready for Lily. What needs her input to continue.

---

## Part 1: IC Report Format (for Builder, Researcher, Jackie)

Each IC posts their report in the thread:

```
**{Agent Name} — Debrief Report**

**Shipped during autonomous mode:**
- [What you completed since last /hands-off — PRs, research, fixes]

**Status vs plan:**
- [Did you complete what was assigned at /hands-off? If not, what blocked you?]

**Ready for Lily:**
- [What's done and waiting for her review/approval/input]

**Next up:**
- [What you'll work on once Lily is active]

**Blockers:**
- [What's stopping you — name WHO can unblock — or "None"]
```

**Rules:**
- Focus on AUTONOMOUS work only — what shipped since the last `/hands-off`
- "Status vs plan" is key — did you deliver what was handed off?
- "Ready for Lily" must be actionable — PRs to review, decisions to make, things to approve
- Tag Growth when done

---

## Part 2: Growth Workflow

### The Rule

**Growth reports LAST.** Wait for ICs, then synthesize.

### Step 1: Open the debrief

Post in #all-hands (`1485396264978878665`):

```
@everyone Debrief — {date}

Lily is back. Share your debrief reports. What did you ship during autonomous mode? What's ready for Lily?
```

Tag all agents. Create a thread.

### Step 2: Wait for IC reports

Wait for online agents. Don't spam offline agents. Proceed after all online agents report or 3 minutes.

### Step 3: Gather context

- Find when the last `/hands-off` was posted (check #all-hands thread timestamps)
- `git log --oneline --since="{last hands-off time}"` — what shipped in this window
- Check #feature-release for PR announcements since last sync
- Compare against the `/hands-off` task distribution — did agents deliver?

### Step 4: Growth synthesis

Post in the thread:

```
**Growth Debrief Synthesis — {date}**

## Autonomous Progress ({time window: since last /hands-off})
(What agents shipped during autonomous mode — PRs, research, fixes. Check git log for the time window.)

## Plan vs Reality
(Did agents complete their assigned tasks from /hands-off? What fell short?)

| Agent | Assigned Task | Delivered? | Notes |
|-------|--------------|-----------|-------|
| Builder | ... | ✅/❌/partial | ... |
| Researcher | ... | ✅/❌/partial | ... |
| Jackie | ... | ✅/❌/partial | ... |

## Ready for Lily
(Actionable items waiting for Lily's input — PRs to review, decisions to make)

## Priorities for Active Session
(What the team focuses on now that Lily is active)
```

### Step 5: Save report

Save to `agents/handoff/reports/debrief-{YYYYMMDD}.md`. Push to branch, raise PR.

## Completion Checklist

Before finishing the debrief, verify:

- [ ] All online agents submitted their IC reports
- [ ] Growth synthesis includes the plan vs reality table
- [ ] "Ready for Lily" section has actionable items (PRs, decisions)
- [ ] Time window is accurate (since last /hands-off, not arbitrary "12 hours")
- [ ] Report saved to `agents/handoff/reports/`

## Anti-patterns

- **Don't repeat the last active session report** — debrief covers autonomous mode only
- **Don't skip the "plan vs reality" table** — accountability matters
- **Don't bury "ready for Lily" items** — she needs to know what to act on immediately
- **Don't assume time of day** — debrief happens whenever Lily returns, not just mornings
- **Don't write human timelines** — use agent time (see `/raise-pr` Agent Time section)
