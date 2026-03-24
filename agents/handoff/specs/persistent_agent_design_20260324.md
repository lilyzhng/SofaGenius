# Persistent Agent on Agent Computer — One-Pager

**Author:** genius-builder  |  **Date:** 2026-03-24  |  **Status:** Draft  |  **Owner:** genius-builder

## Problem

Claude Code agents on Agent Computer lose all state (repos, config, plugins, memories) when the VM resets or `computer claude-login` runs. The default filesystem mode is **isolated** — ephemeral overlay that gets wiped. We need agents that persist across restarts, re-auths, and crashes, with zero manual re-setup.

## Solution

### 1. Shared Filesystem (account-level fix)

Agent Computer has two filesystem modes:
- **Isolated** (default) — ephemeral overlay. Wiped on reset.
- **Shared** — persistent EFS home at `/home/node`. Survives across sessions, re-auths, VM recreation.

**Setup:** Account Profile → Enable "Shared filesystem." Then **recreate** the VM — existing VMs keep their original mode.

```bash
computer delete agent-name
computer create agent-name --ssh-enabled
computer claude-login --machine agent-name  # one-time auth
```

With shared mode, everything in `/home/node/` persists: repos, `.claude/` config, plugins, memories. No bootstrap needed.

**Important:** "Shared storage only affects **future** machines. Existing machines keep their original mode." — Agent Computer docs. Must recreate to pick up shared mode.

**Root cause of state loss (March 24):** Jackie was created with isolated mode (the account default). `computer claude-login` wiped the entire `/home/node/` overlay including SofaGenius repo, Discord plugin, config, and memories. Switching to shared mode + recreating the VM fixed this permanently.

**Warning:** On isolated VMs, `computer claude-login` wipes `~/.claude/` and the entire ephemeral overlay. Never use isolated mode for agents that need persistent state.

### 2. Persistent Storage Fallback (for isolated VMs)

On isolated VMs, `/home/node/.local/` is an NFS mount that persists. Store all state there:

```
/home/node/.local/jackie/
├── SofaGenius/          # git repo
├── claude-config/       # Discord .env, access.json
└── bootstrap.sh         # Restores config into ~/.claude/ on reset
```

After any reset: `bash /home/node/.local/jackie/bootstrap.sh` — restores everything in 2 seconds.

### 3. Always-On Agent Sessions

**Primary approach: Agent Computer's built-in session management.**

Agent Computer has a session system via `computer agent sessions` powered by Rivet's sandbox-agent, which handles "process lifecycle, environment setup, and communication between the machine and the Agent Computer control plane."

```bash
computer agent sessions new jackie --agent claude --name jackie-discord
computer agent prompt jackie "start listening on Discord" --name jackie-discord
computer agent watch jackie --session <id>
computer agent status jackie
```

**Status (March 24):**
- ❌ Internal errors on isolated VM
- ✅ Works on shared VM — sessions create and respond to prompts
- ❌ Does NOT support `--channels` flag — Discord MCP tools don't load in agent sessions
- ✅ **Agent Computer team (Hari) recommended `nohup` approach** — works with `script -qc` wrapper

### Always-On Solution: `nohup` + `script` (VALIDATED)

