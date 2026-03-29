---
name: jackie-ops
description: Manage Genius Product's Fly.io deployment. Restart gateway, check/update cron schedules, view logs, and verify service health.
argument-hint: <action> (restart | cron-list | cron-update | status | logs)
allowed-tools: Bash
---

# Jackie Ops -- Manage Genius Product's Fly.io Deployment

> **DEPRECATION NOTICE (2026-03-23):** Genius Product is shut down on OpenClaw/Fly.io and migrating to Hermes Agent. These commands reference the OpenClaw deployment which is no longer active. This skill will be rewritten for Hermes once migration is complete. See PR #33 for migration spec.

Genius Product (Jackie) runs on Fly.io as a supervised process. Use this skill to manage the deployment.

## Infrastructure Details

| Detail | Value |
|--------|-------|
| **Fly app name** | `openclaw-sofagenius` |
| **Supervisor socket** | `/tmp/supervisor.sock` |
| **Supervisor config** | `/etc/supervisor/conf.d/openclaw-sofagenius.conf` |
| **Cron config** | `/data/cron/jobs.json` |
| **Services** | `openclaw-gateway` (main bot), `sofagenius-backend` (API) |

## Actions

### Restart Gateway

Restarts Jackie's main process. Use after config changes (cron, env, etc).

```bash
fly ssh console -a openclaw-sofagenius -C "supervisorctl -s unix:///tmp/supervisor.sock restart openclaw-gateway"
```

### Check Service Status

```bash
fly ssh console -a openclaw-sofagenius -C "supervisorctl -s unix:///tmp/supervisor.sock status"
```

Both services should show `RUNNING`.

### View Cron Schedules

```bash
fly ssh console -a openclaw-sofagenius -C "cat /data/cron/jobs.json"
```

Key fields per job:
- `schedule.expr` — cron expression (e.g. `0 7 * * *` = 7 AM)
- `schedule.tz` — timezone (should be `America/Los_Angeles`)
- `state.nextRunAtMs` — next scheduled run (epoch ms)
- `enabled` — whether the job is active

### View Logs

```bash
fly logs -a openclaw-sofagenius
```

### Full App Restart

If supervisor restart doesn't fix things, restart the entire Fly machine:

```bash
fly apps restart openclaw-sofagenius
```

**Warning:** This restarts ALL services including the backend. Use only if supervisor-level restart doesn't work.

## Current Cron Jobs

1. **Morning Builder Digest** — `0 7 * * *` PT → posts to #daily-digest
2. **Evening Reflection Call** — `45 22 * * *` PT → voice call with Lily

## Troubleshooting

- **"no such file" on supervisor socket** — The socket is at `/tmp/supervisor.sock`, NOT `/var/run/supervisor.sock`. Always use the `-s unix:///tmp/supervisor.sock` flag.
- **App name confusion** — The app is `openclaw-sofagenius`, not `openclaw-jackie`.
- **Cron not firing after update** — You must restart the gateway after editing `jobs.json` for changes to take effect.
