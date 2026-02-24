"""GRPO training for generative UI — React code generation.

Standalone training logic imported by the Modal app (app.py).
Uses GRPOTrainer with 5 reward functions adapted from the Tinker blog
that teach the model to produce complete, valid, interactive React/UI components.
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------------

def prepare_ui_dataset(
    dataset_name: str = "lilyzhng/uigen-ui-code-gen",
    max_samples: int | None = None,
    skip_eval: bool = False,
) -> tuple[Any, Any | None]:
    """Load and prepare a UI code generation dataset for GRPO.

    Returns (train_dataset, eval_dataset | None) with column [prompt].
    """
    from backend.modal_app.dataset_utils import load_train_eval_split

    train_ds, eval_ds = load_train_eval_split(
        dataset_name=dataset_name,
        max_train_samples=max_samples,
        skip_eval=skip_eval,
    )

    def process_row(example):
        text = example.get("text", "")
        # Extract the requirements/task from the text
        prompt = ""
        for line in text.split("\n"):
            if line.startswith("# Task:") or line.startswith("# Requirements:"):
                prompt = line.replace("# Task:", "").replace("# Requirements:", "").strip()
                break
        if not prompt:
            # Fallback: use first non-empty line
            for line in text.split("\n"):
                if line.strip():
                    prompt = line.strip()
                    break
        return {"prompt": f"Generate a React component with Tailwind CSS for: {prompt}"}

    def _process_and_clean(ds):
        ds = ds.map(process_row)
        keep_cols = {"prompt"}
        remove_cols = [c for c in ds.column_names if c not in keep_cols]
        if remove_cols:
            ds = ds.remove_columns(remove_cols)
        return ds

    train_dataset = _process_and_clean(train_ds)
    eval_dataset = _process_and_clean(eval_ds) if eval_ds is not None else None

    return train_dataset, eval_dataset


# ---------------------------------------------------------------------------
# Reward functions (adapted from Tinker blog)
# ---------------------------------------------------------------------------

def completeness_reward(completions: list[list[dict]], **kwargs) -> list[float]:
    """Reward complete code, heavily penalize truncated output.

    +7.5 for complete code (ends with proper closing tags).
    -15.0 for truncated code (no closing tags found).
    """
    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""
        text = text.strip()

        # Check for proper closing indicators
        has_closing = any([
            text.endswith("/>"),
            text.endswith(");"),
            text.endswith("</div>"),
            text.endswith("</main>"),
            text.endswith("</section>"),
            text.endswith("}"),
            "export default" in text,
            text.rstrip().endswith("```"),
        ])

        rewards.append(7.5 if has_closing else -15.0)
    return rewards


def validity_reward(completions: list[list[dict]], **kwargs) -> list[float]:
    """Check that braces, brackets, and parentheses are balanced.

    Score: 0.0 to 3.0 (1 point per balanced pair type).
    """
    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""

        score = 0.0
        # Check braces {}
        if text.count("{") == text.count("}"):
            score += 1.0
        # Check brackets []
        if text.count("[") == text.count("]"):
            score += 1.0
        # Check parentheses ()
        if text.count("(") == text.count(")"):
            score += 1.0

        rewards.append(score)
    return rewards


def interactivity_reward(completions: list[list[dict]], **kwargs) -> list[float]:
    """Reward React interactivity patterns: hooks and event handlers.

    Score: 0.0 to 5.0 (1 point per interactivity pattern found).
    """
    patterns = [
        r"useState",
        r"useEffect",
        r"onClick",
        r"onChange",
        r"onSubmit|onKeyDown|onKeyPress|onFocus|onBlur",
    ]

    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""

        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text):
                score += 1.0

        rewards.append(score)
    return rewards


def quote_balance_reward(completions: list[list[dict]], **kwargs) -> list[float]:
    """Check that quotes are balanced (single and double).

    Score: 0.0 to 2.0 (1 point per balanced quote type).
    """
    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""

        score = 0.0
        # Count quotes outside of escaped sequences
        double_quotes = len(re.findall(r'(?<!\\)"', text))
        single_quotes = len(re.findall(r"(?<!\\)'", text))

        # Template literals (backticks)
        backticks = text.count("`")

        if double_quotes % 2 == 0:
            score += 1.0
        if single_quotes % 2 == 0 and backticks % 2 == 0:
            score += 1.0

        rewards.append(score)
    return rewards


def length_penalty(completions: list[list[dict]], **kwargs) -> list[float]:
    """Penalize extremely short or long outputs.

    Score: -5.0 for too short (<50 chars), -2.0 for too long (>8000 chars), 0.0 otherwise.
    """
    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""

        length = len(text)
        if length < 50:
            rewards.append(-5.0)
        elif length > 8000:
            rewards.append(-2.0)
        else:
            rewards.append(0.0)

    return rewards


# ---------------------------------------------------------------------------
# Quick eval (runs at end of training)
# ---------------------------------------------------------------------------

def _run_quick_ui_eval(model, tokenizer, eval_dataset, wandb_module):
    """Run held-out eval and log UI-specific metrics to W&B.

    Generates completions on eval prompts and scores with the 5 reward functions.
    """
    from unsloth import FastLanguageModel

    print(f"\nRunning quick UI eval on {len(eval_dataset)} held-out examples...")
    try:
        if len(eval_dataset) == 0:
            print("No eval samples available, skipping eval")
            return

        FastLanguageModel.for_inference(model)

        completeness_scores = []
        validity_scores = []
        interactivity_scores = []
        quote_scores = []
        length_scores = []
        total = len(eval_dataset)

        for i, sample in enumerate(eval_dataset):
            prompt = sample["prompt"]
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
            outputs = model.generate(**inputs, max_new_tokens=2048, temperature=0.7, do_sample=True)
            response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

            comp = [[{"content": response}]]
            completeness_scores.extend(completeness_reward(comp))
            validity_scores.extend(validity_reward(comp))
            interactivity_scores.extend(interactivity_reward(comp))
            quote_scores.extend(quote_balance_reward(comp))
            length_scores.extend(length_penalty(comp))

        wandb_module.log({
            "eval/completeness_avg": sum(completeness_scores) / total,
            "eval/validity_avg": sum(validity_scores) / total,
            "eval/interactivity_avg": sum(interactivity_scores) / total,
            "eval/quote_balance_avg": sum(quote_scores) / total,
            "eval/length_penalty_avg": sum(length_scores) / total,
            "eval/total_reward_avg": (
                sum(completeness_scores) + sum(validity_scores)
                + sum(interactivity_scores) + sum(quote_scores)
                + sum(length_scores)
            ) / total,
        })
        print(f"UI Eval results: completeness={sum(completeness_scores)/total:.2f}, "
              f"validity={sum(validity_scores)/total:.2f}, "
              f"interactivity={sum(interactivity_scores)/total:.2f}, "
              f"quote_balance={sum(quote_scores)/total:.2f}, "
              f"length_penalty={sum(length_scores)/total:.2f}")

    except Exception as e:
        print(f"Quick UI eval failed (non-fatal): {e}")


