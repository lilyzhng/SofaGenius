#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
caffeinate -dims &
CAFFEINATE_PID=$!
cd "$SCRIPT_DIR/../genius-researcher" && source .env && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
kill $CAFFEINATE_PID 2>/dev/null
