# Agent Cron Scheduling — Design Doc

## Problem

Agent Computer VMs have no crontab installed and no systemd. Jackie needs to run the builder digest at 7 AM PT daily, and future tasks (evening calls, health checks) also need reliable scheduling. Current workarounds (bash sleep loops, manual reminders) are fragile and wasteful.

## Proposal

Install cron on the VM and use standard crontab entries for all scheduled agent tasks.

## Why Cron

- Battle-tested for 40+ years — no edge cases left to discover
- One line per task — easy to read, add, remove
- OS-level reliability — runs independently of agent processes
- DST-aware with `CRON_TZ` variable
- Zero custom code to maintain

Other options considered and rejected:
- **Bash sleep loops** — fragile, wasteful, no error recovery
- **OpenClaw heartbeat** — most OpenClaw users ended up using cron anyway
- **Node.js schedulers (croner, node-cron)** — adds a dependency for something the OS already does
- **Claude Code RemoteTrigger** — can't post to Discord (no MCP connector)

## Setup

### One-time install

```bash
apt-get install -y cron
service cron start
```

### Crontab entries

```crontab
# Use Pacific time for all entries
CRON_TZ=America/Los_Angeles

# Jackie: Morning builder digest at 7:00 AM PT
0 7 * * * /home/node/SofaGenius/agents/genius-jackie/trigger-digest.sh >> /tmp/digest-cron.log 2>&1

# Jackie: Evening reflection call at 10:45 PM PT (future)
# 45 22 * * * /home/node/SofaGenius/agents/genius-jackie/trigger-call.sh >> /tmp/call-cron.log 2>&1
```

### Verify

```bash
crontab -l          # list entries
grep CRON /var/log/syslog  # check execution logs
```

## Environment

`trigger-digest.sh` needs `JACKIE_BOT_TOKEN`. Two options:

1. **Source .env inline:** Add `source /home/node/SofaGenius/agents/genius-jackie/.env` to the top of trigger-digest.sh
2. **Set in crontab:** Add `JACKIE_BOT_TOKEN=...` line before the cron entry

Option 1 is cleaner — keeps secrets in one place.

## Persistence

Cron survives process restarts but NOT VM restarts on Agent Computer (container gets replaced). To handle this:

1. Add cron install + crontab setup to Jackie's launch script so it runs on every boot
2. Or add to `agents/startup-all.sh`

Proposed addition to `startup-all.sh`:

```bash
# Install and start cron if not running
if ! pgrep cron > /dev/null; then
  apt-get install -y cron 2>/dev/null
  service cron start
  # Load crontab
  crontab /home/node/SofaGenius/agents/crontab
fi
```

With a checked-in crontab file at `agents/crontab`:

```crontab
CRON_TZ=America/Los_Angeles
0 7 * * * bash -c 'source /home/node/SofaGenius/agents/genius-jackie/.env && /home/node/SofaGenius/agents/genius-jackie/trigger-digest.sh' >> /tmp/digest-cron.log 2>&1
```

## Scope

### In scope
- Install cron on Agent Computer VM
- Crontab entry for Jackie's morning digest (7 AM PT)
- Auto-setup on VM restart via startup script
- Checked-in crontab file for reproducibility

### Future (not in v1)
- Evening reflection call trigger (10:45 PM PT)
- Health check cron (verify all agents are running)
- Cron monitoring/alerting

## Open Questions

1. **Do we have sudo/root access** to install packages on Agent Computer? If not, we need an alternative.
2. **Does `CRON_TZ` work** on this VM's cron implementation? Need to verify after install.
