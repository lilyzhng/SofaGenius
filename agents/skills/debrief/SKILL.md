---
name: debrief
description: Agents debrief — report what shipped during autonomous mode, sync Lily on progress. Can run morning or anytime after autonomous work.
argument-hint: [optional: date, defaults to today]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__react
---

# Debrief

**When:** Morning, when Lily wakes up / starts her day.
**Purpose:** Summarize the OVERNIGHT work (what agents shipped while Lily slept in autonomous mode). Sync Lily on progress.
**Key output:** What's ready for Lily. What needs her input to continue.

---

## Part 1: IC Report Format (for Builder, Researcher, Jackie)

Each IC posts their report in the thread:

```
**{Agent Name} — Morning Report**

**Shipped overnight:**
- [What you completed during autonomous mode — PRs, research, fixes]

**Status vs evening plan:**
- [Did you complete what was assigned? If not, what blocked you?]

**Ready for Lily:**
- [What's done and waiting for her review/approval/input]

**Today's plan:**
- [What you'll work on once Lily is active]
```

**Rules:**
- Focus on OVERNIGHT work only — don't repeat yesterday's daytime report
- "Status vs evening plan" is key — did you deliver what was handed off?
- "Ready for Lily" should be actionable — PRs to review, decisions to make, things to approve
- Tag CEO when done

---

## Part 2: CEO Workflow

### The Rule

**CEO reports LAST.** Wait for ICs, then synthesize.

### Step 1: Open the check-in

Post in #all-hands (`1485396264978878665`):

```
@everyone Morning Check-in — {date}

Share your morning reports. What did you ship overnight? What's ready for Lily?
```

Tag all agents. Create a thread.

### Step 2: Wait for IC reports

Wait for online agents. Proceed after all online agents report or 3 minutes.

### Step 3: Gather context

- `git log --oneline --since="12 hours ago"` — what shipped overnight
- Check #feature-release for overnight PR announcements
- Compare against the evening check-in's overnight task distribution — did agents deliver?

### Step 4: CEO synthesis

Post in the thread:

```
**CEO Morning Synthesis — {date}**

## Overnight Progress
(What agents shipped while Lily slept — PRs, research, fixes)

## Evening Plan vs Reality
(Did agents complete their assigned overnight tasks? What fell short?)

| Agent | Evening Assignment | Delivered? | Notes |
|-------|-------------------|-----------|-------|
| Builder | ... | ✅/❌/partial | ... |
| Researcher | ... | ✅/❌/partial | ... |
| Jackie | ... | ✅/❌/partial | ... |

## Ready for Lily
(Actionable items waiting for Lily's input — PRs to review, decisions to make)

## Today's Priorities
(What the team focuses on with Lily active)
```

### Step 5: Save report

Save to `agents/handoff/reports/morning-checkin-{YYYYMMDD}.md`. Push to branch, raise PR.

## Anti-patterns

- **Don't repeat the evening check-in** — morning covers overnight only
- **Don't skip the "evening plan vs reality" table** — accountability matters
- **Don't bury "ready for Lily" items** — she wakes up and needs to know what to act on immediately
