"""Evaluation tools — propose and launch agent evals, benchmarks, and custom evals."""

from __future__ import annotations

import json
import os
from datetime import datetime


# ---------------------------------------------------------------------------
# GPU cost rates (same as modal_launcher.py)
# ---------------------------------------------------------------------------
_GPU_COST_PER_SEC = {
    "B200": 0.001736,
    "H200": 0.001261,
    "H100": 0.001097,
    "A100": 0.000694,
    "A100-40GB": 0.000583,
    "L40S": 0.000542,
    "A10": 0.000306,
    "L4": 0.000222,
    "T4": 0.000164,
}


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------
AGENT_EVAL_SIZES = {
    "swe_bench_verified": {"tasks": 500, "sec_per_task": 120},
    "posttrain_bench": {"tasks": 28, "sec_per_task": 36000},
    "gaia": {"tasks": 466, "sec_per_task": 60},
    "gpqa": {"tasks": 448, "sec_per_task": 10},
    "humaneval": {"tasks": 164, "sec_per_task": 15},
    "mbpp": {"tasks": 500, "sec_per_task": 15},
}

BENCHMARK_SIZES = {
    "mmlu": 14042,
    "hellaswag": 10042,
    "arc_easy": 2376,
    "arc_challenge": 1172,
    "humaneval": 164,
    "gsm8k": 1319,
    "winogrande": 1267,
    "truthfulqa": 817,
}

# ~2 seconds per sample for 7B-14B models on A100
_BENCHMARK_SEC_PER_SAMPLE = 2.0
_OVERHEAD_SECONDS = 120


def _estimate_agent_eval_cost(
    eval_suite: str,
    limit: int | None,
    gpu_type: str = "A100",
) -> dict:
    rate = _GPU_COST_PER_SEC.get(gpu_type, _GPU_COST_PER_SEC["A100"])
    info = AGENT_EVAL_SIZES.get(eval_suite, {"tasks": 100, "sec_per_task": 60})
    tasks = min(limit, info["tasks"]) if limit else info["tasks"]
    estimated_seconds = _OVERHEAD_SECONDS + (tasks * info["sec_per_task"])
    estimated_cost = round(estimated_seconds * rate, 2)
    return {
        "gpu_type": gpu_type,
        "estimated_seconds": estimated_seconds,
        "estimated_cost_usd": estimated_cost,
        "note": f"{tasks} tasks, ~{info['sec_per_task']}s/task on {gpu_type}",
    }


def _estimate_benchmark_cost(
    benchmarks: list[str],
    limit: int | None,
    gpu_type: str = "A100",
) -> dict:
    rate = _GPU_COST_PER_SEC.get(gpu_type, _GPU_COST_PER_SEC["A100"])
    total_samples = 0
    for bench in benchmarks:
        size = BENCHMARK_SIZES.get(bench, 1000)
        total_samples += min(limit, size) if limit else size
    estimated_seconds = _OVERHEAD_SECONDS + (total_samples * _BENCHMARK_SEC_PER_SAMPLE)
    estimated_cost = round(estimated_seconds * rate, 2)
    return {
        "gpu_type": gpu_type,
        "estimated_seconds": estimated_seconds,
        "estimated_cost_usd": estimated_cost,
        "note": f"{total_samples} total samples across {len(benchmarks)} benchmark(s)",
    }


def _estimate_custom_eval_cost(
    limit: int,
    use_judge: bool,
    gpu_type: str = "A100",
) -> dict:
    per_sample_sec = 120.0 if use_judge else 60.0
    estimated_seconds = round(limit * per_sample_sec + _OVERHEAD_SECONDS)
    rate = _GPU_COST_PER_SEC.get(gpu_type, _GPU_COST_PER_SEC["A100"])
    estimated_cost = round(estimated_seconds * rate, 4)
    return {
        "gpu_type": gpu_type,
        "estimated_seconds": estimated_seconds,
        "estimated_cost_usd": estimated_cost,
        "note": f"{limit} samples, ~{per_sample_sec:.0f}s/sample {'with' if use_judge else 'without'} VLM judge",
    }


