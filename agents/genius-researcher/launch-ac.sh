#!/bin/bash
# Launch script for Agent Computer VM
# Uses per-agent CLAUDE_CONFIG_DIR for Discord bot token isolation
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export CLAUDE_CONFIG_DIR="/home/node/.claude-researcher"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
