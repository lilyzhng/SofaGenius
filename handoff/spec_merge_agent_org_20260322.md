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
│   └── launch-*.sh            ← launch scripts
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
   - Move `claude/launch-*.sh` and `claude/launch.sh` → `agents/`
   - Update paths inside scripts to point to repo structure

### PR 2: AutoResearch

1. **Move autoresearch into repo as top-level folder**
   - Copy contents of `lilyzhng/autoresearch` → `autoresearch/`
   - Keep `pyproject.toml`, `uv.lock` — Researcher runs `cd autoresearch && uv sync` for their own venv
   - `.gitignore` model artifacts, large data files (use HF Hub / DVC for those)

2. **Update Researcher's CLAUDE.md** to reference `autoresearch/` as their workspace

### PR 3: Builder Work Files

1. **Builder's code** — decide per item:
   - `LaunchAngel/` → stays if it's a SofaGenius feature, or becomes its own repo if it's a separate product
   - `scripts/` → `scripts/` or `agents/builder/scripts/`
   - `data/`, `jobs/`, `tasks/`, `tasks-eval/` → appropriate locations
   - `dashboard.html` → check if still needed

### Cleanup (after all PRs merged)

- Delete `claude/` from the vault repo
- Update global CLAUDE.md if it references old `claude/` paths
- Update memory files that reference old paths
- Each agent verifies they can start sessions from SofaGenius

## Key Decisions (direction confirmed by Lily, details under review)

- Monorepo wins over submodules for autoresearch — one PR flow, simpler
- `handoff/` lives inside `agents/` — it's only for agents
- Separate venvs per directory (autoresearch has own `pyproject.toml`)
- `.gitignore` heavy files, use HF Hub for large artifacts
- Jackie stays in own repo (different platform)
- Symlink CLAUDE.md for agents that work outside SofaGenius (e.g. if Researcher needs to `cd autoresearch`)

## Completion Criteria

- [ ] All CLAUDE.md files in SofaGenius are the complete local versions
- [ ] Handoff directory fully migrated to `agents/handoff/`
- [ ] Launch scripts work from SofaGenius
- [ ] AutoResearch merged as top-level folder with own venv
- [ ] Local `claude/` folder deleted from vault
- [ ] All agents can start sessions from SofaGenius repo
- [ ] No broken path references
