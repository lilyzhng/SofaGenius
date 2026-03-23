# Scratchpad: Harbor Port Progress (2026-03-22 overnight)

## Timed Eval Results

| Model | Task | Time | Reward |
|-------|------|------|--------|
| Claude Sonnet 4 | apex-finance-1588 (LBO) | **1:16** | 0.1 |
| Qwen3-Coder-30B | apex-finance-1588 (LBO) | **0:55** | 0.0 |

**Note:** Rewards are lower than earlier runs (Sonnet got 1.0 before). This could be:
- Docker image was rebuilt (different task data state?)
- OpenRouter model routing variance
- Need to investigate — check verifier reward.json for details

**Throughput:** ~1 min per task per model. For 100 tasks × 1 model = ~100 min. Acceptable for initial runs, but Modal parallelization would help.

## Commits Made

1. **autoresearch** `6233a94` — brainstorm doc + repo knowledge.md files + handoff
2. **vault** `0504b53` — APEX Harbor training pipeline (all scripts)
3. **harbor submodule** `bc52307` — per-criterion comparison view

## Issues Found

### Reward Variance
- Same task (apex-finance-1588) gave very different rewards across runs:
  - Run 1: 0.43 (old reward scorer)
  - Run 2: 0.5 (simplified scorer)
  - Run 3: 1.0 (same scorer, different run)
  - Run 4: 1.0 (same scorer)
  - Run 5: 0.3 (Qwen)
  - Run 6 (timed): 0.1 (Sonnet?!)
  - Run 7 (timed): 0.0 (Qwen)
- **Root cause: LLM non-determinism at temperature=1.0.** Same model, same task, very different approaches each run. The analysis shows the agent's calculations are just wrong (expected MOIC 2.84x, got 10.0). Not a scorer bug — the agent genuinely produced bad numbers this time.
- This variance is exactly why RL training is needed — make the agent more consistently correct.

### Code Location (Lily feedback)
- Lily wants RL-related code in `autoresearch/`, not `claude/builder/`
- Builder should stay generic (building tools, not specific RL experiments)
- TODO: Move scripts/ and tasks/ to autoresearch repo

## TODO (from handoff plan)

- [x] Investigate reward variance → LLM non-determinism at temp=1.0, not a bug
- [x] Move RL scripts from builder to autoresearch → `autoresearch/harbor_pipeline/scripts/`
- [x] Commit all code (3 commits: autoresearch, vault, harbor submodule)
- [x] Run parallel eval — 5 tasks × Sonnet in 2:46 (33s/task parallel vs 76s serial). Mean reward 0.617.
- [x] Implement curiosity bonus in SkyRL — modified harbor_generator.py, reads tool_engaged from reward.json, applies batch-level bonus
- [ ] Launch first training run (needs GPU — 4x A100 or Modal)
- [x] Re-push updated reward_scorer to HF (`lilyzhng/apex-harbor-train`)
- [x] Fix Harbor dashboard font (text-base instead of text-xl)

## Additional Commits (2026-03-22 afternoon)

5. **skyrl submodule** `a4ea663` — VerlTool curiosity bonus in harbor_generator.py
6. **harbor submodule** `4c9576b` — font fix in compare.tsx
7. **harbor submodule** `bc52307` — per-criterion breakdown in compare view
8. **autoresearch** `389536e` — Harbor env: modal → daytona
9. **autoresearch** `c4011ef` — GPU watchdog script

## Modal Training Attempts

| Attempt | Error | Root Cause |
|---------|-------|------------|
| v1 | `bash: harbor_pipeline/scripts/...: No such file` | Script not in SkyRL mount |
| v2 | `Failed to download nvidia-cuda-cupti-cu12` | Network timeout (transient) |
| v3 | `Invalid fields {'max_steps'}` | SkyRL doesn't have max_steps param |
| v4 (30B, Daytona) | `Engine core initialization failed` / `No CUDA runtime` | vLLM can't init — either GPU memory or Ray GPU scheduling |
| v5 (1.5B, Daytona) | `Failed to download vllm==0.16.0` | Network timeout (transient) |
| v6 (1.5B, retry) | `Failed to download vllm` | Network timeout again |
| v7 (1.5B, pre-built image) | Modal `InvalidError` | `add_local_dir` before `run_commands` — needs `copy=True` |
| v8 (1.5B, copy=True) | `RemoteError` | Container died — likely OOM from 4x vLLM engines × 32k context |
| v9 (1.5B, 16k, 0.5 GPU, detach) | `Failed to download nvidia-cuda-cupti` | Network timeout — `--isolated` re-downloads despite pre-install |
| v10 (1.5B, uv cache warmup) | **RUNNING** | Modal: <https://modal.com/apps/lilyzhng/main/ap-NUant1faNkfzJgmhYNgvFR> W&B: `apex-small-v7` |

## How to Check V9 Result

1. **W&B**: <https://wandb.ai/alchemxz/apex-professional> — look for `apex-small-v6`
2. **Modal**: <https://modal.com/apps/lilyzhng/main/ap-WoxclDMSolVHRxDbIWJVUr>
3. If V9 succeeds → pipeline validated, ready for Qwen3-Coder-30B
4. If V9 fails → check Modal logs for error type

## V9 Config (what changed from V2 that worked)
- Model: Qwen2.5-1.5B-Instruct (small, fits easily)
- max_model_len: 16384 (reduced from 32768)
- gpu_memory_utilization: 0.5 (reduced from 0.8)
- max_turns: 6 (reduced from 10)
- enable_summarize: true (new)
- environment: daytona (not modal — training on Modal GPU, trials on Daytona CPU)
- --detach (new — survives log off)

**Key learning:** SkyRL on Modal uses Ray workers that download ALL dependencies from scratch each run (~2GB). Need custom image or dependency caching to avoid transient network failures.
