---
from: genius-ceo
to: genius-builder
created: 2026-03-22 17:18 PT
priority: high
---

## Task: Set up GitHub bot identity and raise PR #13 on SofaGenius

### Context
We restructured the agent org today. The SofaGenius repo now has an `agents/` and `handoff/` directory. The code is ready on branch `feature/agent-org` — you just need to push and create the PR under YOUR identity (genius-builder), not CEO's.

PR #13 exists but was created by CEO impersonating you. We need to redo it properly.

### Steps

1. Clone SofaGenius if you haven't:
   ```
   cd /Users/lilyzhang/Documents/lilyzhng/claude
   git clone https://github.com/lilyzhng/SofaGenius.git sofa-genius
   ```

2. Configure your git identity for this repo:
   ```
   cd sofa-genius
   git config user.name "Genius Builder"
   git config user.email "lilyzhng.ai+genius-builder@gmail.com"
   ```

3. Your GitHub token is in `/Users/lilyzhang/Documents/lilyzhng/autoresearch/.env.local` under `BUILDER_BOT_TOKEN`

4. Set remote to use your token:
   ```
   git remote set-url origin https://genius-builder:<BUILDER_BOT_TOKEN>@github.com/lilyzhng/SofaGenius.git
   ```

5. Checkout `feature/agent-org`, rewrite commits with your identity, force push, and create PR via GitHub API using your token.

6. **Important:** Clean the token from the remote URL after pushing:
   ```
   git remote set-url origin https://github.com/lilyzhng/SofaGenius.git
   ```

### Expected Outcome
- PR raised by `genius-builder` GitHub account
- All commits authored by "Genius Builder"
- CEO (sofagenius-ceo) will review and approve
- Lily (board) will merge

Status: NEEDS_CONTEXT — Builder needs to pick this up on next session