Agent Computer's Hari recommended `nohup` for background processes. Claude Code needs a PTY, so we wrap with `script -qc`:

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd /home/node/SofaGenius/agents/genius-jackie
set -a && source .env && set +a
nohup script -qc "claude --channels plugin:discord@claude-plugins-official --dangerously-skip-permissions" /dev/null > discord.log 2>&1 &
```

**Validated (March 24):**
- ✅ Claude Code starts with Discord plugin connected
- ✅ Process survives SSH disconnect
- ✅ Process survives closing all browser tabs / web terminal
- ✅ Jackie responds to Discord messages while running in background
- ⏳ 16-hour persistence test in progress (started 4:15 PM PT March 24)

**Why `script -qc`:** Claude Code detects non-interactive stdin and falls back to `--print` mode with `nohup` alone. `script` provides a pseudo-TTY that Claude Code accepts. The `-q` flag suppresses `script`'s own output. `-c` passes the command.

**Logs:** stdout/stderr go to `discord.log` in Jackie's directory.

**Health check (future):** Hourly cron to verify process is alive. Needs cron installed — no sudo on Agent Computer, asking Hari about this.

**Startup lag:** Discord plugin takes 30-60 seconds to connect to Discord's gateway after launch. Not a bug — it's the WebSocket connection + guild cache warmup.

### 4. Discord Plugin Persistence

Our custom Discord plugin fork: https://github.com/lilyzhng/claude-plugins-official
(4 commits ahead of Anthropic upstream: create_thread, polls, trustedBots, wildcard groups, resolveMentions)

**With shared filesystem:**
- Plugin install at `~/.claude/plugins/` persists across restarts
- Plugin cache at `~/.claude/plugins/cache/` persists (no re-download)
- Discord config at `~/.claude/channels/discord/` persists (token + access.json)
- Custom `server.ts` persists (our fork features survive)

**Plugin auto-update risk:** Claude Code may auto-update the plugin on restart, overwriting our custom `server.ts`. Mitigation: keep a backup at `agents/genius-{name}/server.ts.custom` and re-copy if the plugin version changes. Long-term fix: get our fork features merged upstream.

## Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Filesystem mode | Shared (account default) | Persistent `/home/node`. One-time setup, survives everything. |
| Always-on | Agent Computer's `computer agent sessions` (primary) | Use the platform's built-in session management. No hacks. |
| Fallback | tmux supervisor (only if sessions fail) | Only after filing support ticket + confirming platform can't do it. |
| Plugin | Shared filesystem persists `~/.claude/plugins/` | No re-copying needed with shared mode. |

## Scaling to Multiple Agents

Same pattern for any agent:

```bash
computer create agent-name --ssh-enabled  # inherits shared mode
computer claude-login --machine agent-name
# Clone repo, configure, start supervisor — one-time
```

Each agent = one VM. $20/mo for 25 VMs. Persistent home means clone/install/configure once → persists forever.

**One-time setup checklist (per agent):**

1. `computer create agent-name --ssh-enabled` (shared mode inherits from account)
2. `computer claude-login --machine agent-name` (Lily does this — browser OAuth)
3. Clone repo: `git clone https://github.com/lilyzhng/SofaGenius.git`
4. Set up `.env` with agent's Discord bot token + GitHub PAT
5. Set up Discord config: `~/.claude/channels/discord/.env` + `access.json`
6. **Install Discord plugin from inside a Claude session:**
   ```
   cd /home/node/SofaGenius/agents/genius-{name}
   claude
   # Inside Claude session:
   /plugin install discord@claude-plugins-official
   /exit
   ```
7. Copy our custom plugin fork's `server.ts` over the installed version (for create_thread, polls, etc.)
8. Start with launch script: `bash launch.sh`

Steps 1-7 are **one-time only** — everything persists on shared EFS. Step 8 is needed after each VM restart until we get Agent Computer's session management working.

**Current:** 1/25 VMs (Jackie). Can add CEO, Researcher, or specialized agents.

**Shared filesystem note:** All agents share `/home/node/`. Use per-agent subdirectories (`/home/node/workspace-jackie/`, `/home/node/workspace-researcher/`) for isolation.

## Risks

- **Shared first boot ~20s** — acceptable for persistence.
- **tmux OOM** — cron health check catches within 5 min.
- **Plugin overwrite** — supervisor restores on restart.
- **Shared = shared** — agents see each other's files. Per-agent dirs for isolation.

## Plan

| Phase | What | Owner | Time |
|-------|------|-------|------|
| 1 | Recreate Jackie with shared filesystem | Builder + Lily (auth) | 10 min |
| 2 | One-time setup: clone repo, config, plugin | Builder | 15 min |
| 3 | Test `computer agent sessions` on new VM | Builder | 15 min |
| 4 | If sessions work → configure always-on. If not → file support ticket. | Builder | 15 min |
| 5 | Test: persistence across re-auth, tab close, prompt resume | Builder + Lily | 15 min |

## Open Questions

1. **`computer agent sessions`** — Agent Computer's built-in session system returned internal errors. May be better than tmux. Worth a support ticket.
2. **Multi-agent isolation** — if agents share `/home/node/`, do their `.claude/` configs conflict? Need per-agent `CLAUDE_HOME` or separate working dirs.
3. **Plugin upstream merge** — once Anthropic merges our fork features, the overwrite problem disappears.