# ---------------------------------------------------------------------------
# Tool 1: list_evaluations
# ---------------------------------------------------------------------------
def list_evaluations() -> str:
    """List all available evaluation suites across all three tiers."""
    result = {
        "agent_evals": {
            "description": "Tier 1: Agent evaluation via Inspect AI — tests full agent systems on realistic tasks",
            "suites": {
                "swe_bench_verified": {
                    "description": "Coding agent on real GitHub issues",
                    "tasks": 500,
                    "environment": "Docker sandbox with real repos",
                },
                "posttrain_bench": {
                    "description": "Post-training agent capability (fine-tune a base LLM to maximize benchmark score)",
                    "tasks": 28,
                    "environment": "H100 GPU sandbox",
                },
                "gaia": {
                    "description": "General AI assistant with tool use",
                    "tasks": 466,
                    "environment": "Web browser, file system, APIs",
                },
                "gpqa": {
                    "description": "Graduate-level science Q&A",
                    "tasks": 448,
                    "environment": "Standard",
                },
                "humaneval": {
                    "description": "Python code generation (agent mode)",
                    "tasks": 164,
                    "environment": "Python sandbox",
                },
                "mbpp": {
                    "description": "Basic Python programming problems",
                    "tasks": 500,
                    "environment": "Python sandbox",
                },
            },
        },
        "benchmark_evals": {
            "description": "Tier 2: Model benchmarks via lm-eval-harness or lighteval — tests model in isolation",
            "frameworks": {
                "lm_eval_harness": "Classic benchmarks (MMLU, HumanEval), publishable scores",
                "lighteval": "HF Hub integration, community benchmarks, vLLM speed",
            },
            "benchmarks": {
                "mmlu": {"samples": 14042, "description": "Massive Multitask Language Understanding"},
                "hellaswag": {"samples": 10042, "description": "Commonsense reasoning"},
                "arc_easy": {"samples": 2376, "description": "AI2 Reasoning Challenge (easy)"},
                "arc_challenge": {"samples": 1172, "description": "AI2 Reasoning Challenge (hard)"},
                "humaneval": {"samples": 164, "description": "Python code generation"},
                "gsm8k": {"samples": 1319, "description": "Grade school math"},
                "winogrande": {"samples": 1267, "description": "Commonsense coreference"},
                "truthfulqa": {"samples": 817, "description": "Truthful question answering"},
            },
        },
        "custom_evals": {
            "description": "Tier 3: Custom visual eval — Playwright screenshots + VLM judge with domain-aware rubrics",
            "capabilities": [
                "Base vs fine-tuned model comparison",
                "VLM-as-judge with configurable domain rubrics",
                "Style collapse detection across domains",
                "Per-dimension scoring (intent alignment, domain fit, aesthetics)",
            ],
        },
    }
    return json.dumps(result)


