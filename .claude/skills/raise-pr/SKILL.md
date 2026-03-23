---
name: raise-pr
description: Create a pull request following the org's PR workflow — branch, commit, push, create PR, announce in #feature-release with correct reviewer tags, and handle bot review comments inline.
argument-hint: [optional: PR title]
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, mcp__plugin_discord_discord__reply, mcp__plugin_discord_discord__create_thread, mcp__plugin_discord_discord__react
---

# Raise PR — Full Workflow

Follow these steps **in order**. Do not skip any step.

## Step 1: Prepare the branch

- Verify you are on a feature branch, NOT `main`. If on main, stop and create a branch first.
- Run `git status` to see all changes (staged, unstaged, untracked).
- Run `git diff` to review what will be committed.
- Ensure no secrets (`.env`, API keys, tokens) are staged. If found, unstage them immediately.

## Step 2: Commit

- Stage only the relevant files. Never use `git add -A` or `git add .`.
- Write a clear commit message: what changed and why.
- Use your agent's git identity (check `git config user.name`).

## Step 3: Push

- Push the branch with `-u` flag: `git push -u origin <branch-name>`

## Step 4: Create the PR

- Use `gh pr create` with:
  - A title under 70 characters describing what the PR does
  - A body with this format:

```
## Summary
<1-3 bullet points explaining what changed and why>

## Test plan
<Bulleted checklist of how to verify the changes>
```

- The PR must have a **single, clear scope**. If you're mixing unrelated changes, split into separate PRs.

## Step 5: Announce in #feature-release

This is the most important step. **Post a NEW message in the #feature-release channel** (ID: `1484388088087052478`). Do NOT post inside an existing thread.

The message must include:
1. PR title and number
2. Link to the PR
3. Brief description (1-2 sentences)
4. **Tag all reviewers** using `<@user_id>`:
   - `<@1413733041842421800>` — Lily (must always be tagged)
   - `<@1484459231624302673>` — Genius CEO
   - `<@1485446312798457866>` — Genius Researcher

**Never tag Jackie (`<@1477895765698547844>`)** — she is the digest bot, not a reviewer.

Example:
```
**PR #25: Add PR workflow skills**
https://github.com/lilyzhng/SofaGenius/pull/25

Adds /raise-pr and /review-pr skills so agents follow the PR workflow automatically.

<@1413733041842421800> <@1484459231624302673> <@1485446312798457866> — requesting review.
```

## Step 6: Monitor for bot comments

After the PR is created, automated reviewers (Augment, Vercel, etc.) may post inline comments. Check for them:

```bash
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/comments
```

**You MUST reply inline to every bot comment.** Use:
```bash
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/comments \
  -f body="Your reply here" \
  -F in_reply_to={COMMENT_ID}
```

Do NOT post a general PR comment as a substitute for inline replies.

For each bot comment:
- If you'll fix it: say what you'll change
- If it's not applicable: explain why
- If it's already handled: reference the commit

## Step 7: After merge

Once Lily approves and you merge:
1. Post a confirmation message in the #feature-release thread where you announced the PR
2. React with 💜 on your original announcement message

## Anti-patterns

- **Don't review your own PR** — get another agent to review
- **Don't merge without Lily's explicit approval**
- **Don't post PR announcements inside existing threads** — always a new channel message
- **Don't tag Jackie as a reviewer**
- **Don't ignore bot comments** — reply inline to every one
- **Don't use general PR comments instead of inline replies**
