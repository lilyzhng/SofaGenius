"""Modal Launch subagent — 4 tools for proposing and launching fine-tuning/eval jobs."""

from __future__ import annotations

from typing import Any

from backend.tools.modal_launcher import (
    launch_eval,
    launch_finetune,
    propose_eval,
    propose_finetune,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in launching \
fine-tuning and evaluation jobs on Modal GPUs.

You have access to launch tools:
1) propose_finetune — Create a Launch Card proposing a fine-tuning job with config and cost estimate.
2) propose_eval — Create a Launch Card proposing an evaluation job.
3) launch_finetune — Actually launch a proposed fine-tuning job on Modal (after user approval).
4) launch_eval — Actually launch a proposed evaluation job on Modal (after user approval).

FINE-TUNING RUN MODES — MANDATORY WORKFLOW:
propose_finetune has a run_mode parameter with three modes. You MUST follow this \
progression and ALWAYS start with overfit:

1. "overfit" — 1 step, 1 sample. A sanity check that verifies the pipeline runs \
end-to-end without errors. Costs almost nothing. ALWAYS propose this first.
2. "exp" — 100 samples, 1 epoch. Validates that the model actually learns \
(loss should decrease). Catches data formatting issues. Propose this after the \
overfit run succeeds.
3. "prod" — Full dataset, 1 epoch. Real training run. Model is pushed to \
HuggingFace. Propose this only after exp succeeds.

CRITICAL: When the user asks to fine-tune, ALWAYS start by proposing an overfit \
run first. Explain this is the standard workflow: overfit -> exp -> prod. \
Do NOT skip to prod. After each run completes, suggest the next step.

LAUNCH WORKFLOW:
1. ALWAYS call propose_finetune or propose_eval FIRST. This creates a Launch Card \
with the job configuration, cost estimate, and an "Approve & Launch" button.
2. Do NOT call launch_finetune or launch_eval until the user explicitly approves. \
The user can approve by saying "yes", "go ahead", "launch it", "approve", etc., \
or by clicking the "Approve & Launch" button on the card.
3. When the user approves, call launch_finetune or launch_eval with the config_json \
from the proposal card's config field (pass it as a JSON string).

After proposing, write a brief summary explaining:
- The run mode and what it tests
- The estimated cost and GPU type
- That the user needs to approve before it launches
- What the next step will be after this run

After launching, mention:
- The job is running on Modal
- They can monitor it on W&B (provide the project name)

COST HEURISTICS:
- A100-80GB: ~$3.50/hr
- H100: ~$4.50/hr
- Overfit run: ~$0.01 (seconds)
- Exp run: ~$0.50-1.00 (minutes)
- Prod run: ~$3-10 (1-3 hours depending on dataset)
- Evaluation: ~$1-3 (0.5-1 hour depending on sample count)

IMPORTANT: Never over use emojis in your responses. Use emojis only if it is suitable. \
Never output raw JSON in your response. \
Always propose before launching — never skip the proposal step.\
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "propose_finetune",
        "description": "Propose a fine-tuning job. Creates a Launch Card with configuration, cost estimate, and approval button. Does NOT launch the job — the user must approve first. ALWAYS start with run_mode='overfit' for a sanity check.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "HuggingFace dataset to fine-tune on (e.g. 'lilyzhng/uigen-ui-code-gen')",
                },
                "run_mode": {
                    "type": "string",
                    "enum": ["overfit", "exp", "prod"],
                    "description": "Run mode: 'overfit' (1 step sanity check), 'exp' (100 samples, 1 epoch), 'prod' (full dataset, 1 epoch). ALWAYS start with 'overfit'.",
                    "default": "overfit",
                },
                "model_name": {
                    "type": "string",
                    "description": "Base model to fine-tune (default: 'Qwen/Qwen2.5-Coder-14B')",
                    "default": "Qwen/Qwen2.5-Coder-14B",
                },
                "max_steps": {
                    "type": "integer",
                    "description": "Override max training steps (set by run_mode if omitted)",
                },
                "num_epochs": {
                    "type": "integer",
                    "description": "Override number of training epochs (set by run_mode if omitted)",
                },
                "train_size": {
                    "type": "integer",
                    "description": "Override number of training samples (set by run_mode if omitted)",
                },
                "lora_r": {
                    "type": "integer",
                    "description": "LoRA rank (default 32)",
                    "default": 32,
                },
                "learning_rate": {
                    "type": "number",
                    "description": "Learning rate (default 2e-4)",
                    "default": 0.0002,
                },
                "gpu_type": {
                    "type": "string",
                    "description": "GPU type: 'A100' or 'H100' (default 'A100')",
                    "default": "A100",
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project name (default 'qwen-coder-code-gen')",
                    "default": "qwen-coder-code-gen",
                },
                "push_to_hub": {
                    "type": "boolean",
                    "description": "Override push to HuggingFace Hub (set by run_mode if omitted)",
                },
                "hf_repo_name": {
                    "type": "string",
                    "description": "HuggingFace repo name for the trained model (optional, auto-generated if omitted)",
                },
            },
            "required": ["dataset_name", "run_mode"],
        },
    },
    {
        "name": "propose_eval",
        "description": "Propose an evaluation job comparing a base model against a fine-tuned model. Creates a Launch Card with configuration, cost estimate, and approval button.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lora_model": {
                    "type": "string",
                    "description": "HuggingFace path to the fine-tuned LoRA model to evaluate",
                },
                "base_model": {
                    "type": "string",
                    "description": "Base model to compare against (default: 'Qwen/Qwen2.5-Coder-14B')",
                    "default": "Qwen/Qwen2.5-Coder-14B",
                },
                "hf_dataset": {
                    "type": "string",
                    "description": "HuggingFace dataset for test samples (default: 'lilyzhng/uigen-ui-code-gen')",
                    "default": "lilyzhng/uigen-ui-code-gen",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of test samples (default 20)",
                    "default": 20,
                },
                "use_judge": {
                    "type": "boolean",
                    "description": "Use LLM judge for scoring (default true)",
                    "default": True,
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project name (default 'uiux-eval')",
                    "default": "uiux-eval",
                },
            },
            "required": ["lora_model"],
        },
    },
    {
        "name": "launch_finetune",
        "description": "Launch an approved fine-tuning job on Modal. Only call this AFTER the user has approved the proposal. Pass the config JSON from the proposal card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "config_json": {
                    "type": "string",
                    "description": "The JSON config string from the proposal card's config field",
                },
            },
            "required": ["config_json"],
        },
    },
    {
        "name": "launch_eval",
        "description": "Launch an approved evaluation job on Modal. Only call this AFTER the user has approved the proposal. Pass the config JSON from the proposal card.",
        "input_schema": {
            "type": "object",
            "properties": {
                "config_json": {
                    "type": "string",
                    "description": "The JSON config string from the proposal card's config field",
                },
            },
            "required": ["config_json"],
        },
    },
]

TOOL_DISPATCH: dict[str, Any] = {
    "propose_finetune": propose_finetune,
    "propose_eval": propose_eval,
    "launch_finetune": launch_finetune,
    "launch_eval": launch_eval,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "propose_finetune": "launch_card",
    "propose_eval": "launch_card",
    "launch_finetune": "launch_card",
    "launch_eval": "launch_card",
}
