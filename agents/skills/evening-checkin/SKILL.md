---
name: evening-checkin
description: Run the evening check-in — collect IC reports from all agents, then synthesize into a CEO report with additional observations. CEO reports LAST, not first.
argument-hint: [optional: date to recap, defaults to today]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__fetch_messages, mcp__plugin_discord_discord__react, mcp__plugin_discord_discord__create_poll
---

# Evening Check-in

Run this in the evening when the team has had a full day of work. This skill has two parts: **instructions for ICs** (how to submit reports) and **instructions for CEO** (how to synthesize).

---

## Part 1: IC Report Format (for Builder, Researcher, Jackie)

When CEO opens the standup, each IC posts their report in the thread using this exact format:

```
**{Agent Name} — Standup Report**

**Shipped today:**
- [List PRs merged, features completed, research delivered — with PR numbers/links]

**In progress:**
- [What you're actively working on right now]

**Next up:**
- [What you plan to tackle next session]

**Blockers:**
- [What's stopping you — or "None"]

**Flags for team:**
- [Anything the team should know — risks, discoveries, decisions needed — or "None"]
```

**Rules for ICs:**
- Be specific — PR numbers, file paths, commit hashes. Not "worked on stuff."
- If you shipped 0 PRs, say so honestly. Review-only days are fine, but name what you reviewed.
- Blockers must include WHO can unblock you. "Blocked" without a name is useless.
- Use agent time for any estimates (see Agent Time section in `/raise-pr`).
- Tag the CEO when your report is posted so they know to proceed.

---

## Part 2: CEO Workflow

### The Rule

**CEO reports LAST, not first.** You are the synthesizer, not the first speaker. Your job is to listen, then add value on top.

### Step 1: Open the standup

Post a new message in #all-hands (`1485396264978878665`):

```
@everyone Evening Standup — Recap of {date}

Team, share your status reports using the IC format. Tag me when done.
```

Tag all agents: `<@1484381532201156658>` (Builder), `<@1485446312798457866>` (Researcher), `<@1477895765698547844>` (Jackie).

Create a thread on that message for the discussion.

### Step 2: Wait for IC reports

**Do NOT post your summary yet.** Wait for online agents to respond.

- If an agent responds in the thread, they're online — wait for their report.
- If an agent doesn't respond within 2 minutes AND is known to be running, ping them once more.
- If an agent is **offline** (not launched, shut down, or on a different platform like Fly.io), mark them as "not running — no report" and proceed. Don't spam-ping offline agents.
- Proceed to Step 3 once all online agents have reported or after 3 minutes, whichever comes first.

### Step 3: Read context

While waiting or after reports come in, gather your own data:
- `git log --oneline --since="12 hours ago"` — what actually shipped
- Check #feature-release for PR announcements
- Check handoff status files in `agents/handoff/status/`
- Check content INDEX for posts made today

### Step 4: Synthesize the CEO report

After all IC reports are in, post YOUR report in the thread. Structure:

```
**CEO Report — Recap of {date}**

## IC Reports
(Summarize each agent's self-reported status — tag them)

## What Actually Shipped
(PRs merged, content posted, issues resolved — from git log + INDEX)

## Observations
(What CEO noticed that ICs didn't flag — patterns, gaps, wins)

## Blockers & Decisions Needed
(Anything requiring Lily's input)

## Priorities for Tomorrow
(Top 3 across all agents — informed by IC reports + CEO judgment)
```

### Step 5: Save the report

Save to `agents/handoff/reports/ceo-daily-{YYYYMMDD}.md` with frontmatter:

```markdown
---
type: ceo-daily-report
date: {YYYY-MM-DD}
recap-of: {YYYY-MM-DD}
post_to: all-hands
---
```

Push to a branch and raise a PR.

## Anti-patterns

- **Don't post the CEO summary before ICs report** — you'll miss their input and observations
- **Don't guess what ICs did** — ask them, then verify with git log
- **Don't use stale data** — always check current git log and PR status
- **Don't skip tagging people** — every IC mentioned should be tagged with their Discord ID
- **Don't write human timelines** — use agent time (see `/raise-pr` Agent Time section)
