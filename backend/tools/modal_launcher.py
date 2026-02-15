"""Modal launch tools — propose and launch fine-tuning / evaluation jobs."""

from __future__ import annotations

import json
import os
from datetime import datetime


def _wandb_url(project: str) -> str:
    entity = os.getenv("WANDB_ENTITY", "me")
    return f"https://wandb.ai/{entity}/{project}"


# ---------------------------------------------------------------------------
# Cost heuristics
# ---------------------------------------------------------------------------
_GPU_COST_PER_HOUR = {
    "A100": 3.50,
    "H100": 4.50,
}


def _estimate_finetune_cost(gpu_type: str, num_epochs: int, max_steps: int) -> dict:
    rate = _GPU_COST_PER_HOUR.get(gpu_type, 3.50)
    if max_steps > 0:
        # Rough heuristic: ~2 steps/sec on A100 for 14B model with batch 1
        estimated_hours = round(max_steps / 7200, 2)  # ~2 steps/s
        note = f"Based on ~{max_steps} steps at ~2 steps/sec"
    else:
        # Full epoch: estimate 1-3 hours depending on dataset
        estimated_hours = round(1.5 * num_epochs, 2)
        note = f"Rough estimate for {num_epochs} epoch(s) — actual time depends on dataset size"
    estimated_cost = round(estimated_hours * rate, 2)
    return {
        "gpu_type": gpu_type,
        "estimated_hours": estimated_hours,
        "estimated_cost_usd": estimated_cost,
        "note": note,
    }


def _estimate_eval_cost(limit: int, use_judge: bool) -> dict:
    # Eval with judge: ~2 min per sample (generation + screenshot + judging)
    # Eval without judge: ~1 min per sample
    per_sample_min = 2.0 if use_judge else 1.0
    estimated_hours = round((limit * per_sample_min) / 60, 2)
    rate = _GPU_COST_PER_HOUR["A100"]
    estimated_cost = round(estimated_hours * rate, 2)
    return {
        "gpu_type": "A100",
        "estimated_hours": estimated_hours,
        "estimated_cost_usd": estimated_cost,
        "note": f"{limit} samples, ~{per_sample_min:.0f} min/sample {'with' if use_judge else 'without'} LLM judge",
    }


# ---------------------------------------------------------------------------
# Proposal tools — create LaunchCard JSON, don't actually launch
# ---------------------------------------------------------------------------

_RUN_MODE_DEFAULTS = {
    "overfit": {
        "max_steps": 1,
        "train_size": 1,
        "num_epochs": 1,
        "push_to_hub": False,
        "label": "Overfit (sanity check)",
        "description": "1-step sanity check to verify the pipeline runs end-to-end without errors.",
    },
    "exp": {
        "max_steps": -1,
        "train_size": 100,
        "num_epochs": 1,
        "push_to_hub": False,
        "label": "Exp (100 samples)",
        "description": "Train on 100 samples for 1 epoch to validate learning and check loss curve.",
    },
    "prod": {
        "max_steps": -1,
        "train_size": None,
        "num_epochs": 1,
        "push_to_hub": True,
        "label": "Prod (full dataset)",
        "description": "Full training on the entire dataset. Model is pushed to HuggingFace.",
    },
}


