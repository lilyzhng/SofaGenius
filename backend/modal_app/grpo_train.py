"""GRPO training for tool calling — Hermes function-calling dataset.

Standalone training logic imported by the Modal app (app.py).
Uses GRPOTrainer from trl with 4 reward functions that teach the model
to produce valid, correct, non-hallucinated tool calls.
"""

from __future__ import annotations

import json
import re
from typing import Any


# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------

def _extract_tool_call(text: str) -> dict[str, Any] | None:
    """Extract the first <tool_call>...</tool_call> block and parse its JSON.

    Returns {"name": str, "arguments": dict} or None.
    """
    match = re.search(r"<tool_call>\s*(.*?)\s*</tool_call>", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(1))
        if "name" in parsed and "arguments" in parsed:
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None


# ---------------------------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------------------------

def prepare_hermes_for_grpo(
    dataset_name: str = "NousResearch/hermes-function-calling-v1",
    configs: tuple[str, ...] = ("func_calling_singleturn", "func_calling"),
    max_samples: int | None = None,
    skip_eval: bool = False,
) -> tuple[Any, Any | None]:
    """Load and prepare the Hermes function-calling dataset for GRPO.

    For each row:
    - Build `prompt` from system + human turns
    - Extract ground truth tool call from gpt turn's <tool_call> tags
    - Parse available tool names from the `tools` column

    Returns (train_dataset, eval_dataset | None) with columns
    [prompt, ground_truth, available_tools].
    """
    from datasets import load_dataset, concatenate_datasets

    from backend.modal_app.dataset_utils import (
        DEFAULT_EVAL_FRACTION,
        EVAL_SEED,
        MAX_EVAL,
    )

    all_datasets = []
    for config in configs:
        try:
            ds = load_dataset(dataset_name, config, split="train")
            all_datasets.append(ds)
        except Exception:
            continue

    if not all_datasets:
        raise ValueError(f"Could not load any config from {dataset_name}")

    full_dataset = concatenate_datasets(all_datasets) if len(all_datasets) > 1 else all_datasets[0]

    if skip_eval:
        if max_samples and max_samples < len(full_dataset):
            full_dataset = full_dataset.select(range(max_samples))
        dataset = full_dataset
        eval_raw = None
    else:
        # Split from full data first, then cap training
        splits = full_dataset.train_test_split(
            test_size=DEFAULT_EVAL_FRACTION, seed=EVAL_SEED,
        )
        dataset = splits["train"]
        eval_raw = splits["test"]
        if max_samples and max_samples < len(dataset):
            dataset = dataset.select(range(max_samples))
        desired_eval = max(1, int(len(dataset) * DEFAULT_EVAL_FRACTION))
        eval_cap = min(desired_eval, MAX_EVAL)
        if len(eval_raw) > eval_cap:
            eval_raw = eval_raw.select(range(eval_cap))

    def process_row(example):
        conversations = example.get("conversations", [])
        tools_raw = example.get("tools", "")

        # Build prompt from system + human turns
        prompt_parts = []
        ground_truth = None

        for turn in conversations:
            role = turn.get("from", turn.get("role", ""))
            content = turn.get("value", turn.get("content", ""))

            if role in ("system", "human", "user"):
                prompt_parts.append(content)
            elif role in ("gpt", "assistant"):
                # Extract ground truth tool call
                tc = _extract_tool_call(content)
                if tc and ground_truth is None:
                    ground_truth = json.dumps(tc)

        # Parse available tools from tools column
        available_tools = []
        if tools_raw:
            try:
                tools_list = json.loads(tools_raw) if isinstance(tools_raw, str) else tools_raw
                if isinstance(tools_list, list):
                    for tool in tools_list:
                        if isinstance(tool, dict):
                            name = tool.get("function", {}).get("name") or tool.get("name", "")
                            if name:
                                available_tools.append(name)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "prompt": "\n\n".join(prompt_parts),
            "ground_truth": ground_truth or "",
            "available_tools": json.dumps(available_tools),
        }

    def _process_and_clean(ds):
        ds = ds.map(process_row)
        ds = ds.filter(lambda x: x["ground_truth"] != "")
        keep_cols = {"prompt", "ground_truth", "available_tools"}
        remove_cols = [c for c in ds.column_names if c not in keep_cols]
        if remove_cols:
            ds = ds.remove_columns(remove_cols)
        return ds

    train_dataset = _process_and_clean(dataset)
    eval_dataset = _process_and_clean(eval_raw) if eval_raw is not None else None

    return train_dataset, eval_dataset


# ---------------------------------------------------------------------------
# Reward functions
# ---------------------------------------------------------------------------

def valid_json_reward(completions: list[list[dict]], **kwargs) -> list[float]:
    """Is <tool_call> present with parseable JSON containing 'name' + 'arguments'?

    Score: 0.0 or 1.0
    """
    rewards = []
    for completion_group in completions:
        text = completion_group[0].get("content", "") if completion_group else ""
        tc = _extract_tool_call(text)
        rewards.append(1.0 if tc is not None else 0.0)
    return rewards


