# Agent Computer Migration Plan

**Author:** Genius Builder | **Date:** 2026-03-25 | **Status:** Done

## Goal

Move all agents off Lily's laptop so they run 24/7 without depending on VS Code or the laptop being open.

## What Happened

VS Code crashed on March 24 from running 3 agents simultaneously. All agents went down. Jackie — already on Agent Computer — survived and was the only one who could respond.

## Approach: Same Setup, Cloud VM

All agents run on **Jackie's existing VM** (`jackie-chan`) as separate background processes. Same setup as Lily's laptop — just in the cloud.

**How identity works (same as local):**
- **`access.json`** in `~/.claude/channels/discord/` = shared team roster (who can talk, trusted bots)
- **`DISCORD_BOT_TOKEN`** in each agent's `.env` = individual identity. The env var overrides the file. `launch.sh` sources it before starting.

**Why one VM?**
- Agent Computer shares resources (2 vCPU, 8 GB RAM) across all VMs. Separate VMs don't give isolation.
- CLI processes are independent — one crashing doesn't affect others.
- Jackie's VM is already proven.

## The Fix

One line: `export PATH="$HOME/.bun/bin:$PATH"` in each launch script.

The Discord plugin runs on `bun`. Without bun in PATH, the plugin fails silently ("1 MCP server failed"). This was the only issue — everything else (shared `~/.claude/`, env var override, nohup) works exactly like local.

## How to Launch an Agent

**From SSH (background, always-on):**
```bash
ssh -p 443 jackie-chan@ssh.agentcomputer.ai
bash /home/node/SofaGenius/agents/genius-<name>/launch-bg.sh
```

`launch-bg.sh` wraps `launch.sh` with `nohup script -qc` for background operation. Process survives terminal close and SSH disconnect.

**From web terminal (foreground, for debugging):**
```bash
bash /home/node/SofaGenius/agents/genius-<name>/launch.sh
```

## Current Status

| Agent | PID | Status |
|-------|-----|--------|
| Jackie | 11625 | Online |
| CEO | 11894 | Online |
| Researcher | 12231 | Online |
| Builder | — | Still on laptop (last to migrate) |

## What Lily Needs to Do

- **For setup:** Nothing.
- **If auth expires:** `computer claude-login --machine jackie-chan`
- **To restart an agent:** SSH in and run `bash launch-bg.sh` from the agent's directory.

## Future: Per-Agent Access Control

Today all agents share one `access.json`. If agents later need different access policies (e.g., Jackie open to community, Builder restricted), use `CLAUDE_CONFIG_DIR` per agent to give each its own `~/.claude/` with its own `access.json`.

## Known Limitations

- **VM down = all agents down.** But the VM doesn't sleep or close its lid.
- **No auto-restart.** Crashed processes need manual relaunch.
- **Plugin auto-update.** May overwrite custom `server.ts`. Re-copy after updates.
- **No vault access.** `/Users/lilyzhang/Documents/lilyzhng/` doesn't exist on VM.
