#!/bin/bash
# SofaGenius Agent Supervisor
# Monitors all 4 agents and restarts any that go down.
# Uses PID files to track processes and /proc to verify they're alive.

set -euo pipefail

REPO_ROOT="/home/node/SofaGenius"
AGENTS_DIR="$REPO_ROOT/agents"
PID_DIR="/tmp/sofagenius-pids"
LOG_FILE="$REPO_ROOT/scripts/supervisor.log"
CHECK_INTERVAL=60

AGENTS=(genius-builder genius-ceo genius-researcher genius-jackie)

mkdir -p "$PID_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Find the PID of a running agent by checking /proc/*/cwd for the agent's worktree or source dir.
# Returns the PID if found, empty string if not.
find_agent_pid() {
  local agent="$1"
  local worktree="/home/node/worktrees/$agent/agents/$agent"
  local source_dir="$AGENTS_DIR/$agent"

  # Look through all claude processes
  for pid in $(pgrep -f "claude.*--channels" 2>/dev/null || true); do
    # Check the process's working directory
    local cwd
    cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null) || continue

    if [[ "$cwd" == "$worktree" ]] || [[ "$cwd" == "$source_dir" ]]; then
      echo "$pid"
      return 0
    fi
  done
  return 1
}

# Check if a PID is alive and is a claude process
is_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && [[ -d "/proc/$pid" ]] && grep -q "claude" "/proc/$pid/cmdline" 2>/dev/null
}

# Read stored PID for an agent
read_pid() {
  local agent="$1"
  local pidfile="$PID_DIR/$agent.pid"
  if [[ -f "$pidfile" ]]; then
    cat "$pidfile"
  fi
}

# Store PID for an agent
write_pid() {
  local agent="$1"
  local pid="$2"
  echo "$pid" > "$PID_DIR/$agent.pid"
}

# Relaunch an agent using its launch-bg.sh
relaunch_agent() {
  local agent="$1"
  local launch_script="$AGENTS_DIR/$agent/launch-bg.sh"

  if [[ ! -x "$launch_script" ]]; then
    log "ERROR: $launch_script not found or not executable"
    return 1
  fi

  log "RESTARTING $agent via $launch_script"
  local output
  output=$(bash "$launch_script" 2>&1)
  log "  launch output: $output"

  # Give it a moment to start, then find the new PID
  sleep 2
  local new_pid
  new_pid=$(find_agent_pid "$agent") || true
  if [[ -n "$new_pid" ]]; then
    write_pid "$agent" "$new_pid"
    log "  $agent restarted with PID $new_pid"
  else
    log "  WARNING: launched $agent but could not find its PID"
  fi
}

# On first run, discover any already-running agents
discover_existing() {
  for agent in "${AGENTS[@]}"; do
    local pid
    pid=$(find_agent_pid "$agent") || true
    if [[ -n "$pid" ]]; then
      write_pid "$agent" "$pid"
      log "DISCOVERED $agent already running with PID $pid"
    fi
  done
}

# Main check loop for one agent
check_agent() {
  local agent="$1"
  local stored_pid
  stored_pid=$(read_pid "$agent")

  # First check stored PID
  if [[ -n "$stored_pid" ]] && is_alive "$stored_pid"; then
    return 0  # Agent is running fine
  fi

  # Stored PID is stale or missing. Try to discover via cwd scan.
  local found_pid
  found_pid=$(find_agent_pid "$agent") || true
  if [[ -n "$found_pid" ]]; then
    write_pid "$agent" "$found_pid"
    return 0  # Agent is running, just update PID file
  fi

  # Agent is down
  log "DETECTED $agent is DOWN (stored PID: ${stored_pid:-none})"
  relaunch_agent "$agent"
}

# --- Entry point ---

log "=========================================="
log "Supervisor starting. Monitoring: ${AGENTS[*]}"
log "Check interval: ${CHECK_INTERVAL}s"
log "PID dir: $PID_DIR"
log "=========================================="

# Discover already-running agents on startup
discover_existing

while true; do
  for agent in "${AGENTS[@]}"; do
    check_agent "$agent"
  done
  sleep "$CHECK_INTERVAL"
done
