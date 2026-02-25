"""Modal Launch subagent — 3 tools for proposing and launching training jobs."""

from __future__ import annotations

from typing import Any

from backend.tools.modal_launcher import (
    launch_training,
    modify_and_propose,
    propose_training,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in launching \
training jobs on Modal GPUs.

TRAINING ADVISOR — REASONING CHAIN:
Before calling propose_training, always walk through these steps internally:

1. GOAL: Restate what the user wants to achieve (e.g. "train a model to call tools", \
"generate React UI code", "follow instructions better").
2. QUALITY SIGNAL: Can output quality be measured programmatically with reward functions? \
   - Yes (e.g. JSON validity, tool correctness, code completeness) → GRPO is viable. \
   - No (e.g. general instruction following, conversational Q&A, summarization) → SFT is safer.
3. DATA: Does the user have a dataset? Note format requirements: \
   - SFT needs input/output pairs (supervised examples). \
   - GRPO needs prompts + reward signals (no reference outputs required).
4. RECOMMEND: Pick a method with brief reasoning. Include cost tradeoffs: \
   SFT ~1x cost, GRPO ~4x slower/more expensive due to multiple generations per step. \
   SFT converges faster and more predictably; GRPO can discover novel solutions but is noisier.
5. TEMPLATE: Select the closest task example for defaults.

Training Methods Taxonomy:
├── SFT (supervised fine-tuning)
│   ├── Example: text-to-SQL
│   ├── Example: instruction following
│   └── Example: conversational Q&A
└── GRPO (reward-based optimization)
    ├── task_type="tool_calling" — rewards: JSON validity, correct tool, correct params, no hallucination
    └── task_type="ui_generation" — rewards: completeness, validity, interactivity, quote balance, length

You have 3 tools:
1) propose_training — Create a Launch Card proposing a training job (SFT or GRPO) with config and cost estimate. \
Set method="sft" or method="grpo". For GRPO, optionally set task_type="tool_calling" or "ui_generation".
2) modify_and_propose — Modify an existing config and create a new proposal. Use this when the user \
wants to change parameters (e.g. "change epochs to 2", "use H100", "set learning rate to 1e-4").
3) launch_training — Actually launch a proposed training job on Modal (after user approval). \
Works for both SFT and GRPO — reads method from config automatically.

CONFIG MODIFICATION:
When the user asks to change training parameters, call modify_and_propose with:
- config_json: the full config JSON from the most recent Launch Card
- changes_json: a JSON object with only the fields to change (e.g. {"num_epochs": 2})
This creates a new proposal card with the updated config and recalculated cost.

RUN MODES — MANDATORY WORKFLOW:
propose_training has a run_mode parameter with three modes:

1. "overfit" — 1 step, minimal samples. Sanity check that the pipeline works.
2. "exp" — Small dataset, limited steps. Validates the model learns.
3. "prod" — Full dataset. Real training, pushes to HuggingFace.

When the user first asks to train, propose an overfit run and briefly mention \
the workflow (overfit -> exp -> prod). After that, ONLY propose the next run when \
the user explicitly asks for it. NEVER auto-propose the next step.

LAUNCH WORKFLOW:
1. ALWAYS call propose_training FIRST. This creates a Launch Card \
with the job configuration, cost estimate, and an "Approve & Launch" button.
2. Do NOT call launch_training until the user explicitly approves. \
The user can approve by saying "yes", "go ahead", "launch it", "approve", etc., \
or by clicking the "Approve & Launch" button on the card.
3. When the user approves, call launch_training with the config_json \
from the proposal card's config field (pass it as a JSON string).

NOTE: For evaluation jobs, users should be directed to the evaluation agent. \
This agent handles fine-tuning (SFT) and GRPO training.

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
- GRPO is ~4x more expensive than SFT for the same dataset size.
IMPORTANT: Never over use emojis in your responses. Use emojis only if it is suitable. \
Never output raw JSON in your response. \
Always propose before launching — never skip the proposal step.\
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "propose_training",
        "description": "Propose a training job (SFT or GRPO). Creates a Launch Card with configuration, cost estimate, and approval button. Does NOT launch the job — the user must approve first. ALWAYS start with run_mode='overfit' for a sanity check.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "HuggingFace dataset to train on (e.g. 'lilyzhng/uigen-ui-code-gen')",
                },
                "method": {
                    "type": "string",
                    "enum": ["sft", "grpo"],
                    "description": "Training method: 'sft' for supervised fine-tuning, 'grpo' for reward-based RL training.",
                    "default": "sft",
                },
                "run_mode": {
                    "type": "string",
                    "enum": ["overfit", "exp", "prod"],
                    "description": "Run mode: 'overfit' (sanity check), 'exp' (small experiment), 'prod' (full training). ALWAYS start with 'overfit'.",
                    "default": "overfit",
                },
                "task_type": {
                    "type": "string",
                    "enum": ["tool_calling", "ui_generation"],
                    "description": "GRPO task variant. Only used when method='grpo'. 'tool_calling' for function calling, 'ui_generation' for React code gen.",
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
                "num_generations": {
                    "type": "integer",
                    "description": "Number of generations per step for GRPO (default set by run_mode)",
                },
                "lora_r": {
                    "type": "integer",
                    "description": "LoRA rank (default 32)",
                    "default": 32,
                },
                "learning_rate": {
                    "type": "number",
                    "description": "Learning rate (default: 2e-4 for SFT, 5e-6 for GRPO)",
                },
                "gpu_type": {
                    "type": "string",
                    "description": "GPU type: 'A100' or 'H100' (default 'A100')",
                    "default": "A100",
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project name (auto-set from method/task_type if omitted)",
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
            "required": ["dataset_name", "method", "run_mode"],
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
        "name": "launch_training",
        "description": "Launch an approved training job on Modal. Works for both SFT and GRPO — reads the method from the config automatically. Only call this AFTER the user has approved the proposal. Pass the config JSON from the proposal card.",
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
    "propose_training": propose_training,
    "modify_and_propose": modify_and_propose,
    "launch_training": launch_training,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "propose_training": "launch_card",
    "modify_and_propose": "launch_card",
    "launch_training": "launch_card",
}