def correct_tool_reward(completions: list[list[dict]], ground_truth: list[str] | None = None, **kwargs) -> list[float]:
    """Does the function name match ground truth?

    Score: 0.0 or 1.0
    """
    if not ground_truth:
        return [0.0] * len(completions)

    rewards = []
    for completion_group, gt_json in zip(completions, ground_truth):
        text = completion_group[0].get("content", "") if completion_group else ""
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            gt = json.loads(gt_json)
            rewards.append(1.0 if tc["name"] == gt["name"] else 0.0)
        except (json.JSONDecodeError, KeyError):
            rewards.append(0.0)
    return rewards


def correct_params_reward(completions: list[list[dict]], ground_truth: list[str] | None = None, **kwargs) -> list[float]:
    """Per-parameter overlap with ground truth arguments.

    Score: 0.0 to 1.0 (graduated — fraction of params present with correct value).
    """
    if not ground_truth:
        return [0.0] * len(completions)

    rewards = []
    for completion_group, gt_json in zip(completions, ground_truth):
        text = completion_group[0].get("content", "") if completion_group else ""
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            gt = json.loads(gt_json)
            gt_args = gt.get("arguments", {})
            pred_args = tc.get("arguments", {})
            if not gt_args:
                # No arguments expected — reward if prediction also has none
                rewards.append(1.0 if not pred_args else 0.5)
                continue
            correct = 0
            for key, val in gt_args.items():
                if key in pred_args and str(pred_args[key]) == str(val):
                    correct += 1
            rewards.append(correct / len(gt_args))
        except (json.JSONDecodeError, KeyError):
            rewards.append(0.0)
    return rewards


def no_hallucination_reward(completions: list[list[dict]], available_tools: list[str] | None = None, **kwargs) -> list[float]:
    """Does the called tool exist in the available set?

    Score: -2.0 (hallucinated tool), 0.0 (no tool call), 1.0 (valid tool).
    """
    if not available_tools:
        return [0.0] * len(completions)

    rewards = []
    for completion_group, tools_json in zip(completions, available_tools):
        text = completion_group[0].get("content", "") if completion_group else ""
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            tool_list = json.loads(tools_json) if isinstance(tools_json, str) else tools_json
            if tc["name"] in tool_list:
                rewards.append(1.0)
            else:
                rewards.append(-2.0)  # Heavy penalty for hallucinated tools
        except (json.JSONDecodeError, TypeError):
            rewards.append(0.0)
    return rewards


# ---------------------------------------------------------------------------
# Quick evaluation (runs at end of training)
# ---------------------------------------------------------------------------

def _run_quick_eval(model, tokenizer, eval_dataset, wandb_module):
    """Run on held-out eval examples and log metrics to W&B.

    Parameters
    ----------
    eval_dataset : Dataset
        Pre-split eval dataset (never seen during training).
    """
    from unsloth import FastLanguageModel

    print(f"\nRunning quick eval on {len(eval_dataset)} held-out examples...")
    try:
        if len(eval_dataset) == 0:
            print("No eval samples available, skipping eval")
            return

        FastLanguageModel.for_inference(model)

        valid_json_count = 0
        correct_tool_count = 0
        correct_params_total = 0.0
        no_hallucination_count = 0
        overall_pass_count = 0
        total = len(eval_dataset)

        for i, sample in enumerate(eval_dataset):
            prompt = sample["prompt"]
            gt_json = sample["ground_truth"]
            tools_json = sample["available_tools"]

            inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to("cuda")
            outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7, do_sample=True)
            response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

            tc = _extract_tool_call(response)

            # Score
            is_valid = tc is not None
            if is_valid:
                valid_json_count += 1

            is_correct_tool = False
            is_correct_params = False
            is_no_hallucination = False

            if tc:
                try:
                    gt = json.loads(gt_json)
                    is_correct_tool = tc["name"] == gt["name"]
                except (json.JSONDecodeError, KeyError):
                    pass

                try:
                    gt = json.loads(gt_json)
                    gt_args = gt.get("arguments", {})
                    pred_args = tc.get("arguments", {})
                    if not gt_args:
                        is_correct_params = not pred_args
                    else:
                        correct = sum(1 for k, v in gt_args.items() if k in pred_args and str(pred_args[k]) == str(v))
                        is_correct_params = correct == len(gt_args)
                except (json.JSONDecodeError, KeyError):
                    pass

                try:
                    tool_list = json.loads(tools_json)
                    is_no_hallucination = tc["name"] in tool_list
                except (json.JSONDecodeError, TypeError):
                    pass

            if is_correct_tool:
                correct_tool_count += 1
            if is_correct_params:
                correct_params_total += 1
            if is_no_hallucination:
                no_hallucination_count += 1
            if is_valid and is_correct_tool and is_correct_params and is_no_hallucination:
                overall_pass_count += 1

        # Log to W&B
        wandb_module.log({
            "eval/valid_json_rate": valid_json_count / total,
            "eval/correct_tool_rate": correct_tool_count / total,
            "eval/correct_params_rate": correct_params_total / total,
            "eval/no_hallucination_rate": no_hallucination_count / total,
            "eval/overall_pass_rate": overall_pass_count / total,
        })
        print(f"Eval results: valid_json={valid_json_count}/{total}, "
              f"correct_tool={correct_tool_count}/{total}, "
              f"correct_params={correct_params_total:.0f}/{total}, "
              f"no_hallucination={no_hallucination_count}/{total}, "
              f"overall_pass={overall_pass_count}/{total}")

    except Exception as e:
        print(f"Quick eval failed (non-fatal): {e}")
