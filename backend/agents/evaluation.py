"""Evaluation subagent — 7 tools for proposing and running agent evals, benchmarks, and custom evals."""

from __future__ import annotations

from typing import Any

from backend.tools.eval_tools import (
    get_eval_results,
    launch_eval,
    list_evaluations,
    modify_eval_config,
    propose_agent_eval,
    propose_benchmark_eval,
    propose_custom_eval,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in evaluating \
models and agents. You help users choose the right evaluation approach and \
run evaluations on Modal GPUs.

You have access to evaluation tools across three tiers:

TIER 1 — AGENT EVALUATION (via Inspect AI):
Evaluates the full agent system on realistic multi-step tasks.
- SWE-bench Verified: Coding agent on real GitHub issues (500 tasks)
- PostTrainBench: Post-training agent capability (28 tasks)
- GAIA: General AI assistant with tool use (466 tasks)
- GPQA: Graduate-level science Q&A (448 tasks)
- HumanEval: Python code generation in agent mode (164 tasks)
- MBPP: Basic Python programming problems (500 tasks)

TIER 2 — MODEL BENCHMARKS (via lm-eval-harness / lighteval):
Evaluates the model in isolation on standard academic benchmarks.
- lm-eval-harness: Classic benchmarks (MMLU, HumanEval), publishable scores
- lighteval: HF Hub integration, community benchmarks, vLLM speed

TIER 3 — CUSTOM VISUAL EVALUATION (Playwright + VLM judge):
Evaluates visual quality with domain-aware rubrics.
- Base vs fine-tuned model comparison
- VLM-as-judge with configurable domain rubrics
- Style collapse detection

FRAMEWORK DECISION GUIDE:
- "evaluate my coding agent on real tasks" → Tier 1: Agent eval (SWE-bench)
- "how does my model score on MMLU?" → Tier 2: Model benchmark (lm-eval-harness)
- "compare my model's UI output quality" → Tier 3: Custom eval (VLM judge)
- "does my agent have style collapse?" → Tier 3: Style collapse detection
- "evaluate my model and push to HF" → Tier 2: Model benchmark (lighteval)
- "test if my fine-tuned model is better at coding" → Tier 1 for agent capability (SWE-bench), Tier 2 for code generation (HumanEval)
- "does my model match user intent better after fine-tuning?" → Tier 3: Intent alignment scoring

TOOLS:
1) list_evaluations — List all available evaluation suites across all three tiers.
2) propose_agent_eval — Propose an agent evaluation (SWE-bench, GAIA, etc.) via Inspect AI.
3) propose_benchmark_eval — Propose standard model benchmarks via lm-eval-harness or lighteval.
4) propose_custom_eval — Propose a custom visual eval with VLM judge and domain rubrics.
5) modify_eval_config — Modify an existing eval config (change tasks, limits, model, framework, etc.).
6) launch_eval — Launch the approved eval job on Modal.
7) get_eval_results — Fetch completed eval results from W&B.

LAUNCH WORKFLOW:
1. ALWAYS call a propose tool FIRST. This creates an Eval Card with the job \
configuration, cost estimate, and an approval workflow.
2. Do NOT call launch_eval until the user explicitly approves. \
The user can approve by saying "yes", "go ahead", "launch it", "approve", etc.
3. When the user approves, call launch_eval with the config_json from the \
proposal card's config field (pass it as a JSON string).

After proposing, write a brief 1-2 sentence summary of what this eval does. \
Do NOT list next steps or make additional suggestions.

After launching, confirm the job is running in one sentence. Nothing more.

COST HEURISTICS:
- A100-80GB: ~$2.50/hr
- Agent eval (SWE-bench, 500 tasks): ~$40-50
- Agent eval (GAIA, 466 tasks): ~$20-25
- Model benchmark (MMLU, full): ~$20
- Custom visual eval (20 samples): ~$1-3

