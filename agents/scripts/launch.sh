#!/bin/bash
# Launch all agents — keep Mac awake
# Usage: bash agents/scripts/launch.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

caffeinate -s &
CAFFEINATE_PID=$!
trap "kill $CAFFEINATE_PID 2>/dev/null" EXIT

echo "Mac sleep prevention active (caffeinate PID: $CAFFEINATE_PID)"
echo "Launch each agent in a separate terminal tab:"
echo "  Tab 1: bash $SCRIPT_DIR/launch-builder.sh"
echo "  Tab 2: bash $SCRIPT_DIR/launch-ceo.sh"
echo "  Tab 3: bash $SCRIPT_DIR/launch-researcher.sh"
echo ""
echo "Press Ctrl+C to stop caffeinate and allow sleep again."

wait $CAFFEINATE_PID
