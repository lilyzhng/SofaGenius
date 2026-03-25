# Agent Computer Migration Plan

**Author:** Genius Builder
**Date:** 2026-03-24
**Status:** Proposed

## Problem

Running 3+ agents in VS Code on Lily's laptop is unstable — VS Code crashed from resource exhaustion on March 24. Agents go down when VS Code crashes or the laptop closes. Jackie already proved Agent Computer works for always-on operation.

## Decision: Separate VMs

Each agent gets its own VM on Agent Computer.

**Why not a single VM?** The whole reason we're migrating is that 3 agents in one process crashed. Putting 3 agents in one VM is the same problem on a different computer. Separate VMs give us:
- Fault isolation — one crash doesn't take down the team
- Independent restarts
- Clean resource boundaries
- Easier debugging

**Cost:** $20/mo for 25 VMs. Jackie uses 1. Adding 3 more = 4 total. 21 remaining.

## Migration Order

### Phase 1: CEO (first)
- Lightest workload (coordination, Discord, content) — lowest risk
- Builder sets up the VM while still running locally
- Good smoke test for the full migration process

### Phase 2: Researcher (second)
- Similar setup to CEO, slightly heavier (web searches, long research)
- By this point we'll have ironed out any issues from CEO's migration

### Phase 3: Builder (last)
- Heaviest workload (coding, tests, git ops) — wants process battle-tested first
- Once CEO + Researcher are stable, Builder sets up own VM
- Lily does final `claude-login`

## Per-Agent Setup Checklist

Each agent migration follows the same steps (~20 min each):

### 1. Create VM
```bash
computer create <agent-name>
```
Inherits shared filesystem from account settings.

### 2. Claude Login (requires Lily's browser)
```bash
computer claude-login --machine <agent-name>
```
This is the only step that requires Lily. Everything else Builder handles.

### 3. Clone Repo
```bash
# SSH into the VM
computer ssh <agent-name>

# Clone SofaGenius
cd /home/node
git clone https://github.com/lilyzhng/SofaGenius.git
```

### 4. Configure Environment
Each agent needs its own `.env` in its agent directory (`agents/genius-<name>/.env`):
- `ANTHROPIC_API_KEY` — from Claude login (may be auto-configured)
- `GH_TOKEN` — agent's GitHub PAT
- `DISCORD_BOT_TOKEN` — agent's Discord bot token
- Agent-specific tokens (e.g., Jackie's `JACKIE_BOT_TOKEN`)

Copy from local machine:
```bash
scp -P 443 agents/genius-<name>/.env <agent-name>@ssh.agentcomputer.ai:/home/node/SofaGenius/agents/genius-<name>/.env
```

### 5. Install Discord Plugin
```bash
# On the VM
claude mcp add plugin:discord -- npx @anthropic-ai/claude-code-discord-plugin
```

Copy custom `server.ts` if we have a fork (Jackie's known issue — plugin cache overwrites on restart).

### 6. Copy Memory & Settings
```bash
# Copy agent's Claude memory/settings
scp -P 443 -r ~/.claude/ <agent-name>@ssh.agentcomputer.ai:~/.claude/
```

### 7. Create Launch Script
Each agent already has a `launch.sh`. Verify it works on the VM:
```bash
cd /home/node/SofaGenius/agents/genius-<name>
bash launch.sh
```

### 8. Validate
- [ ] Agent responds to @mentions in Discord
- [ ] Agent can read/write to shared filesystem
- [ ] Agent can push to GitHub (git credentials work)
- [ ] Agent can read other agents' scratchpads and handoff files
- [ ] Cron jobs work (if applicable — Jackie's digest trigger)

## Shared Filesystem

Agent Computer's shared storage mode is enabled on our account. All VMs mount the same `/home/node` directory. This means:

- **Shared:** Repo, scratchpads, handoff directory, brainstorm docs
- **Isolated per VM:** Claude Code process, `.env` files, Discord plugin config

Agents can read each other's files the same way they do locally through the vault.

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| No auto-restart / supervisor | Create a wrapper script with crash recovery (restart on exit). Builder to implement. |
| Plugin cache overwrites on restart | Pre-launch step copies custom `server.ts` before starting Claude Code |
| `claude-login` expires | Monitor for auth failures. Lily re-runs login when needed. |
| Git conflicts from concurrent writes | Same risk as today. Agents pull before pushing, handle merge conflicts. |
| Shared filesystem race conditions | Agents write to their own directories. Handoff protocol already handles coordination. |

## Post-Migration Cleanup

Once all agents are on Agent Computer:
1. Remove local VS Code agent launch configs
2. Update CLAUDE.md files to reference AC paths (`/home/node/SofaGenius/` instead of `/Users/lilyzhang/Documents/lilyzhng/SofaGenius/`)
3. Document the auto-restart solution once proven
4. Update Jackie's CLAUDE.md to remove Fly.io references (already migrated)

## Timeline

- **Phase 1 (CEO):** Builder sets up tonight, Lily does claude-login when available
- **Phase 2 (Researcher):** Next day after CEO is validated
- **Phase 3 (Builder):** After CEO + Researcher stable for 24h
- **Total:** ~2-3 days to full migration
