# Agent Computer Migration Plan

**Author:** Genius Builder | **Date:** 2026-03-25 | **Status:** In Progress | **Owner:** genius-builder

## Problem

Running 3+ agents in VS Code on Lily's laptop is unstable — VS Code crashed from resource exhaustion on March 24. Agents go down when VS Code crashes or the laptop closes. Jackie already proved Agent Computer works for always-on operation.

## Decision: Single VM, Multiple Processes

All agents run on **Jackie's existing VM** as separate `nohup` processes. Each agent gets its own `CLAUDE_CONFIG_DIR` for Discord bot token isolation.

**Why single VM, not multiple?**
- The VS Code crash was an IDE problem, not a process problem. CLI processes are independent — one crashing doesn't affect others.
- Agent Computer resources (2 vCPU / 8 GB RAM) are shared across all VMs at the account level. Separate VMs give zero resource isolation.
- Jackie's VM is already proven (10+ hours uptime). One VM = one SSH target, one place to debug.
- Simpler setup: no per-VM `computer create`, no per-VM `claude-login`, no cross-VM file syncing.

**Cost:** $20/mo plan unchanged. Using 1 VM (Jackie's). 24 remaining for other projects.

## Architecture

```
Jackie VM (jackie@ssh.agentcomputer.ai)
├── /home/node/
│   ├── SofaGenius/                    # Shared repo (all agents)
│   │   └── agents/
│   │       ├── genius-jackie/         # Jackie's .env, launch.sh
│   │       ├── genius-ceo/            # CEO's .env, launch.sh
│   │       ├── genius-builder/        # Builder's .env, launch.sh
│   │       └── genius-researcher/     # Researcher's .env, launch.sh
│   ├── .claude/                       # Jackie's config (shared auth source)
│   ├── .claude-ceo/                   # CEO's config (Discord bot token)
│   ├── .claude-builder/               # Builder's config (Discord bot token)
│   └── .claude-researcher/            # Researcher's config (Discord bot token)
│
│   Running processes:
│   ├── nohup: Jackie       (PID in jackie.pid,     logs: genius-jackie/discord.log)
│   ├── nohup: CEO          (PID in ceo.pid,        logs: genius-ceo/discord.log)
│   ├── nohup: Builder      (PID in builder.pid,    logs: genius-builder/discord.log)
│   └── nohup: Researcher   (PID in researcher.pid, logs: genius-researcher/discord.log)
```

**Per-agent config:** `CLAUDE_CONFIG_DIR` env var points each agent to its own `.claude-<name>/` directory. Auth credentials are shared (copied from Jackie's `.claude/`). Discord bot tokens are per-agent.

## Migration Order

### Phase 1: CEO (first)
- [x] Create `/home/node/.claude-ceo/` (copy credentials + settings + plugins from `.claude/`)
- [x] Configure CEO's Discord bot token + access.json
- [x] Copy CEO's `.env` to `agents/genius-ceo/.env` on VM
- [ ] Update CEO's `launch.sh` with `CLAUDE_CONFIG_DIR` + `nohup`
- [ ] Launch and test

### Phase 2: Researcher
- [ ] Create `/home/node/.claude-researcher/` (same pattern)
- [ ] Configure Researcher's Discord bot token + access.json
- [ ] Copy Researcher's `.env`
- [ ] Update `launch.sh`, launch and test

### Phase 3: Builder (last)
- [ ] Create `/home/node/.claude-builder/` (same pattern)
- [ ] Configure Builder's Discord bot token + access.json
- [ ] Copy Builder's `.env`
- [ ] Verify git push/PR workflows work from VM
- [ ] Update `launch.sh`, launch and test

## Per-Agent Setup (runbook)

All commands run on Jackie's VM (`ssh -p 443 jackie@ssh.agentcomputer.ai`):

```bash
# 1. Create per-agent config dir
AGENT=ceo  # change per agent
mkdir -p /home/node/.claude-$AGENT/channels/discord
cp /home/node/.claude/.credentials.json /home/node/.claude-$AGENT/
cp /home/node/.claude/settings.json /home/node/.claude-$AGENT/
cp -r /home/node/.claude/plugins /home/node/.claude-$AGENT/

# 2. Configure Discord bot token + access
# (edit these files with the agent's specific bot token)
vi /home/node/.claude-$AGENT/channels/discord/.env
vi /home/node/.claude-$AGENT/channels/discord/access.json

# 3. Launch
cd /home/node/SofaGenius/agents/genius-$AGENT
bash launch.sh
```

## Launch Script

Each agent's `launch.sh` updated to work on Agent Computer:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export CLAUDE_CONFIG_DIR="/home/node/.claude-AGENT_NAME"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && \
  nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
echo "Agent launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
```

**Why `nohup` + `script -qc`:** Claude Code needs a PTY — `nohup` alone triggers `--print` mode. `script -qc` provides a pseudo-TTY. Validated in PR #50, tested 16+ hours.

## Health Check

Quick script to see which agents are running:

```bash
#!/bin/bash
# agents-status.sh — run on Jackie's VM
echo "=== Agent Processes ==="
for agent in jackie ceo builder researcher; do
  pid=$(pgrep -f "claude-$agent" 2>/dev/null || pgrep -f "genius-$agent" 2>/dev/null)
  if [ -n "$pid" ]; then
    echo "✅ $agent (PID: $pid)"
  else
    echo "❌ $agent — not running"
  fi
done
```

## Lily's Role (minimal)

- **One-time:** Nothing! Auth credentials shared from Jackie's existing `.claude/`.
- **If auth expires:** Run `computer claude-login --machine jackie` — all agents share the same credentials.
- **To launch an agent:** Open Jackie's web terminal, run `bash /home/node/SofaGenius/agents/genius-<name>/launch.sh`

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Process dies when terminal closes | Solved: `nohup` + `script -qc` (PR #50). Survives terminal close + SSH disconnect. |
| VM goes down = all agents down | Platform-level risk. Same whether 1 or 4 VMs (shared infra). Monitor and relaunch. |
| Plugin auto-update overwrites custom server.ts | Backup persists in config dir. Re-copy after plugin updates. |
| Auth expiry | Re-auth on Jackie's VM propagates to all agents via shared `.credentials.json`. |
| Git conflicts from concurrent writes | Normal git workflow. Agents pull before pushing, handle merge conflicts. |

## Post-Migration Cleanup

1. Remove local VS Code agent launch configs
2. Update CLAUDE.md vault paths if needed (`/home/node/` vs `/Users/lilyzhang/Documents/lilyzhng/`)
3. Consider migrating Jackie to `.claude-jackie/` for naming consistency