# ---------------------------------------------------------------------------
# Tool 2: propose_agent_eval
# ---------------------------------------------------------------------------
def propose_agent_eval(
    model_name: str,
    eval_suite: str = "swe_bench_verified",
    agent_type: str = "model",
    limit: int | None = None,
    sandbox: str = "docker",
    gpu_type: str = "A100",
    wandb_project: str = "sofa-genius-eval",
) -> str:
    """Propose an agent evaluation via Inspect AI."""
    cost = _estimate_agent_eval_cost(eval_suite, limit, gpu_type)
    info = AGENT_EVAL_SIZES.get(eval_suite, {"tasks": 100})
    tasks = min(limit, info["tasks"]) if limit else info["tasks"]

    model_short = model_name.split("/")[-1]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    config = {
        "model_name": model_name,
        "eval_suite": eval_suite,
        "agent_type": agent_type,
        "limit": limit,
        "sandbox": sandbox,
        "gpu_type": gpu_type,
        "wandb_project": wandb_project,
        "experiment_name": f"agent-{model_short}-{eval_suite}-{timestamp}",
    }

    summary = (
        f"Agent eval: {model_short} on {eval_suite} ({tasks} tasks). "
        f"Agent type: {agent_type}, sandbox: {sandbox}. "
        f"Estimated cost: ${cost['estimated_cost_usd']:.2f} ({cost['note']})."
    )

    card = {
        "card_type": "eval_results_card",
        "title": f"Agent Eval — {model_short} on {eval_suite}",
        "eval_tier": "agent",
        "status": "proposed",
        "model_name": model_name,
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "eval_suite": eval_suite,
        "total_tasks": tasks,
        "avg_score": None,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


# ---------------------------------------------------------------------------
# Tool 3: propose_benchmark_eval
# ---------------------------------------------------------------------------
def propose_benchmark_eval(
    model_name: str,
    benchmarks: str = '["mmlu"]',
    framework: str = "lm_eval_harness",
    backend: str = "hf",
    num_fewshot: int | None = None,
    limit: int | None = None,
    gpu_type: str = "A100",
    wandb_project: str = "sofa-genius-eval",
) -> str:
    """Propose standard model benchmarks via lm-eval-harness or lighteval."""
    try:
        bench_list = json.loads(benchmarks)
    except json.JSONDecodeError:
        bench_list = [benchmarks]

    cost = _estimate_benchmark_cost(bench_list, limit, gpu_type)
    model_short = model_name.split("/")[-1]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    config = {
        "model_name": model_name,
        "benchmarks": bench_list,
        "framework": framework,
        "backend": backend,
        "num_fewshot": num_fewshot,
        "limit": limit,
        "gpu_type": gpu_type,
        "wandb_project": wandb_project,
        "experiment_name": f"bench-{model_short}-{framework}-{timestamp}",
    }

    bench_desc = ", ".join(bench_list)
    limit_desc = f" (limit={limit})" if limit else ""
    summary = (
        f"Benchmark eval: {model_short} on [{bench_desc}]{limit_desc} via {framework}. "
        f"Backend: {backend}. "
        f"Estimated cost: ${cost['estimated_cost_usd']:.2f} ({cost['note']})."
    )

    card = {
        "card_type": "eval_results_card",
        "title": f"Benchmark — {model_short}",
        "eval_tier": "benchmark",
        "status": "proposed",
        "model_name": model_name,
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "framework": framework,
        "avg_score": None,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


# ---------------------------------------------------------------------------
# Tool 4: propose_custom_eval
# ---------------------------------------------------------------------------
def propose_custom_eval(
    lora_model: str,
    base_model: str = "Qwen/Qwen2.5-Coder-14B",
    hf_dataset: str = "lilyzhng/uigen-ui-code-gen",
    limit: int = 20,
    use_judge: bool = True,
    domain: str | None = None,
    wandb_project: str = "sofa-genius-eval",
    gpu_type: str = "A100",
) -> str:
    """Propose a custom visual eval with VLM judge and domain-aware rubrics."""
    cost = _estimate_custom_eval_cost(limit, use_judge, gpu_type)
    lora_short = lora_model.split("/")[-1]
    base_short = base_model.split("/")[-1]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    config = {
        "base_model": base_model,
        "lora_model": lora_model,
        "hf_dataset": hf_dataset,
        "limit": limit,
        "use_judge": use_judge,
        "judge_model": "google/gemini-3-pro-preview",
        "domain": domain,
        "gpu_type": gpu_type,
        "wandb_project": wandb_project,
        "experiment_name": f"custom-{lora_short}-vs-{base_short}-{timestamp}",
    }

    domain_desc = f" Domain: {domain}." if domain else ""
    summary = (
        f"Custom visual eval: {lora_short} vs {base_short} on {limit} samples from {hf_dataset}. "
        f"{'VLM judge enabled' if use_judge else 'No VLM judge'}.{domain_desc} "
        f"Estimated cost: ${cost['estimated_cost_usd']:.4f} ({cost['note']})."
    )

    card = {
        "card_type": "eval_results_card",
        "title": f"Custom Eval — {lora_short} vs {base_short}",
        "eval_tier": "custom",
        "status": "proposed",
        "model_name": lora_model,
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "avg_score": None,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


# ---------------------------------------------------------------------------
# Tool 5: modify_eval_config
# ---------------------------------------------------------------------------
def modify_eval_config(config_json: str, changes_json: str) -> str:
    """Modify an existing eval config and create a new proposal."""
    try:
        config = json.loads(config_json)
        changes = json.loads(changes_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})

    config.update(changes)

    # Regenerate experiment name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = config.get("model_name", "model").split("/")[-1]
    eval_suite = config.get("eval_suite", "")
    framework = config.get("framework", "")

    # Determine eval tier from config
    if eval_suite:
        eval_tier = "agent"
        config["experiment_name"] = f"agent-{model_short}-{eval_suite}-{timestamp}"
        cost = _estimate_agent_eval_cost(
            eval_suite,
            config.get("limit"),
            config.get("gpu_type", "A100"),
        )
    elif framework:
        eval_tier = "benchmark"
        config["experiment_name"] = f"bench-{model_short}-{framework}-{timestamp}"
        cost = _estimate_benchmark_cost(
            config.get("benchmarks", []),
            config.get("limit"),
            config.get("gpu_type", "A100"),
        )
    else:
        eval_tier = "custom"
        base_short = config.get("base_model", "base").split("/")[-1]
        config["experiment_name"] = f"custom-{model_short}-vs-{base_short}-{timestamp}"
        cost = _estimate_custom_eval_cost(
            config.get("limit", 20),
            config.get("use_judge", True),
            config.get("gpu_type", "A100"),
        )

    changed_keys = ", ".join(f"{k}={v}" for k, v in changes.items())
    summary = (
        f"Updated eval config for {model_short}. "
        f"Changed: {changed_keys}. "
        f"Estimated cost: ${cost['estimated_cost_usd']:.2f} ({cost['note']})."
    )

    card = {
        "card_type": "eval_results_card",
        "title": f"Eval — {model_short} (updated)",
        "eval_tier": eval_tier,
        "status": "proposed",
        "model_name": config.get("model_name", ""),
        "config": config,
        "cost_estimate": cost,
        "summary": summary,
        "eval_suite": eval_suite or None,
        "framework": framework or None,
        "avg_score": None,
        "modal_function_call_id": None,
        "wandb_url": None,
        "requires_approval": True,
    }
    return json.dumps(card)


# ---------------------------------------------------------------------------
# Tool 6: launch_eval
# ---------------------------------------------------------------------------
def launch_eval(config_json: str) -> str:
    """Launch an approved eval job on Modal."""
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid config JSON: {e}"})

    # Determine which Modal function to call based on config
    eval_suite = config.get("eval_suite")
    framework = config.get("framework")
    base_model = config.get("base_model")

    if eval_suite:
        function_name = "run_agent_eval"
        eval_tier = "agent"
    elif framework:
        if framework == "lighteval":
            function_name = "run_lighteval"
        else:
            function_name = "run_lm_eval"
        eval_tier = "benchmark"
    elif base_model:
        function_name = "run_custom_eval"
        eval_tier = "custom"
    else:
        return json.dumps({"error": "Cannot determine eval type from config"})

    try:
        import modal
        fn = modal.Function.from_name("sofa-genius-eval", function_name)
        call = fn.spawn(config)
        function_call_id = call.object_id

        model_short = config.get("model_name", "model").split("/")[-1]

        card = {
            "card_type": "eval_results_card",
            "title": f"Eval — {model_short}",
            "eval_tier": eval_tier,
            "status": "running",
            "model_name": config.get("model_name", ""),
            "config": config,
            "cost_estimate": None,
            "summary": f"Evaluation job launched on Modal ({function_name}). Results will appear shortly.",
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
                f"Deploy with: modal deploy backend/modal_app/eval_app.py. "
                f"Original error: {error_msg}"
            )
        card = {
            "card_type": "eval_results_card",
            "title": "Eval — Launch Failed",
            "eval_tier": eval_tier,
            "status": "failed",
            "model_name": config.get("model_name", ""),
            "config": config,
            "cost_estimate": None,
            "summary": f"Failed to launch: {error_msg}",
            "modal_function_call_id": None,
            "wandb_url": None,
            "requires_approval": False,
        }
        return json.dumps(card)


# ---------------------------------------------------------------------------
# Tool 7: get_eval_results
# ---------------------------------------------------------------------------
def get_eval_results(
    wandb_project: str = "sofa-genius-eval",
    run_name: str | None = None,
    run_id: str | None = None,
) -> str:
    """Fetch completed eval results from W&B."""
    try:
        import wandb

        api_key = os.environ.get("WANDB_API_KEY", "")
        api = wandb.Api(api_key=api_key) if api_key else wandb.Api()
        entity = api.default_entity

        if run_id:
            run = api.run(f"{entity}/{wandb_project}/{run_id}")
        elif run_name:
            runs = api.runs(
                f"{entity}/{wandb_project}",
                filters={"display_name": run_name},
            )
            if not runs:
                return json.dumps({"error": f"No run found with name '{run_name}'"})
            run = runs[0]
        else:
            # Get the most recent run
            runs = api.runs(f"{entity}/{wandb_project}", per_page=1)
            if not runs:
                return json.dumps({"error": f"No runs found in project '{wandb_project}'"})
            run = runs[0]

        summary = dict(run.summary)
        config = dict(run.config)
        wandb_url = run.url

        # Determine eval tier from run config/name
        eval_suite = config.get("eval_suite")
        framework = config.get("framework")
        base_model = config.get("base_model")

        if eval_suite:
            eval_tier = "agent"
            avg_score = summary.get("avg_score", summary.get("accuracy"))
            task_scores = []
            for key, value in summary.items():
                if key not in ("avg_score", "total_tasks", "eval_suite", "_wandb") and isinstance(value, (int, float)):
                    task_scores.append({
                        "task": key,
                        "score": round(value * 100, 2) if value <= 1 else round(value, 2),
                        "metric": key,
                    })
        elif framework:
            eval_tier = "benchmark"
            avg_score = summary.get("avg_score")
            task_scores = []
            for key, value in summary.items():
                if key.endswith("_acc") or key.endswith("_score"):
                    task_scores.append({
                        "task": key.replace("_acc", "").replace("_score", ""),
                        "score": round(value * 100, 2) if value <= 1 else round(value, 2),
                        "metric": "accuracy",
                    })
        else:
            eval_tier = "custom"
            avg_score = summary.get("lora_avg_score", summary.get("avg_score"))
            task_scores = []

        model_name = config.get("model_name", config.get("lora_model", run.name))
        model_short = model_name.split("/")[-1] if "/" in model_name else model_name

        result_card = {
            "card_type": "eval_results_card",
            "title": f"Eval Results — {model_short}",
            "eval_tier": eval_tier,
            "status": "completed",
            "model_name": model_name,
            "config": config,
            "summary": f"Eval completed: {run.name}. Average score: {avg_score}",
            "avg_score": avg_score,
            "wandb_url": wandb_url,
            "requires_approval": False,
        }

        if eval_tier == "agent":
            result_card["eval_suite"] = eval_suite
            result_card["task_scores"] = task_scores
            result_card["total_tasks"] = summary.get("total_tasks")
        elif eval_tier == "benchmark":
            result_card["benchmark_scores"] = task_scores
            result_card["framework"] = framework
        elif eval_tier == "custom":
            result_card["custom_scores"] = {
                "base_avg_score": summary.get("base_avg_score"),
                "lora_avg_score": summary.get("lora_avg_score"),
                "score_improvement": summary.get("score_improvement"),
                "num_samples": summary.get("num_samples", 0),
            }

        return json.dumps(result_card)

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch results: {str(e)}"})
