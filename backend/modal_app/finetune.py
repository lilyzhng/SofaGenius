"""Fine-tuning implementation for Sofa Genius Modal app.

Adapted from Qwen3-Coder/unsloth/modal_coder_base.py — same Unsloth + SFTTrainer
logic, but accepts a plain dict config and returns a result dict.
"""

from __future__ import annotations

from datetime import datetime


def finetune_impl(config_dict: dict) -> dict:
    """Run QLoRA fine-tuning with Unsloth. Returns result dict."""
    import os
    import json

    import unsloth  # noqa: F401 — must be first for patches
    import torch
    import wandb
    from datasets import Dataset, load_dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    # ---------------------------------------------------------------------------
    # Parse config with defaults
    # ---------------------------------------------------------------------------
    model_name = config_dict.get("model_name", "Qwen/Qwen2.5-Coder-14B")
    dataset_name = config_dict.get("dataset_name", "")
    max_seq_length = config_dict.get("max_seq_length", 4096)
    load_in_4bit = config_dict.get("load_in_4bit", True)
    lora_r = config_dict.get("lora_r", 32)
    lora_alpha = config_dict.get("lora_alpha", lora_r)
    learning_rate = config_dict.get("learning_rate", 2e-4)
    num_epochs = config_dict.get("num_epochs", 1)
    max_steps = config_dict.get("max_steps", -1)
    batch_size = config_dict.get("batch_size", 1)
    gradient_accumulation_steps = config_dict.get("gradient_accumulation_steps", 8)
    gpu_type = config_dict.get("gpu_type", "A100")
    push_to_hub = config_dict.get("push_to_hub", True)
    hf_repo_name = config_dict.get("hf_repo_name")
    wandb_project = config_dict.get("wandb_project", "qwen-coder-code-gen")
    warmup_steps = config_dict.get("warmup_steps", 10)
    weight_decay = config_dict.get("weight_decay", 0.01)
    seed = config_dict.get("seed", 3407)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = config_dict.get("experiment_name", f"{model_short}-r{lora_r}-{timestamp}")
    if not hf_repo_name:
        hf_repo_name = experiment_name

    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ]

    # ---------------------------------------------------------------------------
    # W&B init
    # ---------------------------------------------------------------------------
    wandb.init(
        project=wandb_project,
        name=experiment_name,
        config=config_dict,
    )
    wandb_url = wandb.run.url
    print(f"W&B run: {wandb_url}\n")

    # ---------------------------------------------------------------------------
    # Load model
    # ---------------------------------------------------------------------------
    print(f"Loading BASE model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )

    # ---------------------------------------------------------------------------
    # LoRA
    # ---------------------------------------------------------------------------
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
    print(f"Total params: {total_params:,}, Trainable: {trainable_params:,} ({100*trainable_params/total_params:.2f}%)")

    # ---------------------------------------------------------------------------
    # Load data
    # ---------------------------------------------------------------------------
    if not dataset_name:
        raise ValueError("dataset_name is required")

    print(f"Loading HuggingFace dataset: {dataset_name}")
    train_size = config_dict.get("train_size")
    if train_size:
        dataset = load_dataset(dataset_name, split=f"train[:{train_size}]")
    else:
        dataset = load_dataset(dataset_name, split="train")

    print(f"Loaded {len(dataset)} samples")

    # If dataset already has 'text' field, use as-is
    if "text" not in dataset.column_names:
        def formatting_prompts_func(examples):
            texts = []
            if "conversations" in examples:
                for conversation in examples["conversations"]:
                    text = ""
                    for msg in conversation:
                        text += f"{msg.get('content', msg.get('value', ''))}\n\n"
                    texts.append(text)
            elif "messages" in examples:
                for msgs in examples["messages"]:
                    text = ""
                    for msg in msgs:
                        if msg["role"] == "user":
                            text += f"# Task: {msg['content']}\n\n"
                        elif msg["role"] == "assistant":
                            text += msg["content"]
                    texts.append(text)
            else:
                first_key = list(examples.keys())[0]
                texts = [str(item) for item in examples[first_key]]
            return {"text": texts}

        dataset = dataset.map(formatting_prompts_func, batched=True)

    # ---------------------------------------------------------------------------
    # Training
    # ---------------------------------------------------------------------------
    checkpoint_path = f"/checkpoints/{experiment_name}"

    if max_steps > 0:
        _num_epochs = 1
        _max_steps = max_steps
    else:
        _num_epochs = num_epochs
        _max_steps = -1

    training_args = SFTConfig(
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        warmup_steps=warmup_steps,
        num_train_epochs=_num_epochs,
        max_steps=_max_steps,
        learning_rate=learning_rate,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=weight_decay,
        lr_scheduler_type="cosine",
        seed=seed,
        output_dir=checkpoint_path,
        report_to="wandb",
        save_steps=50,
        save_strategy="steps",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,
        args=training_args,
    )

    print("Starting training...\n")
    trainer_stats = trainer.train()

    # ---------------------------------------------------------------------------
    # Results
    # ---------------------------------------------------------------------------
    runtime_seconds = trainer_stats.metrics["train_runtime"]
    runtime_minutes = round(runtime_seconds / 60, 2)

    final_loss = None
    if trainer.state.log_history:
        for log in reversed(trainer.state.log_history):
            if "loss" in log:
                final_loss = round(log["loss"], 4)
                break

    print(f"Training complete! Time: {runtime_minutes} min, Final loss: {final_loss}")

    # ---------------------------------------------------------------------------
    # Push to HuggingFace
    # ---------------------------------------------------------------------------
    hf_repo_url = None
    if push_to_hub:
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                model.push_to_hub(hf_repo_name, token=hf_token, private=False)
                tokenizer.push_to_hub(hf_repo_name, token=hf_token, private=False)
                hf_repo_url = f"https://huggingface.co/{hf_repo_name}"
                print(f"Pushed to HuggingFace: {hf_repo_url}")
            except Exception as e:
                print(f"Warning: Failed to push to HF: {e}")
                # Save locally as fallback
                final_path = f"{checkpoint_path}/final_model"
                model.save_pretrained(final_path)
                tokenizer.save_pretrained(final_path)
        else:
            print("HF_TOKEN not found, saving to Modal volume")
            final_path = f"{checkpoint_path}/final_model"
            model.save_pretrained(final_path)
            tokenizer.save_pretrained(final_path)
    else:
        final_path = f"{checkpoint_path}/final_model"
        model.save_pretrained(final_path)
        tokenizer.save_pretrained(final_path)

    wandb.finish()

    return {
        "experiment_name": experiment_name,
        "wandb_url": wandb_url,
        "final_loss": final_loss,
        "runtime_minutes": runtime_minutes,
        "hf_repo_url": hf_repo_url,
    }
