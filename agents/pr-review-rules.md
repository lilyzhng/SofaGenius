# PR Review Rules

How agents review pull requests in this org.

## General Principles

- **Every PR gets at least one agent review** before Lily merges
- **Only Lily merges to main.** Agents raise and review — Lily approves the final merge.
- **Use your own GitHub identity** — never review as another agent or as Lily
- **Be constructive** — flag issues clearly, suggest fixes, don't just complain

## Review Format

### Use inline comments, not bulk reviews

**Do this:**
- Comment directly on the specific line(s) that need attention
- Quote the relevant code in your comment
- Suggest the fix inline when possible (use GitHub's "suggestion" feature)

**Don't do this:**
- Post a single giant review comment listing all issues
- Refer to line numbers without inline context ("line 47 has a bug")
- Leave vague comments ("this could be better")

### Comment Structure

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

### Severity Labels

Tag each comment with severity so the author knows what's blocking:

- **🔴 Blocking** — must fix before merge (bugs, security, broken functionality)
- **🟡 Should fix** — important but not a blocker (inconsistency, unclear spec, missing edge case)
- **🟢 Nit** — minor style/wording preference, author's call

## Review Checklist

When reviewing, check for:

- [ ] **Paths** — are they repo-root-relative? No `SofaGenius/` prefix?
- [ ] **Consistency** — does the diagram match the migration steps?
- [ ] **Status claims** — does it say "approved" or "confirmed" for things still under review?
- [ ] **Completeness** — are all open questions resolved, or clearly marked as TBD?
- [ ] **Safety** — are there destructive steps? Do they have safety gates?
- [ ] **Identity** — is the PR raised by the right agent's GitHub account?

## Review Workflow

1. **Author raises PR** with clear description and summary
2. **Reviewer posts inline comments** (not Discord messages about the PR)
3. **Author addresses each comment** — reply with what was fixed, or push back with reasoning
4. **Reviewer re-reviews** after fixes
5. **When satisfied**, reviewer approves (or says "LGTM" in a comment if they lack GitHub approval permissions)
6. **Lily does final review and merges**

## Cross-Agent Reviews

- **CEO reviews:** design specs, org decisions, content strategy
- **Builder reviews:** implementation feasibility, code quality, architecture
- **Researcher reviews:** research workflow impact, data pipeline changes
- **Any agent can flag:** security issues, broken paths, process violations

## Anti-Patterns

- **Don't review your own PR** — get another agent to review
- **Don't approve without reading** — if you don't have context, say so
- **Don't block on nits** — approve with nits noted, don't hold up the merge for style preferences
- **Don't discuss PR content in Discord instead of on the PR** — keep review discussion on GitHub so there's a paper trail
