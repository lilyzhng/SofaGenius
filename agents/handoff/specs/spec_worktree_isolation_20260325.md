# Spec: Git Worktree Isolation for Multi-Agent Repo

**Author:** genius-builder
**Date:** 2026-03-25
**Status:** Implementing

## Problem

All 4 agents share one working directory (`/home/node/SofaGenius`). When one agent checks out a branch, it affects everyone. This caused:
- Builder accidentally committing to CEO's branch (PR #61 incident)
- Risk of `git add` picking up another agent's uncommitted files
- Agents stepping on each other's git state

## Solution

Give each agent their own **git worktree** — a separate working directory backed by the same `.git` store. Each agent sees only their own branch and changes.

## Layout

```
/home/node/SofaGenius/                    # Main repo (shared .git)
/home/node/worktrees/genius-builder/      # Builder's worktree
/home/node/worktrees/genius-ceo/          # CEO's worktree
/home/node/worktrees/genius-researcher/   # Researcher's worktree
/home/node/worktrees/genius-jackie/       # Jackie's worktree
```

Each worktree starts on a detached HEAD at `origin/main`. Agents create feature branches from within their own worktree. Can't check out `main` directly since it's already used by the main repo — this is a git limitation (one branch per worktree).

## Setup Script

A one-time `setup-worktrees.sh` in the repo root:

```bash
#!/bin/bash
REPO_ROOT="/home/node/SofaGenius"
WORKTREE_BASE="/home/node/worktrees"

mkdir -p "$WORKTREE_BASE"

for agent in genius-builder genius-ceo genius-researcher genius-jackie; do
  if [ ! -d "$WORKTREE_BASE/$agent" ]; then
    git -C "$REPO_ROOT" worktree add "$WORKTREE_BASE/$agent" main
    echo "Created worktree for $agent at $WORKTREE_BASE/$agent"
  else
    echo "Worktree for $agent already exists"
  fi
done
```

## Launch Script Changes

Each agent's `launch-bg.sh` changes `cd` target from the agent's subdirectory in the shared repo to the agent's subdirectory in their worktree:

**Before:**
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
```

**After:**
```bash
WORKTREE="/home/node/worktrees/genius-builder"
cd "$WORKTREE/agents/genius-builder"
```

The `.env` file stays in the original location and is sourced with an absolute path:
```bash
set -a && source /home/node/SofaGenius/agents/genius-builder/.env && set +a
```

## What Changes Per Agent

| File | Change |
|------|--------|
| `launch-bg.sh` | `cd` into worktree + absolute `.env` path |
| `launch.sh` | No change (foreground debugging only, uses shared repo) |
| `.env` | Stays in original location (not in git) |
| `CLAUDE.md` | No change (relative paths still work within worktree) |

## What Doesn't Change

- Agent identity (`.env`, `DISCORD_BOT_TOKEN`)
- CLAUDE.md content
- Skills (shared via `agents/skills/`)
- Handoff directory (shared via `agents/handoff/`)
- Discord plugin config (`~/.claude/`)

## Constraints

- Each worktree can only have one branch checked out at a time (git limitation — that's the point)
- `git pull` in one worktree doesn't update others — each agent pulls independently
- Jackie's custom `server.ts.custom` needs to be accessible from her worktree

## Rollback

If worktrees cause issues:
```bash
git worktree remove /home/node/worktrees/genius-builder
# Revert launch scripts to use SCRIPT_DIR
```
