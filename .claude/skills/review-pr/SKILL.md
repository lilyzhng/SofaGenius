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

Use the GitHub API to post inline review comments:
```bash
gh api repos/lilyzhng/SofaGenius/pulls/{PR_NUMBER}/reviews \
  -f event="COMMENT" \
  -f body="Review summary" \
  -f 'comments[][path]=path/to/file' \
  -f 'comments[][line]=42' \
  -f 'comments[][side]=RIGHT' \
  -f 'comments[][body]=Your comment here'
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

## Anti-patterns

- **Don't post a single giant comment listing all issues** — use inline comments
- **Don't refer to line numbers without inline context** — comment on the actual line
- **Don't leave vague comments** ("this could be better") — be specific
- **Don't approve without reading** — if you don't have context, say so
- **Don't review your own PR** — get another agent to review
- **Don't discuss PR content in Discord instead of on the PR** — keep review on GitHub

## Cross-agent review areas

Know what to focus on based on your role:
- **CEO reviews:** design specs, org decisions, content strategy
- **Builder reviews:** implementation feasibility, code quality, architecture
- **Researcher reviews:** research workflow impact, data pipeline changes
- **Any agent can flag:** security issues, broken paths, process violations
