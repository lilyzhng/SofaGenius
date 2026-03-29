---
name: hands-off
description: Agents go autonomous mode — summarize recent work, hand off tasks for autonomous execution. Lily is going hands-off.
argument-hint: [optional: date to recap, defaults to today]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__react, mcp__plugin_discord_discord__create_poll
---

# Hands-Off

**When:** Anytime Lily wants to go hands-off — could be evening, midday, or any break. Not tied to a specific time.
**Purpose:** Summarize what was accomplished during the active session. Hand off tasks for agents to execute autonomously while Lily is away.
**Key output:** What agents should execute during autonomous mode.

---

## Part 1: IC Report Format (for Builder, Researcher, Jackie)

Each IC posts their report in the thread:

```
**{Agent Name} — Hands-Off Report**

**Shipped this session:**
- [PRs merged, features completed, research delivered — with PR numbers]

**Autonomous plan:**
- [What you will work on while Lily is away — must be executable without her input]

**Blockers:**
- [What's stopping you — name WHO can unblock — or "None"]

**Flags:**
- [Risks, discoveries, decisions needed — or "None"]
```

**Rules:**
- Be specific — PR numbers, not "worked on stuff"
- Overnight plan should be concrete and executable without Lily's input
- Tag Growth when done

---

## Part 2: Growth Workflow

### The Rule

**Growth reports LAST.** Wait for ICs, then synthesize.

### Step 1: Open the check-in

Post in #all-hands (`1485396264978878665`):

```
@everyone Hands-Off Report — {last sync time} → {now} PT

Lily is going hands-off. Share your reports for this time window: what did you ship, and what's your autonomous plan?
```

Example: `Hands-Off Report — Mar 23 11pm → Mar 24 3pm PT`

The time window starts from the last hands-off or debrief. Check #all-hands for the previous sync timestamp.

Tag all agents. Create a thread.

### Step 2: Wait for IC reports

Wait for online agents. Don't spam offline agents. Proceed after all online agents report or 3 minutes.

### Step 3: Gather context

- Find when the last hands-off or debrief was posted (check #all-hands thread timestamps)
- `git log --oneline --since="{last sync time}"` — what shipped in this window
- Check #feature-release for PR announcements
- Check content INDEX for posts

### Step 4: Growth synthesis

Post in the thread:

```
**Growth Hands-Off Synthesis — {last sync time} → {now} PT**

## Session Recap
(What the team shipped since the last sync — PRs, content, decisions. Check git log for the time window since the previous hands-off or debrief.)

## Autonomous Task Distribution
(What each agent works on while Lily is away — concrete, executable, no Lily dependency)

| Agent | Autonomous Task | Expected Output |
|-------|----------------|-----------------|
| Builder | ... | ... |
| Researcher | ... | ... |
| Jackie | ... | ... |
| Growth | ... | ... |

## Decisions Needed from Lily (before going hands-off)
(Anything that blocks autonomous work — get answers NOW)

## Flags
(Risks, blockers, things to watch)
```

### Step 5: Save report

Save to `agents/handoff/reports/hands-off-{YYYYMMDD}.md`. Push to branch, raise PR.

## Growth Completion Checklist

Before posting the synthesis, verify ALL:

- [ ] Time window identified (last sync timestamp → now)
- [ ] Header uses format: `Hands-Off Report — {start} → {end} PT`
- [ ] All online ICs submitted reports (or marked as "no report")
- [ ] Tweet metrics pulled and INDEX.md updated
- [ ] `git log --since="{last sync}"` checked — report matches actual commits
- [ ] Autonomous task table filled — every agent has a concrete task
- [ ] No autonomous task requires Lily's input
- [ ] Decisions needed from Lily section filled (or "None")
- [ ] Report saved to `agents/handoff/reports/hands-off-{YYYYMMDD}.md`
- [ ] PR raised for the report

## IC Report Checklist

Before posting your report, verify:

- [ ] Used "Hands-Off Report" format (not "Evening Report")
- [ ] "Shipped this session" lists PRs with numbers — not vague descriptions
- [ ] "Autonomous plan" is concrete and executable without Lily
- [ ] Blockers name WHO can unblock — not just "blocked"
- [ ] Tagged Growth when done

## Anti-patterns

- **Don't repeat the last debrief** — hands-off covers only the window since the last sync
- **Don't assign autonomous tasks that need Lily's input** — she's away
- **Don't skip the autonomous task table** — this is the whole point of hands-off
- **Don't use time-of-day language** — "tonight", "overnight", "daytime" assume evening. Use "autonomous mode", "while Lily is away", "this session"
