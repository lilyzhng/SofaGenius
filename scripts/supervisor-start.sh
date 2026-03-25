#!/bin/bash
# Start the SofaGenius agent supervisor in the background.
# Usage: ./supervisor-start.sh
#   To stop: kill $(cat /tmp/sofagenius-pids/supervisor.pid)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SUPERVISOR="$SCRIPT_DIR/supervisor.sh"
PID_FILE="/tmp/sofagenius-pids/supervisor.pid"

mkdir -p /tmp/sofagenius-pids

# Check if supervisor is already running
if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "Supervisor already running (PID: $(cat "$PID_FILE"))"
  exit 0
fi

nohup bash "$SUPERVISOR" >> /dev/null 2>&1 &
SUPERVISOR_PID=$!
echo "$SUPERVISOR_PID" > "$PID_FILE"

echo "Supervisor started (PID: $SUPERVISOR_PID)"
echo "Logs: /home/node/SofaGenius/scripts/supervisor.log"
echo "Stop:  kill $SUPERVISOR_PID"
