#!/bin/bash
# One-time setup: create git worktrees for each agent
# Each agent gets their own working directory so git operations don't collide.

set -e

REPO_ROOT="/home/node/SofaGenius"
WORKTREE_BASE="/home/node/worktrees"

mkdir -p "$WORKTREE_BASE"

# Mark worktree directories as safe for git
for agent in genius-builder genius-ceo genius-researcher genius-jackie; do
  git config --global --add safe.directory "$WORKTREE_BASE/$agent"
done

for agent in genius-builder genius-ceo genius-researcher genius-jackie; do
  target="$WORKTREE_BASE/$agent"
  if [ -d "$target" ]; then
    echo "✓ $agent worktree already exists at $target"
  else
    # Each worktree starts on a detached HEAD at main to avoid branch conflicts
    # Agents create their own branches from within their worktree
    git -C "$REPO_ROOT" worktree add --detach "$target"
    git -C "$target" checkout main 2>/dev/null || git -C "$target" checkout -b "worktree-$agent" origin/main
    echo "✓ Created worktree for $agent at $target"
  fi
done

echo ""
echo "All worktrees ready. Agents should relaunch with updated launch-bg.sh."
echo "Worktrees:"
git -C "$REPO_ROOT" worktree list
