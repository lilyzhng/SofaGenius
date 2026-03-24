# Jackie Auto-Restart Supervisor — One-Pager

**Author:** genius-builder  |  **Date:** 2026-03-24  |  **Status:** Draft  |  **Owner:** genius-builder

## Problem

Jackie's Claude Code session on Agent Computer dies when the web terminal tab closes, on OOM, or on any crash. There's no supervisor — Jackie stays offline until someone manually restarts via the web terminal. This already happened today (March 24) during active use. Jackie needs to be truly always-on.

## Solution

A tmux-based supervisor wrapper around Jackie's launch script. tmux provides the PTY that Claude Code requires (can't run headless), survives SSH disconnect, and a bash loop handles crash recovery.

```bash
# supervisor.sh — runs inside tmux session
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.bun/bin:$PATH"
MAX_RAPID_CRASHES=10
RAPID_WINDOW=3600  # 1 hour
CRASH_TIMES=()

while true; do
    echo "[$(date)] Starting Jackie..."
    cd "$SCRIPT_DIR" && set -a && source .env && set +a
    START_TIME=$(date +%s)
    claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions
    EXIT_CODE=$?
    END_TIME=$(date +%s)
    RUNTIME=$((END_TIME - START_TIME))
    echo "[$(date)] Jackie exited with code $EXIT_CODE after ${RUNTIME}s. Restarting in 10s..."

    # Track rapid crashes (ran < 60s)
    if [ "$RUNTIME" -lt 60 ]; then
        CRASH_TIMES+=("$END_TIME")
        # Count crashes within the window
        CUTOFF=$((END_TIME - RAPID_WINDOW))
        RECENT=0
        for t in "${CRASH_TIMES[@]}"; do
            [ "$t" -ge "$CUTOFF" ] && RECENT=$((RECENT + 1))
        done
        if [ "$RECENT" -ge "$MAX_RAPID_CRASHES" ]; then
            echo "[$(date)] FATAL: $RECENT rapid crashes in 1 hour. Stopping supervisor."
            echo "[$(date)] Manual intervention required. Check logs."
            exit 1
        fi
        echo "[$(date)] Warning: rapid crash ($RECENT/$MAX_RAPID_CRASHES in window)"
    else
        CRASH_TIMES=()  # Reset counter on healthy run
    fi

    # Re-copy our custom plugin if it was overwritten
    PLUGIN_DIR="$HOME/.claude/plugins/cache/claude-plugins-official/discord"
    LATEST=$(ls -t "$PLUGIN_DIR" | head -1)
    if [ -f "$SCRIPT_DIR/server.ts.custom" ] && [ -n "$LATEST" ]; then
        cp "$SCRIPT_DIR/server.ts.custom" "$PLUGIN_DIR/$LATEST/server.ts"
        echo "[$(date)] Plugin restored from custom backup"
    fi

    sleep 10
done

# start.sh — entry point (creates/attaches tmux)
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SESSION="jackie"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Jackie is already running. Attach with: tmux attach -t $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" "bash $SCRIPT_DIR/supervisor.sh"
echo "Jackie started in tmux session '$SESSION'"
echo "Attach: tmux attach -t $SESSION"
echo "Logs: tmux capture-pane -t $SESSION -p"
```

**How it works:**
1. `start.sh` creates a tmux session named "jackie"
2. Inside tmux, `supervisor.sh` runs Claude Code in a loop
3. If Claude exits (crash, OOM, any reason) → waits 10s → restarts
4. On restart, re-copies our custom Discord plugin (fixes the overwrite issue)
5. tmux session survives terminal close, SSH disconnect, browser tab close

**Cron health check + reboot recovery:**
```bash
# Check every 5 min if tmux session exists, restart if not
*/5 * * * * tmux has-session -t jackie 2>/dev/null || bash /home/node/SofaGenius/agents/genius-jackie/start.sh

# Auto-start on VM reboot
@reboot sleep 30 && bash /home/node/SofaGenius/agents/genius-jackie/start.sh
```

The `@reboot` entry waits 30s for the system to fully initialize, then starts Jackie.

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Supervisor mechanism | tmux + bash loop | Claude Code needs PTY. tmux provides it and survives disconnects. systemd can't provide PTY easily. |
| Restart delay | 10 seconds | Prevents rapid restart loops on persistent errors. Long enough to let transient issues clear. |
| Plugin fix on restart | Copy custom server.ts | Plugin auto-updates overwrite our fork. Backup + restore on each restart solves it. |
| Health check | cron every 5 min | Catches case where tmux itself dies (VM restart, OOM killer). Cron survives everything. |

## Risks

- **Rapid restart loop** — if Claude Code crashes immediately every time, the 10s delay prevents CPU burn but doesn't fix root cause. Add max restart counter (e.g., stop after 10 consecutive crashes within 1 hour).
- **tmux killed by OOM** — the 5-minute cron health check catches this, but there's a 5-min gap.
- **Plugin overwrite race** — if Claude Code starts before the plugin copy finishes, it loads the vanilla plugin. The copy happens before `claude` starts, so this shouldn't happen.

## Plan

| Phase | What | Owner | Time |
|-------|------|-------|------|
| 1 | Write supervisor.sh + start.sh | Builder | 15 min |
| 2 | Back up custom server.ts on Jackie's VM | Builder | 5 min |
| 3 | Deploy scripts to Jackie's VM via SSH | Builder | 10 min |
| 4 | Set up cron health check | Builder | 5 min |
| 5 | Test: kill Claude process, verify auto-restart | Builder + Lily | 10 min |
| 6 | Test: close browser tab, verify tmux survives | Lily | 5 min |

**Total: ~50 minutes including testing.**

## Open Questions

1. **Max restart limit** — should the supervisor stop after N consecutive crashes? Or always restart?
2. **Logging** — should supervisor logs go to a file for debugging? Or just tmux scrollback?
3. **VM reboot** — does Agent Computer reboot VMs during maintenance? If so, need cron `@reboot` entry too.
