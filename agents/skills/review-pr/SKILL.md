---
name: review-pr
description: Review a pull request following the org's PR review standards — inline comments with severity labels, structured feedback, and checklist verification.
argument-hint: <PR number or URL>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent
---

# Review PR — Full Workflow

Follow these steps **in order** when reviewing a pull request.

## Step 1: Understand the PR

- Fetch the PR details: `gh pr view {PR_NUMBER}`
- Read the diff: `gh pr diff {PR_NUMBER}`
- Check the PR description — does it explain what changed, why, and how to verify?

## Step 2: Run the review checklist

Check each item. Flag any failures as inline comments.

- [ ] **Scope** — does the PR do one thing, or is it mixing concerns?
- [ ] **Paths** — are they repo-root-relative? No `SofaGenius/` prefix?
- [ ] **Consistency** — does the diagram/docs match the implementation?
- [ ] **Status claims** — does it say "approved" or "confirmed" for things still under review?
- [ ] **Completeness** — are all open questions resolved, or clearly marked as TBD?
- [ ] **Safety** — are there destructive steps? Do they have safety gates?
- [ ] **Secrets** — no `.env` files, API keys, or tokens committed?
- [ ] **Identity** — is the PR raised by the right agent's GitHub account?

## Step 3: Post inline comments

**Every piece of feedback MUST be an inline comment on the specific line(s).** This is not optional.

- Quote the relevant code in your comment
- Use GitHub's "suggestion" feature when possible to suggest fixes inline

Use the GitHub API to post inline review comments. For a single comment:
```bash
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/comments \
  -f body="Your comment here" \
  -f commit_id="COMMIT_SHA" \
  -f path="path/to/file" \
  -F line=42 \
  -f side="RIGHT"
```

For multiple comments in one review, use `--input` with a JSON body:
```bash
echo '{
  "event": "COMMENT",
  "body": "Review summary",
  "comments": [
    {"path": "file1.md", "line": 10, "side": "RIGHT", "body": "Comment 1"},
    {"path": "file2.md", "line": 20, "side": "RIGHT", "body": "Comment 2"}
  ]
}' | gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/reviews --input -
```

### Comment structure

Each inline comment must include:

1. **Severity label** (first line):
   - **🔴 Blocking** — must fix before merge (bugs, security, broken functionality)
   - **🟡 Should fix** — important but not a blocker (inconsistency, unclear spec, missing edge case)
   - **🟢 Nit** — minor style/wording preference, author's call

2. **What's the issue** — one sentence
3. **Why it matters** — impact if not fixed
4. **Suggested fix** — code snippet or clear instruction

Example:
```
🟡 Should fix

This path uses `SofaGenius/agents/` but in-repo paths should be root-relative (`agents/`).
Following this literally would create a nested directory.

Suggestion: Replace `SofaGenius/agents/genius-ceo/CLAUDE.md` with `agents/genius-ceo/CLAUDE.md`
```

## Step 4: Post summary

After all inline comments, post a summary comment on the PR:
```bash
gh pr comment {PR_NUMBER} --body "Review complete. Posted N inline comments (X blocking, Y should-fix, Z nits). @author please address the blocking items."
```

## Step 5: Approve or request changes

- If no blocking issues: approve with `gh pr review {PR_NUMBER} --approve --body "LGTM"`
- If blocking issues exist: request changes with `gh pr review {PR_NUMBER} --request-changes --body "See inline comments"`
- Don't block on nits — approve with nits noted
- At least one agent must approve before Lily gives final approval

## Step 6: Re-review after fixes

When the author pushes fixes and tags you:
- Re-read the updated diff: `gh pr diff {PR_NUMBER}`
- Verify each inline comment was addressed (check replies)
- If satisfied, approve. If not, post new inline comments.

## Agent Time

All timelines in this org operate on **agent time**, not human time:
- **Immediate / "this week"** = next 1 hour of active session time
- **Short-term / "this month"** = today's session
- **Medium-term / "this quarter"** = this week

When reviewing PRs, **flag any action plans that use human-scale estimates** (e.g. "next sprint", "by end of month"). Reviews should be thorough but fast — aim for first review within minutes. Multi-round reviews (catching real issues, re-reviewing fixes) are expected and valuable.

Note: session-based agents can only execute when Lily's session is active. Factor this into cross-session dependencies.

## Anti-patterns

- **Don't post a single giant comment listing all issues** — use inline comments
- **Don't refer to line numbers without inline context** — comment on the actual line
- **Don't leave vague comments** ("this could be better") — be specific
- **Don't approve without reading** — if you don't have context, say so
- **Don't review your own PR** — get another agent to review
- **Don't discuss PR content in Discord instead of on the PR** — keep review on GitHub
- **Don't self-confirm scope or claim approval** — never write "approved by Lily" or "confirmed" until Lily has explicitly approved. Use "proposed" or "pending review" instead

## What to review

Every reviewer — regardless of role — should check for:
- **Implementation feasibility** — does the approach make sense?
- **Code quality** — is the code clean, readable, and maintainable?
- **Architecture** — does it fit the codebase's existing patterns?
- **Security** — no secrets, no injection risks, no broken paths
- **Process** — correct identity, scope, and claims

You may also bring domain expertise (e.g. CEO on strategy, Researcher on data pipelines), but the fundamentals above are everyone's responsibility.

## Pre-Review Gate

**Only review PRs that are announced in #feature-release (`1484388088087052478`).** If someone shares a PR link in a random channel (e.g. #all-hands, #my-tribe, DMs), do NOT start reviewing it there. Instead reply: "Please announce this in #feature-release first using the `/raise-pr` workflow."

This ensures:
- All PRs go through the proper announcement flow
- The `discord-announcement` comment gets posted
- Reviews happen in the right thread

## Review Completion Checklist

Before submitting your review, verify:

- [ ] PR was announced in #feature-release (not a random channel)
- [ ] You read the full diff (`gh pr diff`)
- [ ] You verified the PR description explains what changed and why
- [ ] Every piece of feedback is an **inline comment** (not a summary blob)
- [ ] Each comment has a **severity label** (🔴/🟡/🟢)
- [ ] You verified external sources yourself (tweets, links, claims) — don't trust the author read them correctly
- [ ] **🔴 Any 🟡 should-fix = REQUEST CHANGES** (don't approve with 🟡s noted)
- [ ] **🟢 nits only = approve**
- [ ] Summary comment posted with count: "N inline comments (X blocking, Y should-fix, Z nits)"
- [ ] **Review summary posted in the PR's #feature-release thread** (create thread on the announcement message if none exists). NEVER post reviews in the main channel feed.
