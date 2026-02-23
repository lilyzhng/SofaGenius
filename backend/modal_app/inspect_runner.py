"""Inspect AI agent evaluation runner.

Runs agent evaluations using the Inspect AI framework. Supports SWE-bench,
GAIA, GPQA, HumanEval, MBPP, PostTrainBench, and custom agent tasks.
"""

from __future__ import annotations


def agent_eval_impl(config_dict: dict) -> dict:
    """Run agent evaluation via Inspect AI.

    Parameters in config_dict:
        model_name: HuggingFace model path
        eval_suite: Which evaluation suite to run
        agent_type: "model", "external", or "sofagenius"
        limit: Max tasks (optional)
        sandbox: "docker" or "modal"
        wandb_project: W&B project for logging
    """
    import inspect_ai
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log
    import wandb

    model_name = config_dict["model_name"]
    eval_suite = config_dict.get("eval_suite", "swe_bench_verified")
    agent_type = config_dict.get("agent_type", "model")
    limit = config_dict.get("limit")
    wandb_project = config_dict.get("wandb_project", "sofa-genius-eval")
    experiment_name = config_dict.get("experiment_name", f"agent-{eval_suite}")

    # Map eval suite to Inspect task
    SUITE_MAP = {
        "swe_bench_verified": "inspect_evals/swe_bench",
        "gaia": "inspect_evals/gaia",
        "gpqa": "inspect_evals/gpqa",
        "humaneval": "inspect_evals/humaneval",
        "mbpp": "inspect_evals/mbpp",
        # PostTrainBench: custom Inspect task wrapping the PostTrainBench framework
        "posttrain_bench": "backend.evals.posttrain_bench",
    }

    task = SUITE_MAP.get(eval_suite, eval_suite)

    # Initialize W&B
    run = wandb.init(
        project=wandb_project,
        name=experiment_name,
        config=config_dict,
    )
    wandb_url = run.url
    print(f"W&B run: {wandb_url}")

    # Run evaluation
    print(f"Running {eval_suite} evaluation on {model_name} (limit={limit})")
    logs = inspect_eval(
        task,
        model=f"hf/{model_name}",
        limit=limit,
        log_dir="/results/inspect_logs",
    )

    # Parse results from Inspect logs
    log = read_eval_log(logs[0])
    results = log.results

    task_results = {}
    for metric_name, metric_value in results.metrics.items():
        task_results[metric_name] = {
            "score": round(metric_value.value * 100, 2),
            "metric": metric_value.name,
        }
        wandb.log({metric_name: metric_value.value})

    # Per-sample results
    sample_results = []
    for sample in log.samples:
        sample_results.append({
            "id": sample.id,
            "score": sample.score.value if sample.score else 0,
            "turns": len(sample.messages),
            "tool_calls": sum(1 for m in sample.messages if m.role == "tool"),
        })

    avg_score = results.metrics.get("accuracy", results.metrics.get("mean_score"))
    avg_value = round(avg_score.value * 100, 2) if avg_score else 0

    wandb.summary["avg_score"] = avg_value
    wandb.summary["total_tasks"] = len(log.samples)
    wandb.summary["eval_suite"] = eval_suite
    wandb.finish()

    return {
        "model_name": model_name,
        "eval_suite": eval_suite,
        "eval_type": "agent",
        "task_results": task_results,
        "sample_results": sample_results[:50],  # cap for card size
        "avg_score": avg_value,
        "total_tasks": len(log.samples),
        "wandb_url": wandb_url,
        "run_name": experiment_name,
    }
