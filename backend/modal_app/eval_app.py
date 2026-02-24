"""
Sofa Genius Evaluation Modal App — separate app for all evaluation workloads.

Deploy once:
    modal deploy backend/modal_app/eval_app.py

Then Sofa Genius can launch eval jobs via:
    modal.Function.from_name("sofa-genius-eval", "run_agent_eval").spawn(config)
    modal.Function.from_name("sofa-genius-eval", "run_lm_eval").spawn(config)
    modal.Function.from_name("sofa-genius-eval", "run_lighteval").spawn(config)
    modal.Function.from_name("sofa-genius-eval", "run_custom_eval").spawn(config)
"""

from __future__ import annotations

import modal

# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------
app = modal.App("sofa-genius-eval")

# ---------------------------------------------------------------------------
# Images — separate images for each eval tier to avoid dependency conflicts
# ---------------------------------------------------------------------------

# Image for Inspect AI agent evaluations
inspect_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "inspect-ai",
        "inspect-evals",
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# Image for lm-eval-harness benchmarks
lm_eval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "lm-eval[all]",
        "accelerate",
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# Image for lighteval benchmarks
lighteval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "lighteval[accelerate,extended_tasks]",
        "wandb",
        "hf-transfer",
    )
    .env({"HF_HOME": "/model_cache"})
)

# Image for custom visual eval (Playwright + VLM judge)
custom_eval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "unsloth[cu128-torch270]",
        "datasets",
        "hf-transfer",
        "wandb",
        "openai",
        "playwright",
    )
    .run_commands("playwright install --with-deps chromium")
    .env({
        "HF_HOME": "/model_cache",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    })
)

# ---------------------------------------------------------------------------
# Persistent volumes
# ---------------------------------------------------------------------------
model_cache_vol = modal.Volume.from_name("sofa-genius-model-cache", create_if_missing=True)
results_vol = modal.Volume.from_name("sofa-genius-eval-results", create_if_missing=True)

# Shared key-value store for passing W&B run URLs
run_urls = modal.Dict.from_name("sofa-genius-run-urls", create_if_missing=True)

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
AGENT_EVAL_TIMEOUT_HOURS = 24  # SWE-bench can take a long time
BENCHMARK_TIMEOUT_HOURS = 12
CUSTOM_EVAL_TIMEOUT_HOURS = 4


# ---------------------------------------------------------------------------
# Agent evaluation via Inspect AI
# ---------------------------------------------------------------------------
@app.function(
    image=inspect_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/results": results_vol,
    },
    secrets=[
        modal.Secret.from_name("wandb-secret"),
        modal.Secret.from_name("hf-secret"),
    ],
    timeout=AGENT_EVAL_TIMEOUT_HOURS * 60 * 60,
)
def run_agent_eval(config_dict: dict) -> dict:
    """Run agent evaluation via Inspect AI."""
    from backend.modal_app.inspect_runner import agent_eval_impl

    result = agent_eval_impl(config_dict)

    # Publish W&B URL for frontend polling
    experiment_name = config_dict.get("experiment_name", "")
    if experiment_name and result.get("wandb_url"):
        run_urls[experiment_name] = result["wandb_url"]

    results_vol.commit()
    return result


# ---------------------------------------------------------------------------
# Standard benchmarks via lm-eval-harness
# ---------------------------------------------------------------------------
@app.function(
    image=lm_eval_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/results": results_vol,
    },
    secrets=[
        modal.Secret.from_name("wandb-secret"),
        modal.Secret.from_name("hf-secret"),
    ],
    timeout=BENCHMARK_TIMEOUT_HOURS * 60 * 60,
)
def run_lm_eval(config_dict: dict) -> dict:
    """Run standard benchmarks via lm-eval-harness."""
    from backend.modal_app.benchmark_eval import lm_eval_impl

    result = lm_eval_impl(config_dict)

    experiment_name = config_dict.get("experiment_name", "")
    if experiment_name and result.get("wandb_url"):
        run_urls[experiment_name] = result["wandb_url"]

    results_vol.commit()
    return result


# ---------------------------------------------------------------------------
# Benchmarks via HuggingFace lighteval
# ---------------------------------------------------------------------------
@app.function(
    image=lighteval_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/results": results_vol,
    },
    secrets=[
        modal.Secret.from_name("wandb-secret"),
        modal.Secret.from_name("hf-secret"),
    ],
    timeout=BENCHMARK_TIMEOUT_HOURS * 60 * 60,
)
def run_lighteval(config_dict: dict) -> dict:
    """Run benchmarks via HuggingFace lighteval."""
    from backend.modal_app.lighteval_runner import lighteval_impl

    result = lighteval_impl(config_dict)

    experiment_name = config_dict.get("experiment_name", "")
    if experiment_name and result.get("wandb_url"):
        run_urls[experiment_name] = result["wandb_url"]

    results_vol.commit()
    return result


# ---------------------------------------------------------------------------
# Custom visual evaluation (Playwright + VLM judge)
# ---------------------------------------------------------------------------
@app.function(
    image=custom_eval_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/results": results_vol,
    },
    secrets=[
        modal.Secret.from_name("wandb-secret"),
        modal.Secret.from_name("hf-secret"),
        modal.Secret.from_name("openrouter-secret"),
    ],
    timeout=CUSTOM_EVAL_TIMEOUT_HOURS * 60 * 60,
)
def run_custom_eval(config_dict: dict) -> dict:
    """Run visual rendering eval (Playwright + VLM judge)."""
    from backend.modal_app.eval import eval_impl

    result = eval_impl(config_dict)

    experiment_name = config_dict.get("experiment_name", "")
    if experiment_name and result.get("wandb_url"):
        run_urls[experiment_name] = result["wandb_url"]

    results_vol.commit()
    return result
