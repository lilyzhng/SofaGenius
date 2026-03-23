#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
caffeinate -dims &
cd "$SCRIPT_DIR/../ceo" && source .env && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
kill %1 2>/dev/null
