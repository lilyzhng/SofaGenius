# PR Rules

How agents create and review pull requests in this org.

## Creating PRs

### One PR, one purpose

- **Each PR must have a clear, single scope.** Don't mix unrelated changes in one PR.
- If you discover something else that needs fixing while working on a PR, create a separate PR for it.
- The PR title should describe what it does in under 70 characters.
- The PR description should explain: what changed, why, and how to verify.

**Good scope:**
- "Add PR review rules for agent org" — one doc, one purpose
- "Migrate agent CLAUDE.md configs to SofaGenius" — one migration step

**Bad scope:**
- "Migration spec + PR review rules + onboarding updates" — three unrelated things
- "Various fixes" — vague, hard to review

### PR identity

- **Use your own GitHub identity** — never raise a PR as another agent or as Lily
- Set `GH_TOKEN` to your bot token when using `gh` CLI
- Configure `git config user.name` and `user.email` to your agent's GitHub account

### Who merges

- **Lily approves, author merges.** Agents raise PRs, get reviews, then Lily approves on GitHub. Once approved, the author merges. Never merge without Lily's explicit approval.

## Reviewing PRs

### Inline comments are mandatory

**Reviewers MUST use GitHub inline comments** — comment directly on the specific line(s) that need attention. This is not optional.

**Do this:**
- Comment directly on the specific line(s) that need attention
- Quote the relevant code in your comment
- Suggest the fix inline when possible (use GitHub's "suggestion" feature)

**Don't do this:**
- Post a single giant review comment listing all issues
- Refer to line numbers without inline context ("line 47 has a bug")
- Leave vague comments ("this could be better")

### Comment structure

Each inline comment should include:

1. **What's the issue** — one sentence
2. **Why it matters** — impact if not fixed (bug, confusion, drift, etc.)
3. **Suggested fix** — code snippet or clear instruction

Example:
```
This path uses `SofaGenius/agents/` but in-repo paths should be root-relative (`agents/`).
Following this literally would create a nested directory.

Suggestion: Replace `SofaGenius/agents/ceo/CLAUDE.md` with `agents/ceo/CLAUDE.md`
```

### Severity labels

Tag each comment with severity so the author knows what's blocking:

- **🔴 Blocking** — must fix before merge (bugs, security, broken functionality)
- **🟡 Should fix** — important but not a blocker (inconsistency, unclear spec, missing edge case)
- **🟢 Nit** — minor style/wording preference, author's call

## Responding to Reviews

### Inline replies are mandatory

**Code owners MUST reply to every inline comment on the PR.** This is not optional — don't leave comments hanging. This includes comments from **automated reviewers** (e.g., Augment bot), not just humans and agents.

- If you fixed it: reply on the inline comment with what you changed (e.g., "Fixed in `abc1234` — changed path to repo-relative")
- If you disagree: reply with your reasoning. Don't silently ignore.
- If it's a nit you're accepting: a simple "Done" or "Fixed" is fine.
- For bot comments: acknowledge and explain whether the issue was addressed or why it's not applicable.
- **Never address feedback only in code without replying** — reviewers need to see their comment was acknowledged.

### Push fixes, then comment

- Fix the issues in a new commit (don't amend — keep the review trail)
- Reply to each inline comment confirming the fix
- Post a summary comment tagging reviewers when all feedback is addressed

## Review Checklist

When reviewing, check for:

- [ ] **Scope** — does the PR do one thing, or is it mixing concerns?
- [ ] **Paths** — are they repo-root-relative? No `SofaGenius/` prefix?
- [ ] **Consistency** — does the diagram match the implementation/steps?
- [ ] **Status claims** — does it say "approved" or "confirmed" for things still under review?
- [ ] **Completeness** — are all open questions resolved, or clearly marked as TBD?
- [ ] **Safety** — are there destructive steps? Do they have safety gates?
- [ ] **Secrets** — no `.env` files, API keys, or tokens committed?
- [ ] **Identity** — is the PR raised by the right agent's GitHub account?

## Review Workflow

1. **Author raises PR** with clear, single-scope description
2. **Author posts the PR link in #feature-release** (channel ID: `1484388088087052478`) **and tags reviewers with `<@user_id>`** so they get notified — this is how the team discovers new PRs
3. **Reviewer posts inline comments** on the PR (not Discord messages about the PR)
4. **Author replies to every comment** — confirm fix or push back with reasoning
5. **Reviewer re-reviews** after fixes
6. **When satisfied**, reviewer approves (or says "LGTM" in a comment) — at least one agent must approve
7. **Lily gives final approval** on GitHub — this is required in addition to agent review, and is the gate to merge
8. **Author merges** once Lily's approval is received — only merge after explicit approval
9. **After merge:** Go back to the #feature-release thread where you announced the PR, post a message confirming it's merged, and **react with 💜 emoji on the original announcement message** to mark it as merged

## Cross-Agent Reviews

- **CEO reviews:** design specs, org decisions, content strategy
- **Builder reviews:** implementation feasibility, code quality, architecture
- **Researcher reviews:** research workflow impact, data pipeline changes
- **Any agent can flag:** security issues, broken paths, process violations

## Anti-Patterns

- **Don't review your own PR** — get another agent to review
- **Don't approve without reading** — if you don't have context, say so
- **Don't block on nits** — approve with nits noted, don't hold up the merge
- **Don't discuss PR content in Discord instead of on the PR** — keep review discussion on GitHub for the paper trail
- **Don't mix unrelated changes in one PR** — one purpose per PR
- **Don't ignore reviewer comments** — reply to every one
- **Don't self-confirm scope or claim approval** — never write "approved by Lily" or "confirmed" until Lily has explicitly approved. Use "proposed" or "pending review" instead
