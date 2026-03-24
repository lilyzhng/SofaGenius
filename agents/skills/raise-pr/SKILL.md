---
name: raise-pr
description: Create a pull request following the org's PR workflow — branch, commit, push, create PR, announce in `#feature-release` with correct reviewer tags, and handle bot review comments inline.
argument-hint: [optional: PR title]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__react
---

# Raise PR — Full Workflow

Follow these steps **in order**. Do not skip any step.

## Step 1: Prepare the branch

- Verify you are on a feature branch, NOT `main`. If on main, stop and create a branch first.
- Run `git status` to see all changes (staged, unstaged, untracked).
- Run `git diff` to review unstaged changes and `git diff --cached` to review already-staged changes.
- Ensure no secrets (`.env`, API keys, tokens) are staged. If found, unstage them immediately.

## Step 2: Commit

- Stage only the relevant files. Never use `git add -A` or `git add .`.
- Write a clear commit message: what changed and why.
- Use your agent's git identity — verify both are set:
  - `git config user.name` (e.g. `genius-builder`)
  - `git config user.email` (e.g. `lilyzen.ml@gmail.com`)
- Ensure `GH_TOKEN` is set to your agent's bot token (from `.env`), not another agent's or Lily's.

## Step 3: Push

- Push the branch with `-u` flag: `git push -u origin <branch-name>`

## Step 4: Create the PR

- Use `gh pr create` with:
  - A title under 70 characters describing what the PR does
  - A body with this format:

```
The repo has a PR template (`.github/pull_request_template.md`) that auto-populates the body with Summary, Test plan, Author Checklist, and Reviewer Checklist. **Use it — do not delete the checklists.** Fill in the Summary and Test plan, then check off the Author Checklist items as you complete them. The Reviewer Checklist stays unchecked — reviewers will copy it into their review comment and check items off before approving.

- The PR must have a **single, clear scope**. If you're mixing unrelated changes, split into separate PRs.

**Good scope:**
- "Add PR review rules for agent org" — one doc, one purpose
- "Migrate agent CLAUDE.md configs to SofaGenius" — one migration step

**Bad scope:**
- "Migration spec + PR review rules + onboarding updates" — three unrelated things
- "Various fixes" — vague, hard to review

## Step 5: Announce in #feature-release

This is the most important step. **Post a NEW message in the #feature-release channel** (ID: `1484388088087052478`). Do NOT post inside an existing thread.

The message must include:
1. PR title and number
2. Link to the PR
3. Brief description (1-2 sentences)
4. **Tag all reviewers** using `<@user_id>` — but **never tag yourself** (you're the author, not a reviewer):
   - `<@1413733041842421800>` — Lily (must always be tagged)
   - `<@1484459231624302673>` — Genius CEO
   - `<@1485446312798457866>` — Genius Researcher
   - `<@1484381532201156658>` — Genius Builder

**Never tag Jackie (`<@1477895765698547844>`)** — she is the notification bot, not a reviewer.
**Never tag yourself as a reviewer** — you are the PR author. Skip your own ID from the list above.

Example:
```
**PR #25: Add PR workflow skills**
https://github.com/lilyzhng/SofaGenius/pull/25

Adds /raise-pr and /review-pr skills so agents follow the PR workflow automatically.

<@1413733041842421800> <@1484459231624302673> <@1485446312798457866> <@1484381532201156658> — requesting review.
```

**After posting**, save the Discord message ID as a comment on the PR so the approval bot can reply in the same thread:
```bash
gh pr comment {PR_NUMBER} --body "discord-announcement: {MESSAGE_ID}"
```
The message ID is returned by the Discord reply tool when you post the announcement. This enables Jackie to post the approval notification in the correct thread.

## Step 6: Respond to ALL review comments

**MANDATORY: A PR is NOT done until every comment — from any source — has an inline reply.**

This applies to ALL comments: Augment bot, Vercel, other agents, Lily, anyone. No exceptions. Unaddressed comments block the PR.

**Before considering your PR work complete, you MUST:**
1. Check for ALL comments on the PR:

```bash
# Inline review comments (from Augment, agents, Lily)
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/comments
# Non-inline PR comments (from Vercel, other bots)
gh api repos/lilyzhng/SofaGenius/issues/{PR_NUMBER}/comments
```

2. **Reply inline to every single comment.** Use:
```bash
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/comments \
  -f body="Your reply here" \
  -F in_reply_to={COMMENT_ID}
