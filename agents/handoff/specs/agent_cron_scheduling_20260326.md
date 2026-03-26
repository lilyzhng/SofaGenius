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

Cron("0 7 * * *", { timezone: "America/Los_Angeles" }, () => {
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

### Option 4: Claude.ai Scheduled Triggers (RemoteTrigger)

Use Claude Code's built-in scheduling system. A cron expression fires a fresh remote session in Anthropic's cloud that runs a prompt.

Already set up: `trig_01Crs6tt1ENgW846sJXRWkqN` (currently disabled). The tribe digest trigger (`trig_012cckfShLfhRKQPX7V1debg`) ran successfully today — proven reliable.

**Pros:**
- Zero VM dependency — runs in Anthropic's cloud
- Already proven reliable (today's tribe digest ran without issues)
- No install, no custom code, no process to keep alive
- Lily can configure via claude.ai web UI
- Managed infrastructure — Anthropic handles uptime
- Native cron expressions with proper scheduling

**Cons:**
- No Discord MCP connector available — can't post to Discord directly from a trigger
- External dependency on Anthropic's infrastructure
- Trigger runs in a fresh sandbox — no access to Agent Computer VM state
- Limited to what the trigger can do without MCP connectors
- Workaround: trigger posts to Discord via raw curl + bot token (hardcoded in prompt or read from repo)

**Discord workaround:** The trigger has Bash access. It can curl the Discord API directly:
```bash
curl -sf -H "Authorization: Bot $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "<@1477895765698547844> Run the morning builder digest now."}' \
  "https://discord.com/api/v10/channels/1485075381613760603/messages"
```
This @mentions Jackie on Agent Computer, who then runs the actual digest. The trigger is just the alarm clock.

---

## Comparison

| Criteria | Cron | Node.js (croner) | Heartbeat | Scheduled Triggers |
|----------|------|-------------------|-----------|-------------------|
| Reliability | High — OS-level | Medium — Node process | Low — known issues | High — Anthropic cloud |
| Precision | Exact minute | Exact second | Up to 30 min late | Exact minute |
| Setup complexity | Install package | npm install + script | Custom daemon | Web UI config |
| Maintenance | Zero | Low | Medium | Zero |
| VM restart survival | Need startup script | Need startup script | Need startup script | N/A (cloud) |
| Root access needed | **Yes (blocker)** | No | No | No |
| Discord access | Via script | Via script | Via script | No MCP — curl workaround |
| DST handling | Built-in | Built-in | Manual | Built-in |
| Custom code | Zero | ~20 lines | ~100 lines | Zero |

## Recommendation

**Option 1 (Cron) is not viable** — Agent Computer blocks `sudo` and `cron` is not installed. No root access.

**Option 4 (Scheduled Triggers) for simple recurring tasks** like the morning digest. Already proven reliable today. The trigger @mentions Jackie via curl, Jackie runs the digest. Zero code, zero VM dependency. Enable the existing disabled trigger (`trig_01Crs6tt1ENgW846sJXRWkqN`) with the curl workaround for Discord.

**Option 2 (croner) for anything that must run on the VM** — e.g. tasks that need access to local files, agent state, or the voice service. Embed in an existing Node process.

**Option 3 (Heartbeat) not recommended** — OpenClaw's own users abandoned it for cron due to reliability issues.

**TL;DR:** Scheduled triggers as the primary scheduler, croner as backup for VM-local tasks.

## Open Questions

1. **Bot token in trigger prompt** — the scheduled trigger needs Jackie's bot token to curl Discord. Is it acceptable to include it in the trigger's prompt, or should we find another way?
