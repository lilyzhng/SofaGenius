# Plan: Phase 4 — Subagent Refactor + Modal Launch Agent

## Context

Phase 3 is complete (13 tools across 3 domains). Adding Modal launch tools pushes past the 15-tool threshold where a single agent struggles with tool selection. Per the architecture decision in STATE.md, this is the inflection point to refactor into subagents. The user wants fine-tuning (Unsloth) + evaluation on Modal, with the "aha moment" of going from scout/draft to actually launching training from the UI.

## Overview

Two interleaved efforts:
1. **Subagent refactor** — Split the monolithic agent into an orchestrator + 4 specialized agents
2. **Modal Launch Agent** — New agent with tools to propose fine-tuning/eval jobs, LaunchCard UI with approval flow, `/api/launch` endpoint

## File Structure

```
backend/
├── orchestrator.py              # NEW — intent classifier + router
├── agents/
│   ├── __init__.py              # NEW
│   ├── base.py                  # NEW — shared parameterized agent loop
│   ├── training.py              # NEW — W&B Monitor (4 tools)
│   ├── data.py                  # NEW — Data/SQL Analyst (6 tools)
│   ├── scout.py                 # NEW — Scout + Draft (4 tools)
│   └── launch.py                # NEW — Modal Launch (2 tools)
├── tools/
│   ├── wandb_monitor.py         # unchanged
│   ├── sql_analyst.py           # unchanged
│   ├── scout_draft.py           # unchanged
│   └── modal_launcher.py        # NEW — propose_finetune, propose_eval
├── modal_app/
│   ├── app.py                   # NEW — Modal App + image/volume defs
│   ├── finetune.py              # NEW — adapted from user's modal_coder_base.py
│   └── eval.py                  # NEW — adapted from user's modal_eval.py
├── models.py                    # MODIFY — add LaunchCard models
├── main.py                      # MODIFY — use orchestrator, add /api/launch
├── requirements.txt             # MODIFY — add modal
├── agent.py                     # KEEP as fallback (not imported)
└── .env                         # unchanged (Modal uses `modal token set`)

frontend/src/
├── components/
│   ├── LaunchCard.tsx            # NEW — stepper UI with approval flow
│   ├── CardsPanel.tsx            # MODIFY — add launch_card case
│   ├── ChatPanel.tsx             # MODIFY — add launch example query
│   └── MessageBubble.tsx         # MODIFY — add launch tool labels
└── types.ts                      # MODIFY — add LaunchCard types
```

---

## Step 1: Backend Models

**File:** `backend/models.py` — append after DraftPostCard

Add:
- `LaunchStatus` enum: proposed, launching, running, completed, failed
- `LaunchType` enum: finetune, eval
- `FinetuneConfig` model — mirrors user's TrainingConfig dataclass: model_name, dataset_name, max_seq_length, load_in_4bit, lora_r, lora_alpha, learning_rate, num_epochs, max_steps, batch_size, gradient_accumulation_steps, gpu_type, push_to_hub, hf_repo_name, wandb_project
- `EvalConfig` model — base_model, lora_model, hf_dataset, limit, use_judge, judge_model, wandb_project
- `CostEstimate` model — gpu_type, estimated_hours, estimated_cost_usd, note
- `LaunchCard` model — card_type="launch_card", title, launch_type, status, config (dict), cost_estimate, summary, modal_function_call_id, wandb_url, requires_approval=True

---

## Step 2: Modal Launcher Tools

**File:** `backend/tools/modal_launcher.py` (NEW)

Two tool functions that ONLY create proposals (never launch):

- `propose_finetune(dataset_name, model_name="Qwen/Qwen2.5-Coder-14B", max_steps=-1, num_epochs=1, lora_r=32, learning_rate=2e-4, gpu_type="A100", wandb_project="qwen-coder-code-gen", push_to_hub=True, hf_repo_name=None)` → returns LaunchCard JSON
- `propose_eval(lora_model, base_model="Qwen/Qwen2.5-Coder-14B", hf_dataset="lilyzhng/uigen-ui-code-gen", limit=20, use_judge=True, wandb_project="uiux-eval")` → returns LaunchCard JSON

Each includes a rough cost estimate heuristic (A100 ~$3.50/hr, H100 ~$4.50/hr).

---

## Step 3: Base Agent Loop

**File:** `backend/agents/base.py` (NEW)

Extract the core loop from `agent.py:run_agent()` (lines 519-635) into a parameterized function:

```python
async def run_subagent(
    message: str,
    history: list[dict] | None,
    *,
    system_prompt: str,
    tools: list[dict],
    tool_dispatch: dict,
    card_tool_mapping: dict[str, str],  # tool_name -> card_type
) -> AsyncGenerator[str, None]:
```

Key change: the hardcoded if/elif chain for card emission (agent.py lines 596-626) is replaced by the `card_tool_mapping` dict. Each subagent declares which tools produce cards.

Also extract `_execute_tool()` and `_summarize_tool_result()` into this file.

---

## Step 4: Subagent Modules

**Files:** `backend/agents/training.py`, `data.py`, `scout.py`, `launch.py` (all NEW)

Each module defines 4 constants:
- `SYSTEM_PROMPT` — focused domain prompt (extracted from the monolithic prompt in agent.py)
- `TOOLS` — only the tool schemas for this domain (copied from agent.py TOOLS list)
- `TOOL_DISPATCH` — maps tool names to functions for this domain
- `CARD_TOOL_MAPPING` — which tools emit cards and their card_type

