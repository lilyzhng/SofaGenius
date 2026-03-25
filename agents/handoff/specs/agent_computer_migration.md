# Agent Computer Migration Plan

**Author:** Genius Builder | **Date:** 2026-03-25 | **Status:** In Progress

## Goal

Move all agents off Lily's laptop so they run 24/7 without depending on VS Code or the laptop being open.

## What Happened

VS Code crashed on March 24 from running 3 agents simultaneously. All agents went down. Jackie — already on Agent Computer — survived and was the only one who could respond. This confirmed the approach works and we should move everyone.

## Approach: Single VM, Multiple Processes

All agents run on **Jackie's existing VM** (`jackie`) as separate background processes. This mirrors what we do today on Lily's laptop — multiple agents, each with their own terminal — just in the cloud instead.

**Why one VM, not four?**
- Agent Computer shares resources (2 vCPU, 8 GB RAM, 25 GB disk) across all VMs at the account level. Separate VMs don't give resource isolation — it's the same pool.
- The VS Code crash was an IDE problem, not a process isolation problem. CLI processes are independent — one crashing doesn't affect others.
- One VM = one place to SSH into, one place to check logs, one place to restart things.
- Jackie's VM is already set up and proven (10+ hours always-on uptime).

**Why each agent needs its own config directory:**
Each agent has a different Discord bot. The Discord plugin reads its bot token from `$CLAUDE_CONFIG_DIR/channels/discord/.env`. Without separate config dirs, all agents would respond as the same bot. The `CLAUDE_CONFIG_DIR` env var solves this — each agent points to its own `.claude-<name>/` directory.

Auth credentials (`.credentials.json`) are shared — copied from Jackie's existing `.claude/`. No extra `claude-login` needed.

## What It Looks Like

```
Jackie's VM (ssh -p 443 jackie@ssh.agentcomputer.ai)

Processes:
  nohup: Jackie      → logs at agents/genius-jackie/discord.log
  nohup: CEO         → logs at agents/genius-ceo/discord.log
  nohup: Builder     → logs at agents/genius-builder/discord.log
  nohup: Researcher  → logs at agents/genius-researcher/discord.log

Files:
  /home/node/SofaGenius/          ← shared repo, same as local
  /home/node/.claude/             ← Jackie's config (existing)
  /home/node/.claude-ceo/         ← CEO's config (Discord bot token)
  /home/node/.claude-builder/     ← Builder's config
  /home/node/.claude-researcher/  ← Researcher's config
```

Each agent's `.env` (GitHub PAT, Discord token) stays in `agents/genius-<name>/.env` — same as today.

## How to Add an Agent

On Jackie's VM (`ssh -p 443 jackie@ssh.agentcomputer.ai`):

```bash
# 1. Create config dir + copy shared auth
AGENT=ceo
mkdir -p /home/node/.claude-$AGENT/channels/discord
cp /home/node/.claude/.credentials.json /home/node/.claude-$AGENT/
cp /home/node/.claude/settings.json /home/node/.claude-$AGENT/
cp -r /home/node/.claude/plugins /home/node/.claude-$AGENT/

# 2. Set the agent's Discord bot token
echo "DISCORD_BOT_TOKEN=<token>" > /home/node/.claude-$AGENT/channels/discord/.env
# Copy access.json (controls who can talk to this agent)
cp /home/node/.claude/channels/discord/access.json /home/node/.claude-$AGENT/channels/discord/

# 3. Launch
cd /home/node/SofaGenius/agents/genius-$AGENT
bash launch.sh
```

## Launch Script

Each agent's `launch.sh` is the same pattern:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export CLAUDE_CONFIG_DIR="/home/node/.claude-AGENT_NAME"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && \
  nohup script -qc "claude --channels plugin:discord@claude-plugins-official \
  --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
echo "Launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
```

`nohup` + `script -qc` is required because Claude Code needs a PTY. `nohup` alone triggers `--print` mode. This pattern was validated in PR #50 — survives terminal close and SSH disconnect.

Note: Jackie's current `launch.sh` runs in the foreground without `CLAUDE_CONFIG_DIR` (she uses the default `~/.claude/`). She can keep her existing setup or be updated for consistency later.

## Migration Order

1. **CEO** — lightest workload, good smoke test
2. **Researcher** — heavier (web searches, long sessions), but same setup
3. **Builder** — last, heaviest workload (coding, git, tests). Wants process battle-tested first.

## What Lily Needs to Do

- **Nothing for setup.** Auth credentials are shared from Jackie's existing login.
- **If auth expires:** Run `computer claude-login --machine jackie` from your laptop. All agents share the same credentials.
- **To launch/restart an agent:** Open web terminal (https://8788--jackie.computer.agentcomputer.ai), run `bash /home/node/SofaGenius/agents/genius-<name>/launch.sh`

## Health Check

```bash
# Quick check: which agents are running?
ps aux | grep "claude.*dangerously-skip" | grep -v grep
```

## Known Limitations

- **VM down = all agents down.** Same single-point-of-failure as the laptop, but the VM doesn't sleep or run out of laptop RAM. If Agent Computer has an outage, we wait.
- **No auto-restart.** If a process crashes, someone needs to relaunch it manually. Agent Computer doesn't have a built-in supervisor. We use `nohup` to survive terminal closes, but not process crashes.
- **Plugin auto-update.** Claude Code may overwrite our custom `server.ts` (fork with create_thread, polls, trustedBots). Re-copy from backup after plugin updates.
- **No vault access.** On the laptop, agents access `/Users/lilyzhang/Documents/lilyzhng/` for datasets and journals. This path doesn't exist on the VM. Agents work from the repo only. Files needed for research should be committed or fetched fresh.
- **30-60 second startup lag.** Discord plugin takes time to connect after launch. Not a bug — it's the WebSocket gateway connection.
