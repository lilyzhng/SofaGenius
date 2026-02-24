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


# ---------------------------------------------------------------------------
# Main training entry point
# ---------------------------------------------------------------------------

def run_grpo_ui_training(config_dict: dict) -> dict:
    """Run GRPO training for generative UI. Called from Modal.

    Returns {experiment_name, wandb_url, final_reward, runtime_minutes, hf_repo_url}.
    """
    import os
    from datetime import datetime

    import unsloth  # noqa: F401 — must be first for patches
    import torch  # noqa: F401
    import wandb
    from trl import GRPOConfig, GRPOTrainer
    from unsloth import FastLanguageModel

    # -- Parse config --
    model_name = config_dict.get("model_name", "Qwen/Qwen2.5-Coder-14B")
    dataset_name = config_dict.get("dataset_name", "lilyzhng/uigen-ui-code-gen")
    max_seq_length = config_dict.get("max_seq_length", 4096)
    load_in_4bit = config_dict.get("load_in_4bit", True)
    lora_r = config_dict.get("lora_r", 32)
    lora_alpha = config_dict.get("lora_alpha", lora_r)
    learning_rate = config_dict.get("learning_rate", 5e-6)
    max_steps = config_dict.get("max_steps", -1)
    num_epochs = config_dict.get("num_epochs", 1)
    batch_size = config_dict.get("batch_size", 1)
    gradient_accumulation_steps = config_dict.get("gradient_accumulation_steps", 1)
    num_generations = config_dict.get("num_generations", 4)
    temperature = config_dict.get("temperature", 1.0)
    max_prompt_length = config_dict.get("max_prompt_length", 1024)
    max_completion_length = config_dict.get("max_completion_length", 2048)
    push_to_hub = config_dict.get("push_to_hub", False)
    hf_repo_name = config_dict.get("hf_repo_name")
    wandb_project = config_dict.get("wandb_project", "grpo-ui-gen")
    seed = config_dict.get("seed", 3407)
    train_size = config_dict.get("train_size")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = config_dict.get("experiment_name", f"{model_short}-grpo-ui-r{lora_r}-{timestamp}")
    if not hf_repo_name:
        hf_repo_name = experiment_name

    # -- W&B --
    wandb.init(project=wandb_project, name=experiment_name, config=config_dict)
    wandb_url = wandb.run.url
    print(f"W&B run: {wandb_url}\n")

    # Publish URL immediately
    import modal
    run_urls = modal.Dict.from_name("sofa-genius-run-urls", create_if_missing=True)
    run_urls[experiment_name] = wandb_url

    # -- Load model --
    print(f"Loading model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )

    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ]
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        target_modules=target_modules,
        lora_alpha=lora_alpha,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=seed,
        use_rslora=False,
        loftq_config=None,
    )

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Params: {total_params:,} total, {trainable_params:,} trainable ({100*trainable_params/total_params:.2f}%)")

    # -- Load dataset --
    from backend.modal_app.dataset_utils import should_skip_eval

    skip_eval = should_skip_eval(config_dict)
    print(f"Loading dataset: {dataset_name}")
    dataset, eval_dataset = prepare_ui_dataset(
        dataset_name=dataset_name,
        max_samples=train_size,
        skip_eval=skip_eval,
    )
    print(f"Prepared {len(dataset)} UI GRPO train samples"
          + (f", {len(eval_dataset)} eval samples" if eval_dataset else " (eval skipped)"))

    # -- GRPO config --
    checkpoint_path = f"/checkpoints/{experiment_name}"
    _num_epochs = 1 if max_steps > 0 else num_epochs
    _max_steps = max_steps if max_steps > 0 else -1

    grpo_config = GRPOConfig(
        output_dir=checkpoint_path,
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        num_generations=num_generations,
        temperature=temperature,
        max_prompt_length=max_prompt_length,
        max_completion_length=max_completion_length,
        num_train_epochs=_num_epochs,
        max_steps=_max_steps,
        optim="adamw_8bit",
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        logging_steps=1,
        report_to="wandb",
        save_steps=50,
        save_strategy="steps",
        seed=seed,
    )

    # -- Training --
    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        args=grpo_config,
        train_dataset=dataset,
        reward_funcs=[
            completeness_reward,
            validity_reward,
            interactivity_reward,
            quote_balance_reward,
            length_penalty,
        ],
    )

    print("Starting GRPO UI training...\n")
    trainer_stats = trainer.train()

    # -- Results --
    runtime_seconds = trainer_stats.metrics.get("train_runtime", 0)
    runtime_minutes = round(runtime_seconds / 60, 2)

    final_reward = None
    if trainer.state.log_history:
        for log_entry in reversed(trainer.state.log_history):
            if "reward" in log_entry:
                final_reward = round(log_entry["reward"], 4)
                break

    print(f"Training complete! {runtime_minutes} min, final_reward={final_reward}")

    # -- Quick eval on held-out samples --
    if eval_dataset is not None:
        _run_quick_ui_eval(model, tokenizer, eval_dataset, wandb)

    # -- Push to HuggingFace --
    hf_repo_url = None
    if push_to_hub:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                model.push_to_hub(hf_repo_name, token=hf_token, private=False)
                tokenizer.push_to_hub(hf_repo_name, token=hf_token, private=False)
                hf_repo_url = f"https://huggingface.co/{hf_repo_name}"
                print(f"Pushed to HF: {hf_repo_url}")
            except Exception as e:
                print(f"Warning: HF push failed: {e}")
                model.save_pretrained(f"{checkpoint_path}/final_model")
                tokenizer.save_pretrained(f"{checkpoint_path}/final_model")
        else:
            print("HF_TOKEN not found, saving to volume")
            model.save_pretrained(f"{checkpoint_path}/final_model")
            tokenizer.save_pretrained(f"{checkpoint_path}/final_model")
    else:
        model.save_pretrained(f"{checkpoint_path}/final_model")
        tokenizer.save_pretrained(f"{checkpoint_path}/final_model")

    wandb.finish()

    return {
        "experiment_name": experiment_name,
        "wandb_url": wandb_url,
        "final_reward": final_reward,
        "runtime_minutes": runtime_minutes,
        "hf_repo_url": hf_repo_url,
    }
