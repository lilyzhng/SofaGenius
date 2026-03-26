#!/bin/bash
# Idempotent agent launcher — only starts agents that aren't running.
# Designed to be called by GitHub Actions watchdog or manually via SSH.
# Usage: bash /home/node/SofaGenius/agents/startup-all.sh

AGENTS_DIR="/home/node/SofaGenius/agents"
AGENTS=("genius-jackie" "genius-ceo" "genius-researcher" "genius-builder")
STARTED=0
ALREADY=0

log() { echo "[startup] $(date +'%Y-%m-%d %H:%M:%S') $1"; }

is_agent_running() {
    local agent="$1"
    # Check all script-wrapped claude processes and match by cwd
    for pid in $(pgrep -f "script.*claude" 2>/dev/null); do
        local cwd
        cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null)
        if echo "$cwd" | grep -q "$agent"; then
            echo "$pid"
            return 0
        fi
    done
    return 1
}

for agent in "${AGENTS[@]}"; do
    dir="$AGENTS_DIR/$agent"

    if [ ! -f "$dir/launch-bg.sh" ] || [ ! -f "$dir/.env" ]; then
        log "SKIP $agent — missing launch-bg.sh or .env"
        continue
    fi

    pid=$(is_agent_running "$agent")
    if [ $? -eq 0 ]; then
        log "OK $agent (PID $pid)"
        ALREADY=$((ALREADY + 1))
    else
        log "DOWN $agent — launching..."
        bash "$dir/launch-bg.sh"
        STARTED=$((STARTED + 1))
        sleep 10
    fi
done

log "Done. Launched: $STARTED, Already running: $ALREADY"
