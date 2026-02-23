"""HuggingFace lighteval benchmark runner.

Runs model benchmarks using the lighteval framework, with support for
HF Hub integration, community benchmarks, and vLLM acceleration.
"""

from __future__ import annotations


def lighteval_impl(config_dict: dict) -> dict:
    """Run benchmarks via HuggingFace lighteval.

    Parameters in config_dict:
        model_name: HuggingFace model path
        benchmarks: List of benchmark names
        backend: "accelerate", "vllm", or "nanotron"
        num_fewshot: Number of few-shot examples (optional)
        limit: Limit samples per benchmark (optional)
        wandb_project: W&B project for logging
    """
    import json
    import wandb

    model_name = config_dict["model_name"]
    benchmarks = config_dict.get("benchmarks", ["mmlu"])
    backend = config_dict.get("backend", "hf")
    num_fewshot = config_dict.get("num_fewshot")
    limit = config_dict.get("limit")
    wandb_project = config_dict.get("wandb_project", "sofa-genius-eval")
    experiment_name = config_dict.get("experiment_name", f"lighteval-{model_name.split('/')[-1]}")

    # Initialize W&B
    run = wandb.init(
        project=wandb_project,
        name=experiment_name,
        config=config_dict,
    )
    wandb_url = run.url
    print(f"W&B run: {wandb_url}")

    # Map backend names
    lighteval_backend = "vllm" if backend == "vllm" else "accelerate"

    # Build task string for lighteval
    # lighteval tasks format: "leaderboard|task_name|num_fewshot"
    task_list = []
    for bench in benchmarks:
        fewshot = num_fewshot if num_fewshot is not None else _default_fewshot(bench)
        task_list.append(f"leaderboard|{bench}|{fewshot}")
    tasks_str = ",".join(task_list)

    # Run evaluation using lighteval Python API
    print(f"Running lighteval: {benchmarks} on {model_name} via {lighteval_backend}")

    from lighteval.main_accelerate import main as accelerate_main
    from lighteval.parsers import make_parser

    # Build args for lighteval
    args = [
        "--model_args", f"pretrained={model_name},dtype=auto,trust_remote_code=True",
        "--tasks", tasks_str,
        "--output_dir", f"/results/{experiment_name}",
    ]
    if limit:
        args.extend(["--max_samples", str(limit)])

    parser = make_parser()
    parsed_args = parser.parse_args(args)
    results = accelerate_main(parsed_args)

    # Parse results
    benchmark_scores = []
    total_score = 0
    score_count = 0

    if isinstance(results, dict):
        for task_name, task_result in results.items():
            if isinstance(task_result, dict):
                score = task_result.get("acc", task_result.get("accuracy"))
                if score is not None:
                    score_pct = round(score * 100, 2) if score <= 1 else round(score, 2)
                    benchmark_scores.append({
                        "task": task_name,
                        "score": score_pct,
                        "metric": "accuracy",
                    })
                    total_score += score_pct
                    score_count += 1
                    wandb.log({f"{task_name}_acc": score})

    avg_score = round(total_score / score_count, 2) if score_count > 0 else 0

    wandb.summary["avg_score"] = avg_score
    wandb.summary["framework"] = "lighteval"
    wandb.summary["benchmarks"] = benchmarks

    # Save results
    results_path = f"/results/{experiment_name}_results.json"
    with open(results_path, "w") as f:
        json.dump(results if isinstance(results, dict) else {}, f, indent=2, default=str)

    wandb.finish()

    return {
        "model_name": model_name,
        "eval_type": "benchmark",
        "framework": "lighteval",
        "benchmark_scores": benchmark_scores,
        "avg_score": avg_score,
        "wandb_url": wandb_url,
        "run_name": experiment_name,
    }


def _default_fewshot(benchmark: str) -> int:
    """Default few-shot count by benchmark (matches Open LLM Leaderboard)."""
    defaults = {
        "mmlu": 5,
        "hellaswag": 10,
        "arc_easy": 25,
        "arc_challenge": 25,
        "humaneval": 0,
        "gsm8k": 5,
        "winogrande": 5,
        "truthfulqa": 0,
    }
    return defaults.get(benchmark, 0)
