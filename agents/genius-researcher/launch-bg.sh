#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_NAME="genius-researcher"
WORKTREE="/home/node/worktrees/$AGENT_NAME/agents/$AGENT_NAME"
export PATH="$HOME/.bun/bin:$PATH"

# Source .env from original location (not in git, not in worktree)
set -a && source "$SCRIPT_DIR/.env" && set +a

# Work in worktree for git isolation; fall back to SCRIPT_DIR if worktree doesn't exist
if [ -d "$WORKTREE" ]; then
  export REPO_ROOT="/home/node/worktrees/$AGENT_NAME"
  cd "$WORKTREE"
else
  export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  cd "$SCRIPT_DIR"
fi

nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > "$SCRIPT_DIR/discord.log" 2>&1 &
echo "Launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
