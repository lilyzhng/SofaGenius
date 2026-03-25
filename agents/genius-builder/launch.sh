#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PATH="$HOME/.bun/bin:$PATH"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