| Agent | Tools | Card Mappings |
|-------|-------|---------------|
| training | get_wandb_info, list_wandb_runs, get_run_metrics, analyze_run_health | analyze_run_health → wandb_health |
| data | search_hf_datasets, discover_dataset_schema, run_sql_query, compute_stats, generate_plot_data, create_data_card | create_data_card → data_card |
| scout | search_hf_datasets, search_hf_models, create_scout_card, create_draft_post_card | create_scout_card → scout_card, create_draft_post_card → draft_post_card |
| launch | propose_finetune, propose_eval | propose_finetune → launch_card, propose_eval → launch_card |

Note: `search_hf_datasets` appears in both data and scout agents (it's a shared tool function from sql_analyst.py).

---

## Step 5: Orchestrator

**File:** `backend/orchestrator.py` (NEW)

```python
async def run_orchestrator(message, history) -> AsyncGenerator[str, None]:
    category = await _classify_intent(message)  # lightweight Claude call
    if category == "general":
        # respond directly without tools
    else:
        # delegate to the matching subagent via run_subagent()
```

Intent classification uses a focused routing prompt with categories: training, data, scout, launch, general. One extra LLM call (~300ms), but keeps each subagent focused with 2-6 tools instead of 16+.

---

## Step 6: Wire main.py

**File:** `backend/main.py`

Changes:
1. Import `run_orchestrator` instead of `run_agent`
2. `chat()` endpoint calls `run_orchestrator()` instead of `run_agent()`
3. Add `POST /api/launch` endpoint:

```python
@app.post("/api/launch")
async def launch_job(req: LaunchRequest):
    # Uses modal.Function.from_name("sofa-genius-launcher", "run_finetune").spawn(config)
    # Returns { success, function_call_id, wandb_project } or { error }
```

Uses Modal's `.spawn()` (non-blocking) so the endpoint returns immediately. The job runs on Modal GPUs asynchronously.

4. Add `modal>=0.67.0` to `backend/requirements.txt`

---

## Step 7: Modal App (deployable)

**Files:** `backend/modal_app/app.py`, `finetune.py`, `eval.py` (all NEW)

Adapted from user's existing code:
- `app.py` — defines `modal.App("sofa-genius-launcher")`, images, volumes, secrets
- `finetune.py` — `run_finetune(config_dict: dict)` adapted from `Qwen3-Coder/unsloth/modal_coder_base.py`
- `eval.py` — `run_evaluation(config_dict: dict)` adapted from `Qwen3-Coder/unsloth/modal_eval.py`

Key changes from user's originals:
- Accept config as dict (not dataclass) for JSON serialization
- Return result dict with wandb_url, final_loss, runtime_minutes
- Use shared Modal volumes prefixed with "sofa-genius-"

Deploy once: `modal deploy backend/modal_app/app.py`

---

## Step 8: Frontend Types

**File:** `frontend/src/types.ts`

Add: `LaunchStatus`, `LaunchType`, `CostEstimate`, `LaunchCard` interfaces.
Update `CardData` union to include `LaunchCard`.

---

## Step 9: LaunchCard Component

**File:** `frontend/src/components/LaunchCard.tsx` (NEW)

Follows DraftPostCard pattern exactly:
- **Stepper** — 4 steps: Proposed → Launching → Running → Completed (with failed state)
- **Summary** — natural language description of the job
- **Cost estimate** — GPU type, estimated hours, estimated USD
- **Approve & Launch button** — states: idle → launching → launched → error (same pattern as DraftPostCard)
- **Expandable config** — key-value grid showing model, dataset, hyperparams
- **Post-launch** — shows W&B link

Also update:
- `CardsPanel.tsx` — add `launch_card` case + import
- `MessageBubble.tsx` — add `propose_finetune` and `propose_eval` to TOOL_LABELS
- `ChatPanel.tsx` — add launch example query, import `Rocket` icon

---

## Build Order

| # | What | Est. | Depends on |
|---|------|------|------------|
| 1 | Backend models (LaunchCard etc.) | 5 min | — |
| 2 | Modal launcher tools (propose_finetune, propose_eval) | 10 min | 1 |
| 3 | Base agent loop (agents/base.py) | 15 min | — |
| 4 | Subagent modules (training, data, scout, launch) | 15 min | 3 |
| 5 | Orchestrator | 10 min | 3, 4 |
| 6 | Wire main.py + /api/launch endpoint | 5 min | 5 |
| 7 | Frontend types + LaunchCard component | 20 min | 1 |
| 8 | Frontend wiring (CardsPanel, MessageBubble, ChatPanel) | 5 min | 7 |
| 9 | Modal app (adapt user's existing code) | 20 min | — |
| 10 | Deploy Modal app + end-to-end test | 10 min | all |

---

## Verification

1. **Subagent routing:** "hello" → general, "check my runs" → training, "analyze dataset X" → data, "find models for code gen" → scout, "fine-tune Qwen" → launch
2. **Existing features work:** W&B health cards, data cards, scout cards, draft post cards all render the same as before
3. **Launch flow:** Ask "Fine-tune Qwen2.5-Coder on lilyzhng/uigen-ui-code-gen" → LaunchCard appears with config + cost → click "Approve & Launch" → Modal job spawns → W&B link shown
4. **Missing Modal credentials:** If Modal isn't configured, clicking Launch shows clear error
5. **TypeScript:** `npx tsc --noEmit` passes clean
6. **SSE format:** No changes to event types — frontend hook works without modification
