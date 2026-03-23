# Build Handoff: Harbor Port + APEX RL Environment

**Date:** 2026-03-22
**From:** CC Builder
**Status:** Pipeline built, smoke-tested, ready for training

---

## Done Today

### Research & Design (brainstorm — 14 rounds of discussion)
- Clarified RL training vs eval: split tasks not data, environment is shared
- Decided: OpenEnv → Harbor (bash-native, Docker isolation, SkyRL integration)
- Decided: skip SFT, go straight to RL
- Analyzed APEX data shape: not tool-calling dataset, but naturally encodes multi-step workflows
- Studied 3 repos: Agent-R1 (dead code process rewards), ToolRL (single-turn, misleading name), VerlTool ⭐ (curiosity bonus, tool server = Harbor architecture)
- Reward design: simplified to **correctness + tool engagement + curiosity bonus** (dropped old process signals)
- Strategy: within-domain complexity scaling > cross-domain generalization
- IB/Finance domain selected for deep focus (heavy tool usage)

### Data Pipeline
- ✅ Downloaded APEX-v1-extended (100 tasks, 132 PDFs, CC-BY-4.0 trainable)
- ✅ Downloaded apex-agents (480 tasks, 33 world zips / 8.9GB, eval-only)
- ✅ Converted 100 training tasks to Harbor format
- ✅ Converted 480 eval tasks to Harbor format (446/480 with file attachments)
- ✅ Pushed to HF: `lilyzhng/apex-harbor-train`, `lilyzhng/apex-harbor-eval`

### Training Infrastructure
- ✅ `scripts/run_apex_train.sh` — SkyRL + Harbor, Qwen3-Coder-30B
- ✅ `scripts/harbor_trial_config.yaml` — 16 turns, 600s timeout, 2GB RAM
- ✅ Reward scorer: correctness (criteria_met / total) + tool_engaged flag
- ✅ Per-criterion analysis: shows expected vs actual numbers for failed criteria

### Smoke Tests
- ✅ Harbor CLI pipeline end-to-end: Docker build → agent execution → test.sh → reward
- ✅ Claude Sonnet on LBO task: **1.0** (10/10 criteria)
- ✅ Qwen3-Coder-30B on same task: **0.3** (3/10 criteria) — clear training opportunity
- ✅ Per-criterion breakdown visible in Harbor dashboard (modified viewer source)

### Harbor Dashboard Improvements
- ✅ Modified Harbor viewer: side-by-side criteria comparison below heatmap
- ✅ ✓ green / ✗ red coloring for pass/fail
- ✅ Analysis text for failed criteria (expected vs agent values)
- ✅ Files created by agent shown

---

## Code Location

All in `claude/builder/`:

| File | Purpose |
|------|---------|
| `scripts/download_apex_files.py` | Download both APEX datasets |
| `scripts/convert_apex_to_harbor.py` | Convert 100 training tasks |
| `scripts/convert_apex_eval.py` | Convert 480 eval tasks |
| `scripts/harbor_template/` | Dockerfile + test.sh + reward_scorer.py |
| `scripts/harbor_trial_config.yaml` | Harbor config for APEX |
| `scripts/run_apex_train.sh` | SkyRL training launch script |
| `scripts/verify_harbor_tasks.py` | Structure verification |
| `scripts/generate_dashboard.py` | Custom comparison dashboard (backup) |

Research docs:
- `autoresearch/brainstorm/20260322_harbor_port_reward_design.md` — full discussion record (14 conversations)
- `autoresearch/submodules/Agent-R1/knowledge.md` — repo analysis
- `autoresearch/submodules/ToolRL/knowledge.md` — repo analysis
- `autoresearch/submodules/verl-tool/knowledge.md` — repo analysis

---

## Tomorrow Morning Priorities

### 1. Run Parallel Eval on Multiple Tasks
- Use Harbor's built-in parallelization or Modal for speed
- Run Sonnet + Qwen on 5-10 tasks across domains, not just one
- This gives us a real baseline before training

### 2. Implement Curiosity Bonus in SkyRL
- VerlTool formula: `bonus = 0.5 × I(used_tool) × max(0, 0.3 - group_rate)`
- Needs to be added at SkyRL training loop level, not in test.sh
- Reference: `autoresearch/submodules/verl-tool/knowledge.md`

### 3. Launch First Training Run
- Sanity check: `bash scripts/run_apex_train.sh --max-steps 1 --train-size 5`
- If passes, scale up: full 100 tasks, 3 epochs
- Monitor on W&B (project: apex-professional)

### 4. Fix Remaining Dashboard Issues
- Font consistency on score display
- Re-push updated reward_scorer.py to HF repos
- Consider Modal-based parallel eval for faster iteration

---

## Key Decisions to Remember

- **Reward = correctness + tool_engaged + curiosity bonus.** No old process signals.
- **APEX data is NOT tool-calling.** Agent uses bash + python natively. No hardcoded tools.
- **Within-domain complexity scaling** > cross-domain generalization for industry value.
- **VerlTool is main reference** for training infra. Agent-R1 and ToolRL are FYI only.
- **Re-read brainstorm doc before coding.** Brainstorm doc is source of truth, not old code.
