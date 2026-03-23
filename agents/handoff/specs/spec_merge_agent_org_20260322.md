# Spec: Merge Local Agent Org + AutoResearch into SofaGenius

**From:** CEO
**For:** Builder
**Priority:** High — do this before any other feature work
**Date:** 2026-03-22
**Status:** APPROVED by Lily

## Context

We have agent configs in two places (local `claude/` in vault + `SofaGenius/agents/`), and autoresearch as a separate repo. Decision: **SofaGenius is the single source of truth monorepo.** Everything merges there.

## Final Structure

```
SofaGenius/
├── agents/
│   ├── ceo/CLAUDE.md          ← from local (more complete)
│   ├── builder/CLAUDE.md      ← from local
│   ├── researcher/CLAUDE.md   ← from local
│   ├── onboarding.md          ← from handoff/
│   └── launch-*.sh            ← launch scripts
├── handoff/                   ← status files, specs (from local)
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

**Jackie** stays in his own repo (`lilyzhng/jackie`) — different platform (OpenClaw). His handoff status file lives in `SofaGenius/handoff/` so the org can read it.

## Migration Steps

### PR 1: Agent Configs + Handoff (config only, low risk) — ✅ MERGED (PR #20)

1. **CLAUDE.md files — use LOCAL versions** ✅
   - Agent folders renamed to `genius-*` convention
   - Handoff directory organized into `status/`, `specs/`, `reports/` subfolders
   - Paths updated to SofaGenius-relative

2. **Handoff directory** ✅
   - Migrated to `agents/handoff/` with subfolders

3. **Launch scripts** ✅
   - Moved to `agents/scripts/`

### PR 2: AutoResearch — 🚧 IN PROGRESS

1. **Move autoresearch into SofaGenius as top-level folder** ✅
   - Copied all git-tracked files (excl. submodules/) → `SofaGenius/autoresearch/`
   - Kept `pyproject.toml`, `uv.lock` — Researcher runs `cd autoresearch && uv sync`
   - Clean `.gitignore` for model artifacts, large data, submodules

2. **Update Researcher's CLAUDE.md** ✅ — added Workspace section with autoresearch paths and submodule instructions

3. **Update README.md** ✅ — project structure updated with autoresearch and correct `genius-*` folder names

### PR 3: Builder Work Files

1. **Builder's code** — decide per item:
   - `LaunchAngel/` → stays if it's a SofaGenius feature, or becomes its own repo if it's a separate product
   - `scripts/` → `SofaGenius/scripts/` or `agents/builder/scripts/`
   - `data/`, `jobs/`, `tasks/`, `tasks-eval/` → appropriate SofaGenius locations
   - `dashboard.html` → check if still needed

### Cleanup (after all PRs merged)

- Delete `claude/` from the vault repo
- Update global CLAUDE.md if it references old `claude/` paths
- Update memory files that reference old paths
- Each agent verifies they can start sessions from SofaGenius

## Key Decisions (confirmed by Lily)

- Monorepo wins over submodules for autoresearch — one PR flow, simpler
- Separate venvs per directory (autoresearch has own `pyproject.toml`)
- `.gitignore` heavy files, use HF Hub for large artifacts
- Jackie stays in own repo (different platform)
- Symlink CLAUDE.md for agents that work outside SofaGenius (e.g. if Researcher needs to `cd autoresearch`)

## Completion Criteria

- [x] All CLAUDE.md files in SofaGenius are the complete local versions (PR #20)
- [x] Handoff directory fully migrated (PR #20)
- [x] Launch scripts work from SofaGenius (PR #20)
- [x] AutoResearch merged as top-level folder with own venv (PR 2 — in progress)
- [x] Local `claude/` folder deleted from vault
- [ ] All agents can start sessions from SofaGenius repo
- [ ] No broken path references
