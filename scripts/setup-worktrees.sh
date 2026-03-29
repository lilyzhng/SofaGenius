#!/bin/bash
# One-time setup: create git worktrees for each agent
# Each agent gets their own working directory so git operations don't collide.

set -e

REPO_ROOT="/home/node/SofaGenius"
WORKTREE_BASE="/home/node/worktrees"

mkdir -p "$WORKTREE_BASE"

# Mark worktree directories as safe for git
for agent in genius-builder genius-growth genius-researcher genius-product; do
  git config --global --add safe.directory "$WORKTREE_BASE/$agent"
done

for agent in genius-builder genius-growth genius-researcher genius-product; do
  target="$WORKTREE_BASE/$agent"
  if [ -d "$target" ]; then
    echo "✓ $agent worktree already exists at $target"
  else
    # Detached HEAD at origin/main — agents create feature branches from here.
    # Can't checkout main directly since it's used by the main repo.
    git -C "$REPO_ROOT" worktree add --detach "$target" origin/main
    echo "✓ Created worktree for $agent at $target"
  fi
done

echo ""
echo "All worktrees ready. Agents should relaunch with updated launch-bg.sh."
echo "Worktrees:"
git -C "$REPO_ROOT" worktree list