def propose_finetune(
    dataset_name: str,
    run_mode: str = "overfit",
    model_name: str = "Qwen/Qwen2.5-Coder-14B",
    max_steps: int | None = None,
    num_epochs: int | None = None,
    train_size: int | None = None,
    lora_r: int = 32,
    learning_rate: float = 2e-4,
    gpu_type: str = "A100",
    wandb_project: str = "qwen-coder-code-gen",
    push_to_hub: bool | None = None,
    hf_repo_name: str | None = None,
) -> str:
    """Propose a fine-tuning job — returns a LaunchCard JSON (status=proposed).

    run_mode sets sensible defaults:
    - "overfit": 1 step, 1 sample — sanity check that the pipeline works
    - "experiment": 100 samples, 1 epoch — validate learning
    - "production": full dataset, 1 epoch — real training, push to HuggingFace
    Explicit parameters override run_mode defaults.
    """
    if run_mode not in _RUN_MODE_DEFAULTS:
        run_mode = "overfit"

    mode = _RUN_MODE_DEFAULTS[run_mode]

    # Apply mode defaults, allow explicit overrides
    _max_steps = max_steps if max_steps is not None else mode["max_steps"]
    _num_epochs = num_epochs if num_epochs is not None else mode["num_epochs"]
    _train_size = train_size if train_size is not None else mode["train_size"]
    _push_to_hub = push_to_hub if push_to_hub is not None else mode["push_to_hub"]

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = f"{model_short}-r{lora_r}-{run_mode}-{timestamp}"

    config = {
        "model_name": model_name,
        "dataset_name": dataset_name,
        "max_seq_length": 4096,
        "load_in_4bit": True,
        "lora_r": lora_r,
        "lora_alpha": lora_r,
        "learning_rate": learning_rate,
        "num_epochs": _num_epochs,
        "max_steps": _max_steps,
        "batch_size": 1,
        "gradient_accumulation_steps": 8,
        "gpu_type": gpu_type,
        "push_to_hub": _push_to_hub,
        "hf_repo_name": hf_repo_name or experiment_name,
        "wandb_project": wandb_project,
        "experiment_name": experiment_name,
        "run_mode": run_mode,
    }
    if _train_size is not None:
        config["train_size"] = _train_size

    cost = _estimate_finetune_cost(gpu_type, _num_epochs, _max_steps)

    # Build summary
    if _max_steps > 0:
        steps_desc = f"{_max_steps} step(s)"
    else:
        steps_desc = f"{_num_epochs} epoch(s)"
    if _train_size:
        steps_desc += f", {_train_size} samples"
    else:
        steps_desc += ", full dataset"

    summary = (
        f"[{mode['label']}] Fine-tune {model_short} on {dataset_name} — "
        f"{steps_desc}, LoRA r={lora_r}, lr={learning_rate}, {gpu_type}. "
        f"{mode['description']} "
        f"Estimated cost: ${cost['estimated_cost_usd']:.2f} "
        f"({cost['estimated_hours']}h)."
    )

    card = {
        "card_type": "launch_card",
        "title": f"{mode['label']} — {model_short}",
        "launch_type": "finetune",
        "status": "proposed",
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


def propose_eval(
    lora_model: str,
    base_model: str = "Qwen/Qwen2.5-Coder-14B",
    hf_dataset: str = "lilyzhng/uigen-ui-code-gen",
    limit: int = 20,
    use_judge: bool = True,
    wandb_project: str = "uiux-eval",
) -> str:
    """Propose an evaluation job — returns a LaunchCard JSON (status=proposed)."""
    config = {
        "base_model": base_model,
        "lora_model": lora_model,
        "hf_dataset": hf_dataset,
        "limit": limit,
        "use_judge": use_judge,
        "judge_model": "google/gemini-3-pro-preview",
        "wandb_project": wandb_project,
    }

    cost = _estimate_eval_cost(limit, use_judge)

    lora_short = lora_model.split("/")[-1]
    base_short = base_model.split("/")[-1]
    summary = (
        f"Evaluate {lora_short} vs {base_short} on {limit} test samples from {hf_dataset}. "
        f"{'LLM judge enabled' if use_judge else 'No LLM judge'}. "
        f"Estimated cost: ${cost['estimated_cost_usd']:.2f} "
        f"({cost['estimated_hours']}h on A100)."
    )

    card = {
        "card_type": "launch_card",
        "title": f"Evaluate {lora_short}",
        "launch_type": "eval",
        "status": "proposed",
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


# ---------------------------------------------------------------------------
# Launch tools — actually spawn Modal jobs
# ---------------------------------------------------------------------------

def launch_finetune(config_json: str) -> str:
    """Launch a fine-tuning job on Modal. Call after user approves the proposal."""
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid config JSON: {e}"})

    try:
        import modal
        fn = modal.Function.from_name("sofa-genius-launcher", "run_finetune")
        call = fn.spawn(config)
        function_call_id = call.object_id

        model_short = config.get("model_name", "model").split("/")[-1]
        wandb_project = config.get("wandb_project", "qwen-coder-code-gen")

        card = {
            "card_type": "launch_card",
            "title": f"Fine-tune {model_short}",
            "launch_type": "finetune",
            "status": "running",
            "config": config,
            "cost_estimate": _estimate_finetune_cost(
                config.get("gpu_type", "A100"),
                config.get("num_epochs", 1),
                config.get("max_steps", -1),
            ),
            "summary": f"Fine-tuning job launched on Modal. Monitor on W&B project '{wandb_project}'.",
            "modal_function_call_id": function_call_id,
            "wandb_url": _wandb_url(wandb_project),
            "requires_approval": False,
        }
        return json.dumps(card)

    except Exception as e:
        error_msg = str(e)
        if "modal" in error_msg.lower() or "not found" in error_msg.lower():
            error_msg = (
                f"Modal app not deployed or not accessible. "
                f"Deploy with: modal deploy backend/modal_app/app.py. "
                f"Original error: {error_msg}"
            )
        card = {
            "card_type": "launch_card",
            "title": "Fine-tune — Launch Failed",
            "launch_type": "finetune",
            "status": "failed",
            "config": config,
            "cost_estimate": None,
            "summary": f"Failed to launch: {error_msg}",
            "modal_function_call_id": None,
            "wandb_url": None,
            "requires_approval": False,
        }
        return json.dumps(card)


def launch_eval(config_json: str) -> str:
    """Launch an evaluation job on Modal. Call after user approves the proposal."""
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid config JSON: {e}"})

    try:
        import modal
        fn = modal.Function.from_name("sofa-genius-launcher", "run_evaluation")
        call = fn.spawn(config)
        function_call_id = call.object_id

        lora_short = config.get("lora_model", "model").split("/")[-1]
        wandb_project = config.get("wandb_project", "uiux-eval")

        card = {
            "card_type": "launch_card",
            "title": f"Evaluate {lora_short}",
            "launch_type": "eval",
            "status": "running",
            "config": config,
            "cost_estimate": _estimate_eval_cost(
                config.get("limit", 20),
                config.get("use_judge", True),
            ),
            "summary": f"Evaluation job launched on Modal. Monitor on W&B project '{wandb_project}'.",
            "modal_function_call_id": function_call_id,
            "wandb_url": _wandb_url(wandb_project),
            "requires_approval": False,
        }
        return json.dumps(card)

    except Exception as e:
        error_msg = str(e)
        if "modal" in error_msg.lower() or "not found" in error_msg.lower():
            error_msg = (
                f"Modal app not deployed or not accessible. "
                f"Deploy with: modal deploy backend/modal_app/app.py. "
                f"Original error: {error_msg}"
            )
        card = {
            "card_type": "launch_card",
            "title": "Evaluation — Launch Failed",
            "launch_type": "eval",
            "status": "failed",
            "config": config,
            "cost_estimate": None,
            "summary": f"Failed to launch: {error_msg}",
            "modal_function_call_id": None,
            "wandb_url": None,
            "requires_approval": False,
        }
        return json.dumps(card)
