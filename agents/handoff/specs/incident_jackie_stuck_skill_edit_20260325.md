---
type: incident-report
date: 2026-03-25
agent: jackie
severity: medium (agent down ~10 hours)
resolved: true
---

# Incident: Jackie Stuck Editing Skill File

## What Happened

Jackie (running on Agent Computer VM `jackie-chan`) became unresponsive on 2026-03-25. He had been trying to modify the `builder-digest` skill, which was located in his own agent-local directory (`agents/genius-jackie/skills/builder-digest/`).

The VM builder agent noticed Jackie was stuck, attempted to kill the process and relaunch him, but the relaunch didn't fully work — Jackie came back without a functioning Discord plugin connection.

## Root Cause (Two Issues)

### Issue 1: Skill in wrong location

The `builder-digest` skill was defined under `agents/genius-jackie/skills/` instead of the shared `agents/skills/` folder. When Jackie (running in a **git worktree** at `/home/node/worktrees/genius-jackie/`) tried to edit the skill, he was editing files inside the worktree — which is a shallow copy of the repo that doesn't contain `.env` files or other local-only state. The Edit tool may have encountered permission or path resolution issues in the worktree, causing the Claude session to hang.

### Issue 2: Plugin path mismatch after restart

When the VM builder killed Jackie and relaunched him, Claude Code v2.1.83 resolved the Discord plugin from a **new path**:

- **Other agents (launched earlier):** `~/.claude/plugins/cache/claude-plugins-official/discord/0.0.4/server.ts` (our custom version with `create_thread`, polls, `resolveMentions`)
- **Jackie (relaunched later):** `~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts` (stock version — missing custom features)

Claude Code now has two plugin resolution paths: the legacy `cache/` directory and the newer `marketplaces/` directory. New sessions resolve from `marketplaces/`, which gets auto-updated from the GitHub repo and **overwrites our custom server.ts**.

## Fix Applied

1. **Killed Jackie's zombie processes** (PID 42700/42701 — one in `D` state, one `<defunct>`)
2. **Copied custom `server.ts`** from `cache/` path to `marketplaces/` path so new sessions get our custom Discord features
3. **Relaunched Jackie** via `launch-bg.sh` — confirmed Discord plugin (bun) is running and connected
4. **Moved `builder-digest` skill** from `agents/genius-jackie/skills/` to `agents/skills/` (shared location)

## Mitigation: How Agents Should Edit Skills

### Rule: Skills live in `agents/skills/`, not in agent-local dirs

All shared skills MUST be in `agents/skills/`. Agent-local `skills/` folders should only contain agent-specific skills that no other agent uses.

### How to safely modify a shared skill

1. **Edit the skill in `agents/skills/<skill-name>/SKILL.md`** (the shared folder in the main repo)
2. **Commit and push** via a PR using `/raise-pr`
3. **On the VM**, the change propagates via `git pull` in each agent's worktree

### What NOT to do

- Do NOT edit skills in `~/.claude/plugins/` — that's managed by Claude Code and gets overwritten
- Do NOT create duplicate skills in agent-local `skills/` folders — this causes confusion about which version is canonical
- Do NOT edit files in the worktree that are expected to be synced from the main repo — the worktree is for git isolation, not independent editing

### Plugin custom server.ts maintenance

Our custom Discord `server.ts` (with `create_thread`, polls, `resolveMentions`, `trustedBots`) must be kept in sync across two paths on the VM:

```
~/.claude/plugins/cache/claude-plugins-official/discord/0.0.4/server.ts       # legacy path
~/.claude/plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts  # new path
```

**After any agent restart**, verify the Discord plugin is using our custom version. The `marketplaces/` version may get overwritten by auto-updates.

A future improvement would be a `post-launch` hook that automatically copies the custom server.ts to both paths.

## Process Diagram

```
Agent wants to edit a skill
  |
  v
Is it in agents/skills/? ──yes──> Edit there, commit, push
  |
  no
  |
  v
Move it to agents/skills/ first, then edit
  |
  (never edit in agents/genius-<name>/skills/ for shared skills)
```
