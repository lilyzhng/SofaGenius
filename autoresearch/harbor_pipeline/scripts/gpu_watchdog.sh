#!/bin/bash
# GPU Watchdog — kills training if GPU utilization stays at 0% for too long
#
# Runs nvidia-smi every 30s. If GPU utilization is 0% for 5 consecutive checks
# (2.5 minutes), logs a warning. After 10 consecutive checks (5 minutes), kills
# the training process to stop wasting credits.
#
# Usage: bash gpu_watchdog.sh &  (run in background alongside training)

ZERO_COUNT=0
ZERO_THRESHOLD_WARN=5    # 2.5 min
ZERO_THRESHOLD_KILL=10   # 5 min
CHECK_INTERVAL=30
GRACE_PERIOD=120          # 2 min grace period at start (model loading)

echo "[GPU Watchdog] Starting. Grace period: ${GRACE_PERIOD}s"
sleep $GRACE_PERIOD
echo "[GPU Watchdog] Grace period over. Monitoring GPU utilization."

while true; do
    # Get GPU utilization percentage
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')

    if [ -z "$GPU_UTIL" ]; then
        echo "[GPU Watchdog] nvidia-smi failed — GPU not accessible"
        sleep $CHECK_INTERVAL
        continue
    fi

    TIMESTAMP=$(date '+%H:%M:%S')

    if [ "$GPU_UTIL" -eq 0 ] 2>/dev/null; then
        ZERO_COUNT=$((ZERO_COUNT + 1))
        echo "[GPU Watchdog] $TIMESTAMP GPU: ${GPU_UTIL}% (zero count: $ZERO_COUNT/$ZERO_THRESHOLD_KILL)"

        if [ $ZERO_COUNT -ge $ZERO_THRESHOLD_KILL ]; then
            echo "[GPU Watchdog] ⚠️  GPU has been at 0% for $(($ZERO_COUNT * $CHECK_INTERVAL))s — KILLING TRAINING"
            echo "[GPU Watchdog] This likely means the model isn't training. Check logs."
            # Kill the parent process group
            kill -TERM 0 2>/dev/null
            exit 1
        elif [ $ZERO_COUNT -ge $ZERO_THRESHOLD_WARN ]; then
            echo "[GPU Watchdog] ⚠️  Warning: GPU idle for $(($ZERO_COUNT * $CHECK_INTERVAL))s"
        fi
    else
        if [ $ZERO_COUNT -gt 0 ]; then
            echo "[GPU Watchdog] $TIMESTAMP GPU: ${GPU_UTIL}% (recovered from idle)"
        fi
        ZERO_COUNT=0
    fi

    sleep $CHECK_INTERVAL
done
