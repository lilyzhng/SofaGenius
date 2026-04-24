#!/bin/bash
# Watchdog for Agent Computer — checks every 5 minutes if agents are alive, restarts dead ones.
# Run with: nohup bash /home/node/SofaGenius/agents/watchdog.sh > /home/node/watchdog.log 2>&1 &
#
# Each agent runs as: nohup script -qc "claude --channels ..." /dev/null
# We detect them by checking for a claude process whose cwd matches the agent directory.

REPO_ROOT="/home/node/SofaGenius"
AGENTS_DIR="$REPO_ROOT/agents"
CHECK_INTERVAL=300  # 5 minutes
LOG_PREFIX="[watchdog]"

# Agents to monitor — add/remove as needed
AGENTS=("genius-jackie" "genius-ceo" "genius-researcher" "genius-builder")

log() {
    echo "$LOG_PREFIX $(date '+%Y-%m-%d %H:%M:%S') $1"
}

is_agent_running() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"
    # Check if there's a claude process with this agent's directory in its environment/cwd
    # We look for the script wrapper that has the agent's launch.sh or directory
    pgrep -f "claude.*--channels.*discord" | while read pid; do
        # Check if this process's cwd or cmdline relates to our agent
        if ls -l /proc/$pid/cwd 2>/dev/null | grep -q "$agent_name"; then
            echo "$pid"
            return 0
        fi
    done
    # Fallback: check if any claude process was started from this agent's directory
    # by looking for the agent name in process environment
    local pid
    pid=$(pgrep -f "script.*claude.*--channels" | while read p; do
        if cat /proc/$p/environ 2>/dev/null | tr '\0' '\n' | grep -q "$agent_name"; then
            echo "$p"
            break
        fi
        # Also check the cwd symlink
        if readlink /proc/$p/cwd 2>/dev/null | grep -q "$agent_name"; then
            echo "$p"
            break
        fi
    done)
    [ -n "$pid" ]
}

start_agent() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    if [ ! -f "$agent_dir/launch.sh" ]; then
        log "SKIP $agent_name — no launch.sh found"
        return 1
    fi

    if [ ! -f "$agent_dir/.env" ]; then
        log "SKIP $agent_name — no .env found"
        return 1
    fi

    log "STARTING $agent_name..."

    export PATH="$HOME/.bun/bin:$PATH"
    cd "$agent_dir"
    set -a && source .env && set +a

    nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" \
        /dev/null > "$agent_dir/discord.log" 2>&1 &

    local new_pid=$!
    log "STARTED $agent_name (PID: $new_pid)"

    # Wait for Discord plugin to connect (30-60s warmup)
    sleep 5
}

# --- PID file approach: track which PIDs we launched ---
PID_DIR="/home/node/.agent-pids"
mkdir -p "$PID_DIR"

start_agent_tracked() {
    local agent_name="$1"
    local agent_dir="$AGENTS_DIR/$agent_name"

    if [ ! -f "$agent_dir/launch.sh" ]; then
        log "SKIP $agent_name — no launch.sh found"
        return 1
    fi

    if [ ! -f "$agent_dir/.env" ]; then
        log "SKIP $agent_name — no .env found"
        return 1
    fi

    log "STARTING $agent_name..."

    # Launch in a subshell so env vars don't leak between agents
    (
        export PATH="$HOME/.bun/bin:$PATH"
        cd "$agent_dir"
        set -a && source .env && set +a
        nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" \
            /dev/null > "$agent_dir/discord.log" 2>&1 &
        echo $! > "$PID_DIR/$agent_name.pid"
        log "STARTED $agent_name (PID: $!)"
    )

    sleep 5
}

is_agent_running_tracked() {
    local agent_name="$1"
    local pid_file="$PID_DIR/$agent_name.pid"

    if [ ! -f "$pid_file" ]; then
        return 1
    fi

    local pid
    pid=$(cat "$pid_file")

    # Check if the PID is still alive and is actually a script/claude process
    if kill -0 "$pid" 2>/dev/null; then
        # Verify it's still our agent process (not a recycled PID)
        if cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | grep -q "script.*claude\|claude.*channels"; then
            return 0
        fi
        # The script wrapper might have a child claude process — check children
        if pgrep -P "$pid" 2>/dev/null | while read child; do
            cat /proc/$child/cmdline 2>/dev/null | tr '\0' ' ' | grep -q "claude"
        done; then
            return 0
        fi
        # PID alive but not our process — stale
        log "STALE PID $pid for $agent_name (process recycled)"
        rm -f "$pid_file"
        return 1
    fi

    # PID is dead
    rm -f "$pid_file"
    return 1
}

# --- Main loop ---
log "=== Watchdog starting ==="
log "Monitoring agents: ${AGENTS[*]}"
log "Check interval: ${CHECK_INTERVAL}s"

while true; do
    for agent in "${AGENTS[@]}"; do
        if is_agent_running_tracked "$agent"; then
            log "OK $agent is running"
        else
            log "DOWN $agent — restarting"
            start_agent_tracked "$agent"
        fi
    done

    log "--- sleeping ${CHECK_INTERVAL}s ---"
    sleep "$CHECK_INTERVAL"
done
