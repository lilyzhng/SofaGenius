"""lm-eval-harness benchmark runner.

Runs standard model benchmarks (MMLU, HumanEval, GSM8K, etc.) using
the EleutherAI lm-evaluation-harness framework.
"""

from __future__ import annotations


def lm_eval_impl(config_dict: dict) -> dict:
    """Run standard benchmarks via lm-eval-harness.

    Parameters in config_dict:
        model_name: HuggingFace model path
        benchmarks: List of benchmark names
        backend: "hf", "vllm", or "sglang"
        num_fewshot: Number of few-shot examples (optional)
        limit: Limit samples per benchmark (optional)
        wandb_project: W&B project for logging
    """
    import json
    import lm_eval
    import wandb

    model_name = config_dict["model_name"]
    benchmarks = config_dict.get("benchmarks", ["mmlu"])
    backend = config_dict.get("backend", "hf")
    num_fewshot = config_dict.get("num_fewshot")
    limit = config_dict.get("limit")
    wandb_project = config_dict.get("wandb_project", "sofa-genius-eval")
    experiment_name = config_dict.get("experiment_name", f"bench-{model_name.split('/')[-1]}")

    # Initialize W&B
    run = wandb.init(
        project=wandb_project,
        name=experiment_name,
        config=config_dict,
    )
    wandb_url = run.url
    print(f"W&B run: {wandb_url}")

    # Configure model based on backend
    if backend == "vllm":
        model_type = "vllm"
        model_args = f"pretrained={model_name},tensor_parallel_size=1,gpu_memory_utilization=0.9"
    elif backend == "sglang":
        model_type = "sglang"
        model_args = f"pretrained={model_name}"
    else:
        model_type = "hf"
        model_args = f"pretrained={model_name},dtype=auto,trust_remote_code=True"

    # Run evaluation
    print(f"Running benchmarks: {benchmarks} on {model_name} via {backend}")
    results = lm_eval.simple_evaluate(
        model=model_type,
        model_args=model_args,
        tasks=benchmarks,
        num_fewshot=num_fewshot,
        limit=limit,
        batch_size="auto",
        log_samples=False,
    )

    # Parse results
    benchmark_scores = []
    total_score = 0
    score_count = 0

    for task_name, task_result in results["results"].items():
        # lm-eval-harness returns metrics like "acc,none", "acc_norm,none"
        score = None
        stderr = None
        metric_name = "accuracy"

        for key, value in task_result.items():
            if key.startswith("acc") and not key.endswith("stderr"):
                score = value
                metric_name = key.split(",")[0] if "," in key else key
                stderr_key = f"{key}_stderr" if "," not in key else key.replace(",", "_stderr,")
                stderr = task_result.get(stderr_key)
                break

        if score is not None:
            score_pct = round(score * 100, 2)
            benchmark_scores.append({
                "task": task_name,
                "score": score_pct,
                "stderr": round(stderr * 100, 2) if stderr is not None else None,
                "metric": metric_name,
            })
            total_score += score_pct
            score_count += 1
            wandb.log({f"{task_name}_acc": score})

    avg_score = round(total_score / score_count, 2) if score_count > 0 else 0

    wandb.summary["avg_score"] = avg_score
    wandb.summary["framework"] = "lm_eval_harness"
    wandb.summary["benchmarks"] = benchmarks

    # Save full results to disk
    results_path = f"/results/{experiment_name}_results.json"
    with open(results_path, "w") as f:
        json.dump(results["results"], f, indent=2, default=str)

    wandb.finish()

    return {
        "model_name": model_name,
        "eval_type": "benchmark",
        "framework": "lm_eval_harness",
        "benchmark_scores": benchmark_scores,
        "avg_score": avg_score,
        "wandb_url": wandb_url,
        "run_name": experiment_name,
    }
