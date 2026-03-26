# Agent Scheduling — Design Doc

## Problem

Agent Computer VMs have no crontab installed and no systemd. Jackie needs to run the builder digest at 7 AM PT daily, and future tasks (evening calls, health checks) also need reliable scheduling. Current workarounds (bash sleep loops, manual reminders) are fragile and wasteful.

## Options

### Option 1: Install Cron

Install the standard Unix cron daemon on the VM.

```bash
apt-get install -y cron && service cron start
```

```crontab
CRON_TZ=America/Los_Angeles
0 7 * * * bash -c 'source /home/node/SofaGenius/agents/genius-jackie/.env && /home/node/SofaGenius/agents/genius-jackie/trigger-digest.sh' >> /tmp/digest-cron.log 2>&1
```

**Pros:**
- Battle-tested for 40+ years — no edge cases left to discover
- One line per task — easy to read, add, remove
- OS-level — runs independently of agent processes
- DST-aware with `CRON_TZ`
- Zero custom code to maintain
- Every developer already knows cron syntax

**Cons:**
- Requires package install (may need root/sudo)
- Does not survive VM restart on Agent Computer — container gets replaced, cron daemon dies. Need to re-install and re-load crontab on every boot (via startup script)
- No built-in alerting if a job fails silently
- Cron environment is minimal — scripts must source their own env vars

**Persistence strategy:** Check-in a `agents/crontab` file. On boot, `startup-all.sh` installs cron and loads it:
```bash
if ! pgrep cron > /dev/null; then
  apt-get install -y cron 2>/dev/null
  service cron start
  crontab /home/node/SofaGenius/agents/crontab
fi
```

---

### Option 2: Node.js Scheduler (croner)

Run a lightweight Node.js process with the `croner` library that handles all scheduled tasks.

```typescript
import { Cron } from "croner";

Cron("0 14 * * *", { timezone: "America/Los_Angeles" }, () => {
  // 7 AM PT — trigger digest
  execFileSync("bash", ["trigger-digest.sh"]);
});
```

**Pros:**
- No OS-level install required — just `npm install croner`
- TypeScript-native, DST-aware, built-in error handling (won't crash on exception)
- Can run as part of an existing Node process (e.g. Jackie's voice service)
- Portable — works on any platform with Node.js
- Can integrate with the agent's own logging/monitoring

**Cons:**
- Another process to keep alive (or embedded in voice service, coupling concerns)
- If the Node process dies, all scheduled tasks stop
- Adds a dependency for something the OS can do natively
- Need a supervisor (tmux loop) to restart if it crashes

**Persistence strategy:** Embed in voice service or run as separate `scheduler.js`. Wrap in tmux supervisor loop for auto-restart.

---

### Option 3: OpenClaw-Style Heartbeat

A lightweight daemon that fires at a configurable interval. Agent reads a config file (like HEARTBEAT.md) and decides whether to act based on the current time and last-run state.

```json
{
  "heartbeat": {
    "every": "30m",
    "activeHours": { "start": "06:00", "end": "23:00", "timezone": "America/Los_Angeles" }
  },
  "tasks": [
    { "name": "builder-digest", "time": "07:00", "script": "trigger-digest.sh", "lastRun": "" },
    { "name": "evening-call", "time": "22:45", "script": "trigger-call.sh", "lastRun": "" }
  ]
}
```

Daemon wakes every 30 minutes, checks if any task's time has passed since `lastRun`, fires it, updates `lastRun`.

**Pros:**
- Self-contained — config + state in one file
- Flexible — can add tasks without touching system config
- Natural fit for agent workflows (agents already read config files)
- No root/package install needed

**Cons:**
- OpenClaw's heartbeat had known reliability issues — users frequently reported missed fires and switched to cron instead
- Up to 30 minutes of delay (fires at next heartbeat, not at exact time)
- Custom code to maintain — error handling, state management, timezone logic
- Need to handle edge cases: DST transitions, duplicate fires, crash recovery
- Another process to keep alive

**Known pain points from OpenClaw community:**
- Heartbeat interval too coarse for time-sensitive tasks (30 min granularity)
- State file corruption when agent crashes mid-write
- DST transitions caused double-fires or missed fires
- "lastRun" tracking broke when VM clock drifted
- Most power users abandoned heartbeat for cron within weeks

---

## Comparison

| Criteria | Cron | Node.js (croner) | Heartbeat |
|----------|------|-------------------|-----------|
| Reliability | High — OS-level daemon | Medium — depends on Node process | Low — known issues |
| Precision | Exact minute | Exact second | Up to 30 min late |
| Setup complexity | Install package + crontab | npm install + script | Custom daemon code |
| Maintenance | Zero | Low (library updates) | Medium (custom code) |
| VM restart survival | Need startup script | Need startup script | Need startup script |
| Root access needed | Yes (to install) | No | No |
| DST handling | Built-in (`CRON_TZ`) | Built-in | Manual (error-prone) |
| Failure visibility | Syslog + email | Custom logging | Custom logging |
| Learning curve | None (everyone knows cron) | Low | Medium |

## Recommendation

**Option 1 (Cron)** if we have root access to install packages. It's the simplest, most reliable, and requires zero custom code. The only downside is needing to reinstall on VM restart, which the startup script handles.

**Option 2 (croner)** as fallback if we can't install system packages. Embed it in an existing Node process to avoid another thing to keep alive.

**Option 3 (Heartbeat)** is not recommended. OpenClaw's own users abandoned it for cron due to reliability issues.

## Open Questions

1. **Do we have root access** to install packages on Agent Computer? This determines Option 1 vs 2.
2. **Should we embed the scheduler in the voice service** (keeps it simple) or run it separately (isolation)?