```

Do NOT post a general PR comment as a substitute for inline replies. Never address feedback only in code without replying — reviewers need to see their comment was acknowledged.

For each comment:
- If you fixed it: reply with what you changed (e.g. "Fixed in `abc1234` — changed path to repo-relative")
- If you disagree: reply with your reasoning. Don't silently ignore.
- If it's a nit you're accepting: a simple "Done" or "Fixed" is fine.
- For bot comments: acknowledge and explain whether the issue was addressed or why it's not applicable.

## Step 7: Push fixes, then notify

When addressing review feedback:
- Fix issues in a **new commit** (don't amend — keep the review trail)
- Reply to each inline comment confirming the fix
- Post a summary comment tagging reviewers when all feedback is addressed:
```bash
gh pr comment {PR_NUMBER} --body "All feedback addressed in \`commit_hash\`. @reviewer1 @reviewer2 ready for re-review."
```

## Step 8: Merge when the PR Approval Bot tags you

A GitHub Actions workflow sends a Discord notification when Lily approves the PR. It will tag you with a message like: "PR #N approved by Lily — merge it!"

**When you see this notification, immediately complete the remaining workflow:**

1. Merge the PR: `gh pr merge {PR_NUMBER} --squash`
2. Create a thread on your original #feature-release announcement message (if one doesn't exist yet) and post a confirmation that the PR is merged
3. React with 💜 on your original announcement message

Do NOT wait for a separate instruction from Lily — the approval bot notification IS the trigger. This is the final step of `/raise-pr` and your work is not done until all three actions above are completed.

## Agent Time

All timelines in this org operate on **agent time**, not human time. When writing action plans or estimates:
- **Immediate / "this week"** = next 1 hour of active session time
- **Short-term / "this month"** = today's session
- **Medium-term / "this quarter"** = this week

We are a 4-agent team that can work in parallel during active sessions. Action items should reflect agent speed — what a human team plans for a week, we execute in hours. Never pad timelines with human-scale estimates.

Note: session-based agents (Builder, Researcher, CEO) can only execute when Lily's session is active. Factor this into cross-session dependencies.

## Anti-patterns

- **Don't review your own PR** — get another agent to review
- **Don't merge without Lily's explicit approval**
- **Don't post PR announcements inside existing threads** — always a new channel message
- **Don't tag Jackie as a reviewer**
- **Don't ignore any review comments** — reply inline to every one (bot and human)
- **Don't use general PR comments instead of inline replies**
- **Don't self-confirm scope or claim approval** — never write "approved by Lily" or "confirmed" until Lily has explicitly approved. Use "proposed" or "pending review" instead
- **Don't close a PR without replying to all review comments first** — reviewers invested time in their feedback. Reply to every comment (fix it or explain why not) before closing, splitting, or restructuring the PR. Splitting is fine when needed — but always acknowledge the feedback first.

## Completion Checklist

Before considering a PR "done", verify ALL of these. Do NOT skip any.

- [ ] Branch created (not on main)
- [ ] No secrets staged (.env, API keys, tokens)
- [ ] Committed with agent's git identity
- [ ] Pushed with `-u` flag
- [ ] PR created with summary + test plan
- [ ] **Announcement posted in #feature-release** (new message, not in existing thread)
- [ ] **All reviewers tagged** (Lily + other agents, NOT yourself, NOT Jackie)
- [ ] **`discord-announcement: {MESSAGE_ID}` comment posted on the PR**
- [ ] All bot review comments replied to inline
- [ ] All human review comments replied to inline
- [ ] After approval: merged, thread confirmation posted, 💜 reacted
- [ ] **PR body updated to reflect final content** (if code changed during review, update the summary)
- [ ] **Branch deleted after merge** (`git push origin --delete {branch-name}`)

**If you skip the `discord-announcement` comment, the approval bot cannot find the right thread.** This breaks the merge workflow for everyone.
