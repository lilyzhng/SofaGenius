# Agent Computer Migration Plan

**Author:** Genius Builder | **Date:** 2026-03-25 | **Status:** In Progress | **Owner:** genius-builder

## Problem

Running 3+ agents in VS Code on Lily's laptop is unstable — VS Code crashed from resource exhaustion on March 24. Agents go down when VS Code crashes or the laptop closes. Jackie already proved Agent Computer works for always-on operation.

## Decision: Separate VMs + Per-Agent Config

Each agent gets its own VM on Agent Computer. All VMs share `/home/node/` via EFS (shared filesystem mode), but each agent gets an isolated `CLAUDE_CONFIG_DIR` to separate Discord bot tokens and plugin config.

**Why separate VMs?** The whole reason we're migrating is that 3 agents in one process crashed. Separate VMs give us:
- Fault isolation — one crash doesn't take down the team
- Independent restarts
- Clean resource boundaries
- Easier debugging

**Cost:** $20/mo for 25 VMs. 4 agents = 4 VMs. 21 remaining.

## Architecture

```
/home/node/
├── SofaGenius/                    # Shared repo (all agents)
│   └── agents/
│       ├── genius-ceo/            # CEO's CLAUDE.md, .env, launch-ac.sh
│       ├── genius-builder/        # Builder's CLAUDE.md, .env, launch-ac.sh
│       ├── genius-researcher/     # Researcher's CLAUDE.md, .env, launch-ac.sh
│       └── genius-jackie/         # Jackie's CLAUDE.md, .env, launch.sh
├── .claude/                       # Jackie's config (original, shared auth source)
├── .claude-ceo/                   # CEO's isolated config
│   ├── .credentials.json          # Copied from .claude/ (shared auth)
│   ├── plugins/                   # Copied from .claude/ (custom Discord fork)
│   └── channels/discord/          # CEO's bot token + access.json
├── .claude-builder/               # Builder's isolated config
│   └── channels/discord/          # Builder's bot token + access.json
└── .claude-researcher/            # Researcher's isolated config
    └── channels/discord/          # Researcher's bot token + access.json
```

**Key discovery:** `CLAUDE_CONFIG_DIR` env var lets each agent use a different `.claude/` directory. Auth credentials are shared (copied from Jackie's original `.claude/`), but Discord bot tokens are per-agent. No `claude-login` needed for new agents — just copy `.credentials.json`.

## Migration Order & Status

### Phase 1: CEO ✅ (set up, ready to launch)

VM `genius-ceo` is fully configured:
- [x] `computer create genius-ceo --ssh-enabled`
- [x] Per-agent config: `/home/node/.claude-ceo/` with credentials, settings, plugins
- [x] Discord bot token + access.json configured
- [x] Plugin cache copied with custom server.ts (our fork features)
- [x] CEO's .env (DISCORD_BOT_TOKEN + GH_TOKEN) on VM
- [x] CEO's scratchpad copied
- [x] `launch-ac.sh` created
- [ ] **Launch and test** — Lily runs from web terminal: `bash /home/node/SofaGenius/agents/genius-ceo/launch-ac.sh`

**Access:**
- Web terminal: https://8788--genius-ceo.computer.agentcomputer.ai
- SSH: `ssh -p 443 genius-ceo@ssh.agentcomputer.ai`

### Phase 2: Researcher (next)

- [ ] `computer create genius-researcher --ssh-enabled`
- [ ] Create `/home/node/.claude-researcher/` (copy credentials + settings + plugins)
- [ ] Configure Discord bot token + access.json
- [ ] Copy researcher's .env and scratchpad/research files
- [ ] Test launch

### Phase 3: Builder (last)

- [ ] `computer create genius-builder --ssh-enabled`
- [ ] Create `/home/node/.claude-builder/` (copy credentials + settings + plugins)
- [ ] Configure Discord bot token + access.json
- [ ] Copy builder's .env and scratchpad files
- [ ] Verify git push/PR workflows work from VM
- [ ] Test launch

## Per-Agent Setup (runbook)

```bash
# 1. Create VM (inherits shared filesystem)
computer create AGENT_NAME --ssh-enabled

# 2. Create per-agent config dir
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'mkdir -p /home/node/.claude-SHORTNAME/channels/discord'
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cp /home/node/.claude/.credentials.json /home/node/.claude-SHORTNAME/'
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cp /home/node/.claude/settings.json /home/node/.claude-SHORTNAME/'
ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai 'cp -r /home/node/.claude/plugins /home/node/.claude-SHORTNAME/'

# 3. Configure Discord (pipe local → VM, no SCP support)
echo "DISCORD_BOT_TOKEN=..." | ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai \
  'cat > /home/node/.claude-SHORTNAME/channels/discord/.env'
cat access.json | ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai \
  'cat > /home/node/.claude-SHORTNAME/channels/discord/access.json'

# 4. Copy agent's .env
cat agents/genius-SHORTNAME/.env | ssh -p 443 AGENT_NAME@ssh.agentcomputer.ai \
  'cat > /home/node/SofaGenius/agents/genius-SHORTNAME/.env'

# 5. Launch from web terminal: https://8788--AGENT_NAME.computer.agentcomputer.ai
bash /home/node/SofaGenius/agents/genius-SHORTNAME/launch-ac.sh
```

## Launch Script (launch-ac.sh)

Each agent has a `launch-ac.sh` in their agent directory. Uses `nohup` + `script -qc` pattern validated in PR #50 — survives terminal close and SSH disconnect:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export CLAUDE_CONFIG_DIR="/home/node/.claude-SHORTNAME"
cd "$SCRIPT_DIR" && set -a && source .env && set +a && \
  nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
echo "Agent launched (PID: $!). Logs: $SCRIPT_DIR/discord.log"
```

**Why `nohup` + `script -qc`:** Claude Code needs a PTY — `nohup` alone triggers `--print` mode. `script -qc` provides a pseudo-TTY. Validated by Agent Computer team (Hari) and tested for 16+ hours.

Differences from local `launch.sh`: sets `CLAUDE_CONFIG_DIR`, uses `nohup` + `script` (not `caffeinate`), backgrounds the process.

## Lily's Role (minimal)

- **One-time:** Nothing! Auth credentials shared via filesystem. No `claude-login` per agent.
- **If auth expires:** Run `computer claude-login --machine jackie` — credentials propagate to all agents via shared `.claude/`.
- **Testing:** Launch agents from web terminal to verify Discord connectivity.

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Process dies when terminal closes | Solved: `nohup` + `script -qc` pattern (PR #50). Survives terminal close and SSH disconnect. |
| Plugin auto-update overwrites custom server.ts | Backup at `/home/node/.claude/plugins/cache/` persists. Re-copy after plugin updates. |
| Auth expiry | Re-auth on any VM propagates to all via shared `.claude/.credentials.json`. |
| Git conflicts from concurrent writes | Same as local. Agents pull before pushing, handle merge conflicts. |

## Post-Migration Cleanup

Once all agents are on Agent Computer:
1. Remove local VS Code agent launch configs
2. Update CLAUDE.md files to reference AC paths if needed
3. Consider migrating Jackie to `/home/node/.claude-jackie/` for consistency
4. Document auto-restart solution once Agent Computer responds about `--channels` support
