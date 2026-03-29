#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENT_NAME="genius-product"
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

# Start voice service if not already running
VOICE_DIR="$SCRIPT_DIR/voice-service"
if [ -d "$VOICE_DIR/dist" ]; then
  if ! lsof -i :3334 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Starting voice service..."
    cd "$VOICE_DIR"
    set -a && source "$SCRIPT_DIR/.env" && set +a
    nohup node dist/index.js > "$SCRIPT_DIR/voice-service.log" 2>&1 &
    echo "Voice service launched (PID: $!). Logs: $SCRIPT_DIR/voice-service.log"
    cd "$WORKTREE" 2>/dev/null || cd "$SCRIPT_DIR"
  else
    echo "Voice service already running on port 3334"
  fi
else
  echo "Voice service not built (no dist/), skipping"
fi

nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > "$SCRIPT_DIR/discord.log" 2>&1 &
echo "Launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