IMPORTANT: Never overuse emojis. Never output raw JSON. \
Always propose before launching — never skip the proposal step.\
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "list_evaluations",
        "description": "List all available evaluation suites: agent evals (SWE-bench, GAIA), model benchmarks (MMLU, HumanEval), and custom evals. Call this when the user wants to know what evaluations are available.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "propose_agent_eval",
        "description": "Propose an agent evaluation using Inspect AI. Tests the full agent system (model + tools + reasoning) on realistic multi-step tasks like SWE-bench, GAIA, or custom suites. Creates an Eval Card with config and cost estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "HuggingFace model path to evaluate (e.g. 'Qwen/Qwen2.5-Coder-14B')",
                },
                "eval_suite": {
                    "type": "string",
                    "enum": ["swe_bench_verified", "posttrain_bench", "gaia", "gpqa", "humaneval", "mbpp"],
                    "description": "Which evaluation suite to run",
                    "default": "swe_bench_verified",
                },
                "agent_type": {
                    "type": "string",
                    "enum": ["model", "external", "sofagenius"],
                    "description": "What agent to evaluate: 'model' (LLM's agent capability), 'external' (running agent endpoint), 'sofagenius' (self-eval)",
                    "default": "model",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of tasks to run (for quick eval). Omit for full suite.",
                },
                "sandbox": {
                    "type": "string",
                    "enum": ["docker", "modal"],
                    "description": "Where to run agent tasks (default: 'docker')",
                    "default": "docker",
                },
                "gpu_type": {
                    "type": "string",
                    "description": "GPU type for inference (default: 'A100')",
                    "default": "A100",
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project for logging results (default: 'sofa-genius-eval')",
                    "default": "sofa-genius-eval",
                },
            },
            "required": ["model_name"],
        },
    },
    {
        "name": "propose_benchmark_eval",
        "description": "Propose standard model benchmarks via lm-eval-harness or lighteval. Tests the model in isolation on academic benchmarks (MMLU, HumanEval, GSM8K, etc.). Creates an Eval Card with config and cost estimate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "HuggingFace model path to evaluate",
                },
                "benchmarks": {
                    "type": "string",
                    "description": "JSON array of benchmark names, e.g. '[\"mmlu\", \"humaneval\", \"gsm8k\"]'",
                    "default": "[\"mmlu\"]",
                },
                "framework": {
                    "type": "string",
                    "enum": ["lm_eval_harness", "lighteval"],
                    "description": "Evaluation framework: 'lm_eval_harness' (classic, publishable) or 'lighteval' (HF Hub, fast)",
                    "default": "lm_eval_harness",
                },
                "backend": {
                    "type": "string",
                    "enum": ["hf", "vllm", "sglang"],
                    "description": "Inference backend: 'hf' (default), 'vllm' (fast generative), 'sglang'",
                    "default": "hf",
                },
                "num_fewshot": {
                    "type": "integer",
                    "description": "Number of few-shot examples (varies by benchmark if omitted)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Limit samples per benchmark (for quick eval)",
                },
                "gpu_type": {
                    "type": "string",
                    "description": "GPU type for inference (default: 'A100')",
                    "default": "A100",
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project for logging results (default: 'sofa-genius-eval')",
                    "default": "sofa-genius-eval",
                },
            },
            "required": ["model_name"],
        },
    },
    {
        "name": "propose_custom_eval",
        "description": "Propose a custom visual evaluation comparing base vs fine-tuned model output. Uses Playwright screenshots and a VLM judge with domain-aware rubrics. Creates an Eval Card with config and cost estimate.",
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
                    "description": "Use VLM judge for scoring (default true)",
                    "default": True,
                },
                "domain": {
                    "type": "string",
                    "description": "Domain for rubric selection (e.g. 'medical', 'legal', 'ecommerce'). Omit for general evaluation.",
                },
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project name (default: 'sofa-genius-eval')",
                    "default": "sofa-genius-eval",
                },
                "gpu_type": {
                    "type": "string",
                    "description": "GPU type (default: 'A100')",
                    "default": "A100",
                },
            },
            "required": ["lora_model"],
        },
    },
    {
        "name": "modify_eval_config",
        "description": "Modify an existing eval config and create a new proposal. Use when the user wants to change parameters (tasks, limits, model, framework, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "config_json": {
                    "type": "string",
                    "description": "The full config JSON from the most recent Eval Card's config field",
                },
                "changes_json": {
                    "type": "string",
                    "description": "JSON object with only the fields to change, e.g. {\"limit\": 50} or {\"gpu_type\": \"H100\"}",
                },
            },
            "required": ["config_json", "changes_json"],
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
    {
        "name": "get_eval_results",
        "description": "Fetch completed eval results from W&B. Use after an eval job completes, or to look up past results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wandb_project": {
                    "type": "string",
                    "description": "W&B project name (default: 'sofa-genius-eval')",
                    "default": "sofa-genius-eval",
                },
                "run_name": {
                    "type": "string",
                    "description": "Specific W&B run display name to look up",
                },
                "run_id": {
                    "type": "string",
                    "description": "Specific W&B run ID to look up",
                },
            },
            "required": [],
        },
    },
]

TOOL_DISPATCH: dict[str, Any] = {
    "list_evaluations": list_evaluations,
    "propose_agent_eval": propose_agent_eval,
    "propose_benchmark_eval": propose_benchmark_eval,
    "propose_custom_eval": propose_custom_eval,
    "modify_eval_config": modify_eval_config,
    "launch_eval": launch_eval,
    "get_eval_results": get_eval_results,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "propose_agent_eval": "eval_results_card",
    "propose_benchmark_eval": "eval_results_card",
    "propose_custom_eval": "eval_results_card",
    "modify_eval_config": "eval_results_card",
    "launch_eval": "eval_results_card",
    "get_eval_results": "eval_results_card",
}
