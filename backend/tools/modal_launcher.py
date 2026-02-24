"""Modal launch tools — propose and launch fine-tuning / evaluation jobs."""

from __future__ import annotations

import json
import os
from datetime import datetime


def _wandb_url(project: str) -> str:
    entity = os.getenv("WANDB_ENTITY", "me")
    return f"https://wandb.ai/{entity}/{project}"


# ---------------------------------------------------------------------------
# Dataset size lookup
# ---------------------------------------------------------------------------
def _get_dataset_train_size(dataset_name: str) -> int | None:
    """Query HuggingFace API for the number of rows in the training split."""
    try:
        import urllib.request
        url = f"https://datasets-server.huggingface.co/size?dataset={dataset_name}"
        req = urllib.request.Request(url, headers={"User-Agent": "SofaGenius/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        # Find the train split size
        for split_info in data.get("size", {}).get("splits", []):
            if split_info.get("split") == "train":
                return split_info.get("num_rows")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Cost — exact per-second rates from https://modal.com/pricing
# ---------------------------------------------------------------------------
_GPU_COST_PER_SEC = {
    "B200": 0.001736,
    "H200": 0.001261,
    "H100": 0.001097,
    "A100": 0.000694,   # A100-80GB (what we use)
    "A100-40GB": 0.000583,
    "L40S": 0.000542,
    "A10": 0.000306,
    "L4": 0.000222,
    "T4": 0.000164,
}

# Empirical from Modal runs: ~1 sec/step for batch_size=1 on A100-80GB with 14B model
_SECONDS_PER_STEP = 1.0
# Fixed overhead: model loading + data loading + saving + HF push
_OVERHEAD_SECONDS = 120


def _estimate_finetune_cost(
    gpu_type: str,
    num_epochs: int,
    max_steps: int,
    train_samples: int | None = None,
    batch_size: int = 1,
    gradient_accumulation_steps: int = 8,
) -> dict:
    rate_per_sec = _GPU_COST_PER_SEC.get(gpu_type, _GPU_COST_PER_SEC["A100"])

    if max_steps > 0:
        steps = max_steps
        note = f"{steps} step(s)"
    elif train_samples:
        effective_batch = batch_size * gradient_accumulation_steps
        steps = -(-train_samples // effective_batch)  # ceil division
        steps *= num_epochs
        note = f"{train_samples} samples, {num_epochs} epoch(s), ~{steps} steps"
    else:
        # Fallback if we couldn't look up the dataset size
        estimated_seconds = round(1.5 * num_epochs * 3600)
        estimated_cost = round(estimated_seconds * rate_per_sec, 2)
        return {
            "gpu_type": gpu_type,
            "estimated_seconds": estimated_seconds,
            "estimated_cost_usd": estimated_cost,
            "note": f"Rough estimate for {num_epochs} epoch(s) — dataset size unknown",
        }

    estimated_seconds = _OVERHEAD_SECONDS + (steps * _SECONDS_PER_STEP)
    estimated_cost = round(estimated_seconds * rate_per_sec, 4)
    return {
        "gpu_type": gpu_type,
        "estimated_seconds": estimated_seconds,
        "estimated_cost_usd": estimated_cost,
        "note": note,
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

    # Look up the actual dataset size from HuggingFace for accurate cost estimate
    _dataset_total = _get_dataset_train_size(dataset_name)
    if _train_size is None and _dataset_total:
        # prod mode: use full dataset — now we know the real size
        _cost_samples = _dataset_total
    elif _train_size:
        _cost_samples = _train_size
    else:
        _cost_samples = _dataset_total  # may be None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = f"{model_short}-r{lora_r}-{run_mode}-{timestamp}"

    _batch_size = 1
    _grad_accum = 8

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
        "batch_size": _batch_size,
        "gradient_accumulation_steps": _grad_accum,
        "gpu_type": gpu_type,
        "push_to_hub": _push_to_hub,
        "hf_repo_name": hf_repo_name or experiment_name,
        "wandb_project": wandb_project,
        "experiment_name": experiment_name,
        "run_mode": run_mode,
    }
    if _train_size is not None:
        config["train_size"] = _train_size

    cost = _estimate_finetune_cost(
        gpu_type, _num_epochs, _max_steps,
        train_samples=_cost_samples,
        batch_size=_batch_size,
        gradient_accumulation_steps=_grad_accum,
    )

    # Build summary
    if _max_steps > 0:
        steps_desc = f"{_max_steps} step(s)"
    else:
        steps_desc = f"{_num_epochs} epoch(s)"
    if _train_size:
        steps_desc += f", {_train_size} samples"
    elif _dataset_total:
        steps_desc += f", {_dataset_total} samples (full dataset)"
    else:
        steps_desc += ", full dataset"

    summary = (
        f"[{mode['label']}] Fine-tune {model_short} on {dataset_name} — "
        f"{steps_desc}, LoRA r={lora_r}, lr={learning_rate}, {gpu_type}. "
        f"{mode['description']} "
        f"Estimated cost: ${cost['estimated_cost_usd']:.4f} "
        f"({cost['note']})."
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


def modify_and_propose(config_json: str, changes_json: str) -> str:
    """Modify an existing launch config and create a new proposal.

    Takes the config JSON from an existing card, applies changes, and returns
    a new LaunchCard with the updated config and recalculated cost.
    """
    try:
        config = json.loads(config_json)
        changes = json.loads(changes_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})

    # Apply changes
    config.update(changes)

    # Regenerate experiment name with new timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = config.get("model_name", "model").split("/")[-1]
    lora_r = config.get("lora_r", 32)
    run_mode = config.get("run_mode", "prod")
    experiment_name = f"{model_short}-r{lora_r}-{run_mode}-{timestamp}"
    config["experiment_name"] = experiment_name
    if not changes.get("hf_repo_name"):
        config["hf_repo_name"] = experiment_name

    # Look up dataset size for cost
    dataset_name = config.get("dataset_name", "")
    train_size = config.get("train_size")
    if train_size is None:
        _dataset_total = _get_dataset_train_size(dataset_name) if dataset_name else None
    else:
        _dataset_total = train_size

    # Recalculate cost
    cost = _estimate_finetune_cost(
        config.get("gpu_type", "A100"),
        config.get("num_epochs", 1),
        config.get("max_steps", -1),
        train_samples=_dataset_total,
        batch_size=config.get("batch_size", 1),
        gradient_accumulation_steps=config.get("gradient_accumulation_steps", 8),
    )

    # Build summary
    mode_label = _RUN_MODE_DEFAULTS.get(run_mode, {}).get("label", run_mode)
    _max_steps = config.get("max_steps", -1)
    _num_epochs = config.get("num_epochs", 1)
    if _max_steps > 0:
        steps_desc = f"{_max_steps} step(s)"
    else:
        steps_desc = f"{_num_epochs} epoch(s)"
    if _dataset_total:
        steps_desc += f", {_dataset_total} samples"
    else:
        steps_desc += ", full dataset"

    # Highlight what changed
    changed_keys = ", ".join(f"{k}={v}" for k, v in changes.items())

    summary = (
        f"[{mode_label}] Fine-tune {model_short} on {dataset_name} — "
        f"{steps_desc}, LoRA r={lora_r}, lr={config.get('learning_rate', 2e-4)}, "
        f"{config.get('gpu_type', 'A100')}. "
        f"Updated: {changed_keys}. "
        f"Estimated cost: ${cost['estimated_cost_usd']:.4f} ({cost['note']})."
    )

    card = {
        "card_type": "launch_card",
        "title": f"{mode_label} — {model_short}",
        "launch_type": config.get("launch_type", "finetune"),
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
            "summary": f"Fine-tuning job launched on Modal. W&B run link will appear shortly.",
            "modal_function_call_id": function_call_id,
            "wandb_url": None,
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


