# Spec: Merge Local Agent Org + AutoResearch into SofaGenius

**From:** CEO
**For:** Builder
**Priority:** High — do this before any other feature work
**Date:** 2026-03-22
**Status:** PENDING REVIEW

## Context

We have agent configs in two places (local `claude/` in vault + `agents/` in this repo), and autoresearch as a separate repo. Decision: **SofaGenius is the single source of truth monorepo.** Everything merges there.

## Final Structure

All paths are relative to the repo root.

```
.
├── agents/
│   ├── ceo/CLAUDE.md          ← from local (more complete)
│   ├── builder/CLAUDE.md      ← from local
│   ├── researcher/CLAUDE.md   ← from local
│   ├── handoff/               ← status files, specs (from local)
│   ├── onboarding.md
│   └── scripts/
│       ├── launch-ceo.sh
│       ├── launch-builder.sh
│       ├── launch-researcher.sh
│       └── launch.sh
├── autoresearch/              ← moved in as folder, keeps own pyproject.toml/venv
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── scripts/
│   ├── configs/
│   ├── reward/
│   ├── harbor_pipeline/
│   ├── tasks/
│   ├── jobs/
│   └── ...
├── backend/
├── frontend/
└── ...
```

**Jackie** stays in his own repo (`lilyzhng/jackie`) — different platform (OpenClaw). His handoff status file lives in `agents/handoff/` so the org can read it.

## Launch Directory

**Each agent launches from `agents/{name}/`.** Claude Code reads CLAUDE.md from the working directory, so each agent's CLAUDE.md lives in their launch directory.

Launch scripts handle this:
```bash
# Example: launch-ceo.sh
cd "$(dirname "$0")/../ceo" && claude
```

For cross-directory access (e.g., Researcher accessing `autoresearch/`), use absolute paths or paths relative to the repo root. The launch script can set a `REPO_ROOT` env var for convenience.

## Migration Steps

### PR 1: Agent Configs + Handoff (config only, low risk)

1. **CLAUDE.md files — use LOCAL versions** (they're more complete with Discord IDs, content strategy, handoff protocols)
   - `claude/ceo/CLAUDE.md` → overwrites `agents/ceo/CLAUDE.md`
   - `claude/builder/CLAUDE.md` → overwrites `agents/builder/CLAUDE.md`
   - `claude/researcher/CLAUDE.md` → overwrites `agents/researcher/CLAUDE.md`
   - **Update paths** in CLAUDE.md files: replace vault-relative paths with repo-relative paths

2. **Handoff directory**
   - Move all files from `claude/handoff/` → `agents/handoff/`
   - Replace stale handoff files with local ones
   - Include: status files, specs, `onboarding.md`
   - Delete the old top-level `handoff/` directory

3. **Launch scripts**
   - Move `claude/launch-*.sh` and `claude/launch.sh` → `agents/scripts/`
   - Update paths inside scripts to `cd` into `agents/{name}/` before launching
   - Set `REPO_ROOT` env var for cross-directory access

### PR 2: AutoResearch

1. **Move autoresearch into repo as top-level folder**
   - Copy contents of `lilyzhng/autoresearch` → `autoresearch/`
   - Keep `pyproject.toml`, `uv.lock` — Researcher runs `cd autoresearch && uv sync` for their own venv
   - Add `.gitignore` for autoresearch: `*.pt`, `*.safetensors`, `*.ckpt`, `__pycache__/`, `.venv/`, `data/raw/`, `wandb/`, `outputs/`

2. **Update Researcher's CLAUDE.md** to reference `autoresearch/` as their workspace (accessed via absolute paths from `agents/researcher/`)

### Cleanup (after ALL agents verified)

**Safety gate:** Do NOT delete `claude/` until all agents have completed at least one full session from SofaGenius and verified:
- Session start routine works (read handoff files, check channels)
- Can read/write to handoff directory
- Launch scripts work correctly
- Cross-directory access works (e.g., Researcher can access `autoresearch/`)

Only after verification:
- Archive `claude/` from the vault repo
- Update global CLAUDE.md if it references old `claude/` paths
- Update memory files that reference old paths

## Key Decisions (direction confirmed by Lily, details under review)

- Monorepo wins over submodules for autoresearch — one PR flow, simpler
- `handoff/` lives inside `agents/` — it's only for agents
- Separate venvs per directory (autoresearch has own `pyproject.toml`)
- `.gitignore` heavy files, use HF Hub for large artifacts
- Jackie stays in own repo (different platform)
- Each agent launches from `agents/{name}/` — CLAUDE.md is in the working directory

## Completion Criteria

- [ ] All CLAUDE.md files in SofaGenius are the complete local versions
- [ ] Handoff directory fully migrated to `agents/handoff/`
- [ ] Launch scripts work from `agents/scripts/`, launching into `agents/{name}/`
- [ ] AutoResearch merged as top-level folder with own venv and `.gitignore`
- [ ] All agents verified working from SofaGenius (at least one full session each)
- [ ] Local `claude/` folder archived from vault (only after verification)
- [ ] No broken path references
