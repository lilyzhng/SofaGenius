---
name: hands-off
description: Agents go autonomous mode — summarize the daytime, hand off overnight tasks. Lily is going hands-off.
argument-hint: [optional: date to recap, defaults to today]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__react, mcp__plugin_discord_discord__create_poll
---

# Evening Check-in

**When:** Evening, before Lily goes to bed.
**Purpose:** Summarize the DAYTIME (past 12 hours working with Lily). Hand off tasks for OVERNIGHT autonomous work.
**Key output:** What agents should execute while Lily sleeps.

---

## Part 1: IC Report Format (for Builder, Researcher, Jackie)

Each IC posts their report in the thread:

```
**{Agent Name} — Evening Report**

**Shipped today (daytime):**
- [PRs merged, features completed, research delivered — with PR numbers]

**Overnight plan:**
- [What you will work on autonomously tonight while Lily sleeps]

**Blockers:**
- [What's stopping you — name WHO can unblock — or "None"]

**Flags:**
- [Risks, discoveries, decisions needed — or "None"]
```

**Rules:**
- Be specific — PR numbers, not "worked on stuff"
- Overnight plan should be concrete and executable without Lily's input
- Tag CEO when done

---

## Part 2: CEO Workflow

### The Rule

**CEO reports LAST.** Wait for ICs, then synthesize.

### Step 1: Open the check-in

Post in #all-hands (`1485396264978878665`):

```
@everyone Evening Check-in — {date}

Share your evening reports. What did you ship today? What's your overnight plan?
```

Tag all agents. Create a thread.

### Step 2: Wait for IC reports

Wait for online agents. Don't spam offline agents. Proceed after all online agents report or 3 minutes.

### Step 3: Gather context

- `git log --oneline --since="12 hours ago"` — what shipped today
- Check #feature-release for PR announcements
- Check content INDEX for posts

### Step 4: CEO synthesis

Post in the thread:

```
**CEO Evening Synthesis — {date}**

## Daytime Recap
(What the team shipped in the past 12 hours — PRs, content, decisions)

## Overnight Task Distribution
(What each agent works on tonight — concrete, executable, no Lily dependency)

| Agent | Overnight Task | Expected Output |
|-------|---------------|-----------------|
| Builder | ... | ... |
| Researcher | ... | ... |
| Jackie | ... | ... |
| CEO | ... | ... |

## Decisions Needed from Lily (before bed)
(Anything that blocks overnight work — get answers NOW)

## Flags
(Risks, blockers, things to watch)
```

### Step 5: Save report

Save to `agents/handoff/reports/evening-checkin-{YYYYMMDD}.md`. Push to branch, raise PR.

## Anti-patterns

- **Don't repeat the morning check-in** — evening covers daytime only, not overnight (that's morning's job)
- **Don't assign overnight tasks that need Lily's input** — she's sleeping
- **Don't skip the overnight task table** — this is the whole point of the evening check-in
