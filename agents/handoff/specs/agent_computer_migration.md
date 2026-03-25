# Agent Computer Migration Plan

**Author:** Genius Builder | **Date:** 2026-03-25 | **Status:** In Progress

## Goal

Move all agents off Lily's laptop so they run 24/7 without depending on VS Code or the laptop being open.

## What Happened

VS Code crashed on March 24 from running 3 agents simultaneously. All agents went down. Jackie — already on Agent Computer — survived and was the only one who could respond.

## Approach: Same Setup, Cloud VM

All agents run on **Jackie's existing VM** as separate background processes. This is the same setup as Lily's laptop — just in the cloud.

**How identity works (same as today):**
- **`access.json`** (shared) = the team roster. Defines who's allowed to talk and who's a trusted bot. All agents share the same one.
- **`DISCORD_BOT_TOKEN`** in each agent's `.env` = individual identity. `launch.sh` sources it before starting, so each agent becomes the right bot.

No special config isolation needed. The env var override is how the Discord plugin is designed to work.

**Why one VM?**
- Agent Computer shares resources (2 vCPU, 8 GB RAM, 25 GB disk) across all VMs at the account level. Separate VMs don't give resource isolation.
- The VS Code crash was an IDE problem, not a process problem. CLI processes are independent.
- Jackie's VM is already proven. One VM = one place to manage.

## What It Looks Like

```
Jackie's VM (ssh -p 443 jackie@ssh.agentcomputer.ai)

Processes:
  nohup: Jackie      → logs at agents/genius-jackie/discord.log
  nohup: CEO         → logs at agents/genius-ceo/discord.log
  nohup: Builder     → logs at agents/genius-builder/discord.log
  nohup: Researcher  → logs at agents/genius-researcher/discord.log

Files:
  /home/node/SofaGenius/              ← shared repo
  /home/node/.claude/                 ← shared config (auth, plugins, access.json)
  agents/genius-<name>/.env           ← per-agent identity (bot token, GitHub PAT)
  agents/genius-<name>/discord.log    ← per-agent logs
```

## How to Add an Agent

SSH into Jackie's VM and run from the agent's directory:

```bash
ssh -p 443 jackie@ssh.agentcomputer.ai
cd /home/node/SofaGenius/agents/genius-<name>
bash launch.sh
```

That's it. The agent's `.env` has the right bot token. `launch.sh` sources it and starts the process.

## Launch Script

Each agent's `launch.sh`:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && \
  nohup script -qc "claude --channels plugin:discord@claude-plugins-official \
  --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
echo "Launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
```

`nohup` + `script -qc` is required because Claude Code needs a PTY. Validated in PR #50 — survives terminal close and SSH disconnect.

## Migration Order

1. **CEO** — lightest workload, good smoke test
2. **Researcher** — heavier (web searches, long sessions), same setup
3. **Builder** — last, heaviest workload, wants process battle-tested first

## What Lily Needs to Do

- **For setup:** Nothing. Auth and plugins are already on Jackie's VM.
- **If auth expires:** Run `computer claude-login --machine jackie`.
- **To launch/restart an agent:** Open web terminal, run `bash launch.sh` from the agent's directory.

## Health Check

```bash
ps aux | grep "claude.*dangerously-skip" | grep -v grep
```

## Future: Per-Agent Access Control

Today all agents share one `access.json` (same team roster, same permissions). If we later need different agents to have different access — e.g., Jackie open to community members but Builder restricted to the team — we can split configs using `CLAUDE_CONFIG_DIR`:

```bash
# In launch.sh, point to a per-agent config dir
export CLAUDE_CONFIG_DIR="/home/node/.claude-<agent>"
```

Each agent would get its own `.claude-<agent>/` directory with its own `access.json`. Auth credentials and plugins can still be shared (symlinked or copied from `.claude/`). Only needed when access policies diverge — not now.

## Known Limitations

- **VM down = all agents down.** Same single-point-of-failure as the laptop, but the VM doesn't sleep or close its lid.
- **No auto-restart.** If a process crashes, someone relaunches it. `nohup` survives terminal closes but not process crashes.
- **Plugin auto-update.** May overwrite our custom `server.ts`. Re-copy from backup after updates.
- **No vault access.** `/Users/lilyzhang/Documents/lilyzhng/` doesn't exist on the VM. Agents work from the repo only.
- **30-60 second startup lag.** Discord plugin needs time to connect to the gateway. Normal.
