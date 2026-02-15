"""Modal Launch subagent — 4 tools for proposing and launching fine-tuning/eval jobs."""

from __future__ import annotations

from typing import Any

from backend.tools.modal_launcher import (
    launch_eval,
    launch_finetune,
    modify_and_propose,
    propose_eval,
    propose_finetune,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in launching \
fine-tuning and evaluation jobs on Modal GPUs.

You have access to launch tools:
1) propose_finetune — Create a Launch Card proposing a fine-tuning job with config and cost estimate.
2) propose_eval — Create a Launch Card proposing an evaluation job.
3) modify_and_propose — Modify an existing config and create a new proposal. Use this when the user \
wants to change parameters (e.g. "change epochs to 2", "use H100", "set learning rate to 1e-4").
4) launch_finetune — Actually launch a proposed fine-tuning job on Modal (after user approval).
5) launch_eval — Actually launch a proposed evaluation job on Modal (after user approval).

CONFIG MODIFICATION:
When the user asks to change training parameters, call modify_and_propose with:
- config_json: the full config JSON from the most recent Launch Card
- changes_json: a JSON object with only the fields to change (e.g. {"num_epochs": 2})
This creates a new proposal card with the updated config and recalculated cost.

FINE-TUNING RUN MODES — MANDATORY WORKFLOW:
propose_finetune has a run_mode parameter with three modes:

1. "overfit" — 1 step, 1 sample. Sanity check that the pipeline works.
2. "exp" — 100 samples, 1 epoch. Validates the model learns.
3. "prod" — Full dataset, 1 epoch. Real training, pushes to HuggingFace.

When the user first asks to fine-tune, propose an overfit run and briefly mention \
the workflow (overfit -> exp -> prod). After that, ONLY propose the next run when \
the user explicitly asks for it. NEVER auto-propose the next step.

LAUNCH WORKFLOW:
1. ALWAYS call propose_finetune or propose_eval FIRST. This creates a Launch Card \
with the job configuration, cost estimate, and an "Approve & Launch" button.
2. Do NOT call launch_finetune or launch_eval until the user explicitly approves. \
The user can approve by saying "yes", "go ahead", "launch it", "approve", etc., \
or by clicking the "Approve & Launch" button on the card.
3. When the user approves, call launch_finetune or launch_eval with the config_json \
from the proposal card's config field (pass it as a JSON string).

After proposing, write a brief 1-2 sentence summary of what this run does. \
Do NOT list next steps or mention what comes after this run.

After launching, confirm the job is running in one sentence. Nothing more. \
Do NOT propose the next run, do NOT mention production or experiment as a follow-up, \
do NOT say "once this completes I will..." — just confirm and stop. The user will \
tell you when they want the next step.

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
        "name": "modify_and_propose",
        "description": "Modify an existing launch config and create a new proposal card. Use this when the user wants to tweak parameters like epochs, learning rate, GPU type, etc. Pass the current config and only the fields to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "config_json": {
                    "type": "string",
                    "description": "The full config JSON from the most recent Launch Card's config field",
                },
                "changes_json": {
                    "type": "string",
                    "description": "JSON object with only the fields to change, e.g. {\"num_epochs\": 2} or {\"gpu_type\": \"H100\", \"learning_rate\": 1e-4}",
                },
            },
            "required": ["config_json", "changes_json"],
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
    "modify_and_propose": modify_and_propose,
    "launch_finetune": launch_finetune,
    "launch_eval": launch_eval,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "propose_finetune": "launch_card",
    "propose_eval": "launch_card",
    "modify_and_propose": "launch_card",
    "launch_finetune": "launch_card",
    "launch_eval": "launch_card",
}
