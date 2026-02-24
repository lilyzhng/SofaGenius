"""
Sofa Genius Modal App — deployable fine-tuning and evaluation functions.

Deploy once:
    modal deploy backend/modal_app/app.py

Then Sofa Genius can launch jobs via:
    modal.Function.from_name("sofa-genius-launcher", "run_finetune").spawn(config)
    modal.Function.from_name("sofa-genius-launcher", "run_evaluation").spawn(config)
"""

from __future__ import annotations

import modal

# ---------------------------------------------------------------------------
# App definition
# ---------------------------------------------------------------------------
app = modal.App("sofa-genius-launcher")

# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------
train_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "unsloth[cu128-torch270]",
        "datasets",
        "hf-transfer",
        "wandb",
        "trl>=0.22.0",
    )
    .env({
        "HF_HOME": "/model_cache",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    })
)

eval_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "unsloth[cu128-torch270]",
        "datasets",
        "hf-transfer",
        "wandb",
        "openai",
        "python-dotenv",
        "playwright",
    )
    .run_commands("playwright install --with-deps chromium")
    .env({
        "HF_HOME": "/model_cache",
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
    })
)

# ---------------------------------------------------------------------------
# Persistent volumes (prefixed sofa-genius-)
# ---------------------------------------------------------------------------
model_cache_vol = modal.Volume.from_name("sofa-genius-model-cache", create_if_missing=True)
checkpoint_vol = modal.Volume.from_name("sofa-genius-checkpoints", create_if_missing=True)
results_vol = modal.Volume.from_name("sofa-genius-eval-results", create_if_missing=True)

# Shared key-value store for passing W&B run URLs from Modal to the backend
run_urls = modal.Dict.from_name("sofa-genius-run-urls", create_if_missing=True)

# ---------------------------------------------------------------------------
# Fine-tuning function
# ---------------------------------------------------------------------------
FINETUNE_TIMEOUT_HOURS = 6


@app.function(
    image=train_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/checkpoints": checkpoint_vol,
    },
    secrets=[modal.Secret.from_name("wandb-secret"), modal.Secret.from_name("hf-secret")],
    timeout=FINETUNE_TIMEOUT_HOURS * 60 * 60,
)
def run_finetune(config_dict: dict) -> dict:
    """Run QLoRA fine-tuning with Unsloth. Accepts a plain dict config.

    Adapted from Qwen3-Coder/unsloth/modal_coder_base.py.
    """
    import os
    from datetime import datetime

    import unsloth  # noqa: F401 — must be first for patches
    import torch  # noqa: F401
    import wandb
    from datasets import get_dataset_split_names, load_dataset
    from trl import SFTConfig, SFTTrainer
    from unsloth import FastLanguageModel

    # -- Parse config with defaults --
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

    # -- W&B --
    wandb.init(project=wandb_project, name=experiment_name, config=config_dict)
    wandb_url = wandb.run.url
    print(f"W&B run: {wandb_url}\n")

    # Publish URL immediately so the frontend can show it while training
    run_urls[experiment_name] = wandb_url

    # -- Load model --
    print(f"Loading BASE model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )
    model_cache_vol.commit()

    # -- LoRA --
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

    # -- Load data with train/eval split --
    if not dataset_name:
        raise ValueError("dataset_name is required")
    print(f"Loading dataset: {dataset_name}")
    train_size = config_dict.get("train_size")

    # Determine if we should skip eval (overfit mode)
    skip_eval = (max_steps == 1) or (train_size is not None and train_size <= 4)

    full_dataset = load_dataset(dataset_name, split="train")

    eval_dataset = None
    if skip_eval:
        if train_size and train_size < len(full_dataset):
            full_dataset = full_dataset.select(range(train_size))
        dataset = full_dataset
    else:
        try:
            split_names = get_dataset_split_names(dataset_name)
            if "test" in split_names:
                eval_dataset = load_dataset(dataset_name, split="test")
        except Exception:
            pass
        if eval_dataset is not None:
            dataset = full_dataset
            if train_size and train_size < len(dataset):
                dataset = dataset.select(range(train_size))
        else:
            splits = full_dataset.train_test_split(test_size=0.1, seed=42)
            dataset = splits["train"]
            eval_dataset = splits["test"]
            if train_size and train_size < len(dataset):
                dataset = dataset.select(range(train_size))
        # Scale eval to 10% of training size, capped at 200
        desired_eval = max(1, int(len(dataset) * 0.1))
        eval_cap = min(desired_eval, 200)
        if len(eval_dataset) > eval_cap:
            eval_dataset = eval_dataset.select(range(eval_cap))

    print(f"Loaded {len(dataset)} train samples"
          + (f", {len(eval_dataset)} eval samples" if eval_dataset else " (eval skipped)"))

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

    if "text" not in dataset.column_names:
        dataset = dataset.map(formatting_prompts_func, batched=True)
    if eval_dataset is not None and "text" not in eval_dataset.column_names:
        eval_dataset = eval_dataset.map(formatting_prompts_func, batched=True)

    # -- Training --
    checkpoint_path = f"/checkpoints/{experiment_name}"
    _num_epochs = 1 if max_steps > 0 else num_epochs
    _max_steps = max_steps if max_steps > 0 else -1

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
        **({"eval_strategy": "steps", "eval_steps": 50} if eval_dataset else {}),
    )
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,
        args=training_args,
    )
    print("Starting training...\n")
    trainer_stats = trainer.train()

    # -- Results --
    runtime_seconds = trainer_stats.metrics["train_runtime"]
    runtime_minutes = round(runtime_seconds / 60, 2)
    final_loss = None
    if trainer.state.log_history:
        for log in reversed(trainer.state.log_history):
            if "loss" in log:
                final_loss = round(log["loss"], 4)
                break
    print(f"Training complete! {runtime_minutes} min, loss={final_loss}")

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
            print("HF_TOKEN not found, saving to Modal volume")
            model.save_pretrained(f"{checkpoint_path}/final_model")
            tokenizer.save_pretrained(f"{checkpoint_path}/final_model")
    else:
        model.save_pretrained(f"{checkpoint_path}/final_model")
        tokenizer.save_pretrained(f"{checkpoint_path}/final_model")

    checkpoint_vol.commit()
    wandb.finish()

    return {
        "experiment_name": experiment_name,
        "wandb_url": wandb_url,
        "final_loss": final_loss,
        "runtime_minutes": runtime_minutes,
        "hf_repo_url": hf_repo_url,
    }


# ---------------------------------------------------------------------------
# Evaluation function
# ---------------------------------------------------------------------------
EVAL_TIMEOUT_HOURS = 2


@app.function(
    image=eval_image,
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
    timeout=EVAL_TIMEOUT_HOURS * 60 * 60,
)
def run_evaluation(config_dict: dict) -> dict:
    """Run side-by-side evaluation comparing base vs fine-tuned model.

    Adapted from Qwen3-Coder/unsloth/modal_eval.py.
    """
    import os
    import json
    import time
    import base64
    import re

    os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"

    import unsloth  # noqa: F401 — must be first for patches
    import wandb
    from openai import OpenAI
    from playwright.sync_api import sync_playwright
    from unsloth import FastLanguageModel
    from transformers import AutoTokenizer

    # -- Parse config --
    base_model_name = config_dict.get("base_model", "Qwen/Qwen2.5-Coder-14B")
    lora_model_name = config_dict.get("lora_model", "")
    hf_dataset = config_dict.get("hf_dataset", "lilyzhng/uigen-ui-code-gen")
    limit = config_dict.get("limit", 20)
    use_judge = config_dict.get("use_judge", True)
    judge_model = config_dict.get("judge_model", "google/gemini-3-pro-preview")
    wandb_project = config_dict.get("wandb_project", "uiux-eval")

    if not lora_model_name:
        raise ValueError("lora_model is required")

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    HTML_TEMPLATE = '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <script src="https://cdn.tailwindcss.com"></script>\n  <title>{title}</title>\n</head>\n<body>\n{content}\n</body>\n</html>'
    PROMPT_TEMPLATE = "# Task: Generate HTML/CSS code using Tailwind CSS\n# Requirements: {requirements}\n\n"

    # -- Helpers --
    def load_test_data(ds_name):
        from datasets import load_dataset as _ld
        ds = _ld(ds_name, split="test")
        samples = []
        for i, item in enumerate(ds):
            text = item["text"]
            requirements = ""
            for line in text.split("\n"):
                if line.startswith("# Requirements:"):
                    requirements = line.replace("# Requirements:", "").strip()
                    break
            prompt = PROMPT_TEMPLATE.format(requirements=requirements)
            code_match = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.DOTALL)
            answer = code_match.group(1).strip() if code_match else ""
            samples.append({"id": f"test_{i}", "question": prompt, "requirements": requirements, "answer": answer})
        return samples

    def extract_code(resp):
        matches = re.findall(r"```(?:html|css|tsx|jsx|vue)?\s*\n(.*?)```", resp, re.DOTALL)
        if matches:
            return "\n".join(matches)
        s = resp.strip()
        return s if s.startswith("<") or s.startswith("<!") else s

    def wrap_in_html(code, title="UI Output"):
        if "<!DOCTYPE" in code.upper() or "<html" in code.lower():
            if "tailwindcss" not in code:
                code = code.replace("<head>", '<head>\n  <script src="https://cdn.tailwindcss.com"></script>', 1)
            return code
        return HTML_TEMPLATE.format(title=title, content=code)

    def render_screenshot(html_path, screenshot_path, browser):
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"file://{os.path.abspath(html_path)}", wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=screenshot_path, full_page=True)
            page.close()
            return True
        except Exception as e:
            print(f"  Screenshot failed: {e}")
            return False

    def img_b64(path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return ""

    def judge_output(client, prompt, model_output, reference, gen_img, gt_img, max_retries=2):
        part_before = f"You are a UI code quality judge. Rate the generation from 1-10.\n\nSCORING RUBRIC (start at 10, subtract for issues):\n- broken-code (-4)\n- broken-layout (-3)\n- wrong-framework (-2)\n- generic-colors (-2)\n- no-design-thinking (-2)\n- missing-states (-1)\n\nTASK: {prompt}\n\nGENERATION:\n{model_output}\n\nGROUND TRUTH:\n{reference}\n\nGENERATION_IMAGE:\n"
        part_between = "\n\nGROUND_TRUTH_IMAGE:\n"
        part_after = '\n\nRespond with ONLY valid JSON: {"score": <1-10>, "failure_modes": [...], "reasoning": "..."}'
        content_parts = [{"type": "text", "text": part_before}]
        if gen_img and os.path.exists(gen_img):
            b = img_b64(gen_img)
            if b:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b}"}})
        content_parts.append({"type": "text", "text": part_between})
        if gt_img and os.path.exists(gt_img):
            b = img_b64(gt_img)
            if b:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b}"}})
        content_parts.append({"type": "text", "text": part_after})
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(1)
                resp = client.chat.completions.create(model=judge_model, messages=[{"role": "user", "content": content_parts}], max_tokens=8192, temperature=0.0)
                raw = (resp.choices[0].message.content or "").strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
                    raw = re.sub(r"\n?```\s*$", "", raw)
                m = re.search(r"\{[^{}]*(?:\[[^\[\]]*\][^{}]*)*\}", raw, re.DOTALL)
                if m:
                    js = re.sub(r'(?<=: ")(.*?)(?=")', lambda x: x.group(1).replace('\n', ' '), m.group(), flags=re.DOTALL)
                    parsed = json.loads(js)
                    if "score" in parsed:
                        return parsed
            except Exception as e:
                print(f"  Judge attempt {attempt} error: {e}")
        return {"score": 0, "failure_modes": ["judge-error"], "reasoning": "All attempts failed"}

    def generate_response(mdl, tok, question, max_new_tokens=4096):
        inputs = tok(question, return_tensors="pt").to("cuda")
        outputs = mdl.generate(**inputs, max_new_tokens=max_new_tokens, temperature=0.7, top_p=0.9, top_k=20, do_sample=True)
        return tok.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # -- Main evaluation flow --
    print(f"Base: {base_model_name}, LoRA: {lora_model_name}, Dataset: {hf_dataset}, Limit: {limit}")

    samples = load_test_data(hf_dataset)
    if limit:
        samples = samples[:limit]
    print(f"Loaded {len(samples)} test samples")

    openrouter_client = None
    if use_judge:
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            openrouter_client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)
        else:
            print("WARNING: No OPENROUTER_API_KEY, disabling judge")
            use_judge = False

    print(f"Loading base model: {base_model_name}")
    base_model, base_tokenizer = FastLanguageModel.from_pretrained(model_name=base_model_name, max_seq_length=4096, load_in_4bit=True)
    FastLanguageModel.for_inference(base_model)

    print(f"Loading LoRA model: {lora_model_name}")
    lora_model, _ = FastLanguageModel.from_pretrained(model_name=lora_model_name, max_seq_length=4096, load_in_4bit=True)
    lora_tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    FastLanguageModel.for_inference(lora_model)

    model_cache_vol.commit()

    base_short = base_model_name.split("/")[-1]
    lora_short = lora_model_name.split("/")[-1]
    run_name = f"comparison-{base_short}-vs-{lora_short}-{time.strftime('%m%d-%H%M')}"
    output_dir = f"/results/{run_name}"
    screenshots_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    run = wandb.init(project=wandb_project, name=run_name, config=config_dict)
    wandb_url = run.url

    # Publish URL immediately so the frontend can show it while running
    run_urls[run_name] = wandb_url

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)

    base_judgments, lora_judgments = [], []

    for i, sample in enumerate(samples):
        sid = sample["id"]
        question = sample["question"]
        requirements = sample.get("requirements", question[:100])
        reference = sample["answer"]
        print(f"\n[{i+1}/{len(samples)}] {requirements[:50]}...")

        try:
            base_raw = generate_response(base_model, base_tokenizer, question)
        except Exception as e:
            base_raw = f"ERROR: {e}"
        try:
            lora_raw = generate_response(lora_model, lora_tokenizer, question)
        except Exception as e:
            lora_raw = f"ERROR: {e}"

        be, le = extract_code(base_raw), extract_code(lora_raw)
        bh, lh, gh = wrap_in_html(be, f"Base-{sid}"), wrap_in_html(le, f"FT-{sid}"), wrap_in_html(reference, f"GT-{sid}")

        bp = os.path.join(output_dir, f"{sid}_base.html")
        lp = os.path.join(output_dir, f"{sid}_lora.html")
        gp = os.path.join(output_dir, f"{sid}_gt.html")
        bi = os.path.join(screenshots_dir, f"{sid}_base.png")
        li = os.path.join(screenshots_dir, f"{sid}_lora.png")
        gi = os.path.join(screenshots_dir, f"{sid}_gt.png")

        for path, html in [(bp, bh), (lp, lh), (gp, gh)]:
            with open(path, "w") as f:
                f.write(html)

        render_screenshot(bp, bi, browser)
        render_screenshot(lp, li, browser)
        render_screenshot(gp, gi, browser)

        if use_judge and openrouter_client:
            bj = judge_output(openrouter_client, question, be, reference, bi, gi)
            base_judgments.append(bj)
            lj = judge_output(openrouter_client, question, le, reference, li, gi)
            lora_judgments.append(lj)
            wandb.log({"base_score": bj.get("score", 0), "lora_score": lj.get("score", 0), "score_diff": lj.get("score", 0) - bj.get("score", 0), "sample_idx": i})

    browser.close()
    pw.stop()

    base_avg, lora_avg = 0.0, 0.0
    if base_judgments:
        scores = [j["score"] for j in base_judgments if j.get("score", 0) > 0]
        base_avg = sum(scores) / len(scores) if scores else 0
        wandb.summary["base_avg_score"] = round(base_avg, 2)
    if lora_judgments:
        scores = [j["score"] for j in lora_judgments if j.get("score", 0) > 0]
        lora_avg = sum(scores) / len(scores) if scores else 0
        wandb.summary["lora_avg_score"] = round(lora_avg, 2)

    wandb.summary["score_improvement"] = round(lora_avg - base_avg, 2)
    wandb.summary["num_samples"] = len(samples)

    results_vol.commit()
    wandb.finish()

    return {
        "base_avg_score": round(base_avg, 2) if base_judgments else None,
        "lora_avg_score": round(lora_avg, 2) if lora_judgments else None,
        "wandb_url": wandb_url,
        "run_name": run_name,
    }


# ---------------------------------------------------------------------------
# GRPO training — shared imports and helpers
# ---------------------------------------------------------------------------
GRPO_TIMEOUT_HOURS = 8

with train_image.imports():
    import json as _json
    import re as _re
    from datetime import datetime as _datetime

    from datasets import concatenate_datasets as _concatenate_datasets
    from datasets import get_dataset_split_names as _get_dataset_split_names
    from datasets import load_dataset as _load_dataset
    from trl import GRPOConfig, GRPOTrainer
    from unsloth import FastLanguageModel


# ---------------------------------------------------------------------------
# Dataset splitting utilities (inline — Modal can't import local modules)
# ---------------------------------------------------------------------------
_DEFAULT_EVAL_FRACTION = 0.1
_EVAL_SEED = 42
_MAX_EVAL = 200
_MIN_EVAL = 20


def _should_skip_eval(config_dict: dict) -> bool:
    """True for overfit/sanity-check runs (max_steps=1 or train_size<=4)."""
    if config_dict.get("max_steps", -1) == 1:
        return True
    train_size = config_dict.get("train_size")
    if train_size is not None and train_size <= 4:
        return True
    return False


def _load_train_eval_split(dataset_name, split_config=None, max_train_samples=None, skip_eval=False):
    """Load HF dataset and return (train, eval | None). Mirrors dataset_utils.py."""
    kwargs = {"path": dataset_name}
    if split_config:
        kwargs["name"] = split_config
    full_ds = _load_dataset(**kwargs, split="train")
    if skip_eval:
        if max_train_samples and max_train_samples < len(full_ds):
            full_ds = full_ds.select(range(max_train_samples))
        return full_ds, None
    eval_ds = None
    try:
        split_names = _get_dataset_split_names(dataset_name, config_name=split_config)
        if "test" in split_names:
            eval_ds = _load_dataset(**kwargs, split="test")
    except Exception:
        pass
    if eval_ds is not None:
        train_ds = full_ds
        if max_train_samples and max_train_samples < len(train_ds):
            train_ds = train_ds.select(range(max_train_samples))
    else:
        splits = full_ds.train_test_split(test_size=_DEFAULT_EVAL_FRACTION, seed=_EVAL_SEED)
        train_ds = splits["train"]
        eval_ds = splits["test"]
        if max_train_samples and max_train_samples < len(train_ds):
            train_ds = train_ds.select(range(max_train_samples))
    desired_eval = max(1, int(len(train_ds) * _DEFAULT_EVAL_FRACTION))
    eval_cap = min(desired_eval, _MAX_EVAL)
    if len(eval_ds) > eval_cap:
        eval_ds = eval_ds.select(range(eval_cap))
    return train_ds, eval_ds


# -- Tool-call extraction utility --

def _extract_tool_call(text: str):
    """Extract the first <tool_call>...</tool_call> block and parse JSON."""
    match = _re.search(r"<tool_call>\s*(.*?)\s*</tool_call>", text, _re.DOTALL)
    if not match:
        return None
    try:
        parsed = _json.loads(match.group(1))
        if "name" in parsed and "arguments" in parsed:
            return parsed
    except (_json.JSONDecodeError, TypeError):
        pass
    return None


# -- Hermes dataset preparation --

def _prepare_hermes_for_grpo(dataset_name, configs, max_samples, skip_eval=False):
    """Load Hermes function-calling dataset and prepare for GRPO.

    Returns (train_dataset, eval_dataset | None).
    """
    all_datasets = []
    for config in configs:
        try:
            ds = _load_dataset(dataset_name, config, split="train")
            all_datasets.append(ds)
        except Exception:
            continue
    if not all_datasets:
        raise ValueError(f"Could not load any config from {dataset_name}")
    full_dataset = _concatenate_datasets(all_datasets) if len(all_datasets) > 1 else all_datasets[0]

    if skip_eval:
        if max_samples and max_samples < len(full_dataset):
            full_dataset = full_dataset.select(range(max_samples))
        dataset = full_dataset
        eval_raw = None
    else:
        # Split from full data first, then cap training
        splits = full_dataset.train_test_split(test_size=_DEFAULT_EVAL_FRACTION, seed=_EVAL_SEED)
        dataset = splits["train"]
        eval_raw = splits["test"]
        if max_samples and max_samples < len(dataset):
            dataset = dataset.select(range(max_samples))
        desired_eval = max(1, int(len(dataset) * _DEFAULT_EVAL_FRACTION))
        eval_cap = min(desired_eval, _MAX_EVAL)
        if len(eval_raw) > eval_cap:
            eval_raw = eval_raw.select(range(eval_cap))

    def process_row(example):
        conversations = example.get("conversations", [])
        tools_raw = example.get("tools", "")
        prompt_parts = []
        ground_truth = None
        for turn in conversations:
            role = turn.get("from", turn.get("role", ""))
            content = turn.get("value", turn.get("content", ""))
            if role in ("system", "human", "user"):
                prompt_parts.append(content)
            elif role in ("gpt", "assistant"):
                tc = _extract_tool_call(content)
                if tc and ground_truth is None:
                    ground_truth = _json.dumps(tc)
        available_tools = []
        if tools_raw:
            try:
                tools_list = _json.loads(tools_raw) if isinstance(tools_raw, str) else tools_raw
                if isinstance(tools_list, list):
                    for tool in tools_list:
                        if isinstance(tool, dict):
                            name = tool.get("function", {}).get("name") or tool.get("name", "")
                            if name:
                                available_tools.append(name)
            except (_json.JSONDecodeError, TypeError):
                pass
        return {
            "prompt": "\n\n".join(prompt_parts),
            "ground_truth": ground_truth or "",
            "available_tools": _json.dumps(available_tools),
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


# -- Completion text extraction --
# TRL passes completions as list[str] for standard-format datasets,
# or list[list[dict]] for conversational format. This helper normalises both.

def _get_completion_text(completion):
    """Extract text from a completion (str or list[dict] or list[list[dict]])."""
    if isinstance(completion, str):
        return completion
    if isinstance(completion, list):
        if not completion:
            return ""
        first = completion[0]
        if isinstance(first, dict):
            return first.get("content", "")
        if isinstance(first, list) and first:
            return first[0].get("content", "") if isinstance(first[0], dict) else str(first[0])
    return str(completion)


# -- Tool-calling reward functions --

def _valid_json_reward(completions, **kwargs):
    """Is <tool_call> present with parseable JSON containing 'name' + 'arguments'?"""
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg)
        rewards.append(1.0 if _extract_tool_call(text) is not None else 0.0)
    return rewards


def _correct_tool_reward(completions, ground_truth=None, **kwargs):
    """Does function name match ground truth?"""
    if not ground_truth:
        return [0.0] * len(completions)
    rewards = []
    for cg, gt_json in zip(completions, ground_truth):
        text = _get_completion_text(cg)
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            gt = _json.loads(gt_json)
            rewards.append(1.0 if tc["name"] == gt["name"] else 0.0)
        except (_json.JSONDecodeError, KeyError):
            rewards.append(0.0)
    return rewards


def _correct_params_reward(completions, ground_truth=None, **kwargs):
    """Per-parameter overlap with ground truth arguments (0.0-1.0 graduated)."""
    if not ground_truth:
        return [0.0] * len(completions)
    rewards = []
    for cg, gt_json in zip(completions, ground_truth):
        text = _get_completion_text(cg)
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            gt = _json.loads(gt_json)
            gt_args = gt.get("arguments", {})
            pred_args = tc.get("arguments", {})
            if not gt_args:
                rewards.append(1.0 if not pred_args else 0.5)
                continue
            correct = sum(
                1 for k, v in gt_args.items()
                if k in pred_args and str(pred_args[k]) == str(v)
            )
            rewards.append(correct / len(gt_args))
        except (_json.JSONDecodeError, KeyError):
            rewards.append(0.0)
    return rewards


def _no_hallucination_reward(completions, available_tools=None, **kwargs):
    """Tool exists in available set? -2.0 for hallucinated, 1.0 for valid."""
    if not available_tools:
        return [0.0] * len(completions)
    rewards = []
    for cg, tools_json in zip(completions, available_tools):
        text = _get_completion_text(cg)
        tc = _extract_tool_call(text)
        if tc is None:
            rewards.append(0.0)
            continue
        try:
            tool_list = _json.loads(tools_json) if isinstance(tools_json, str) else tools_json
            rewards.append(1.0 if tc["name"] in tool_list else -2.0)
        except (_json.JSONDecodeError, TypeError):
            rewards.append(0.0)
    return rewards


# -- Shared model loading + saving --

def _load_model_with_lora(config_dict):
    """Load base model and apply LoRA. Returns (model, tokenizer)."""
    model_name = config_dict.get("model_name", "Qwen/Qwen2.5-Coder-14B")
    max_seq_length = config_dict.get("max_seq_length", 4096)
    load_in_4bit = config_dict.get("load_in_4bit", True)
    lora_r = config_dict.get("lora_r", 32)
    lora_alpha = config_dict.get("lora_alpha", lora_r)
    seed = config_dict.get("seed", 3407)

    print(f"Loading model: {model_name}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=load_in_4bit,
    )
    model_cache_vol.commit()

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
    print(f"Params: {total_params:,} total, {trainable_params:,} trainable "
          f"({100 * trainable_params / total_params:.2f}%)")
    return model, tokenizer


def _save_model(model, tokenizer, config_dict, checkpoint_path):
    """Push to HF or save to checkpoint volume. Returns hf_repo_url or None."""
    import os

    push_to_hub = config_dict.get("push_to_hub", False)
    hf_repo_name = config_dict.get("hf_repo_name", "")
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
            model.save_pretrained(f"{checkpoint_path}/final_model")
            tokenizer.save_pretrained(f"{checkpoint_path}/final_model")
    else:
        model.save_pretrained(f"{checkpoint_path}/final_model")
        tokenizer.save_pretrained(f"{checkpoint_path}/final_model")

    checkpoint_vol.commit()
    return hf_repo_url


# -- UI dataset preparation --

def _prepare_ui_dataset(dataset_name, max_samples, skip_eval=False):
    """Load UI code generation dataset and prepare for GRPO.

    Returns (train_dataset, eval_dataset | None).
    """
    train_ds, eval_ds = _load_train_eval_split(
        dataset_name, max_train_samples=max_samples, skip_eval=skip_eval,
    )

    def process_row(example):
        text = example.get("text", "")
        prompt = ""
        for line in text.split("\n"):
            if line.startswith("# Task:") or line.startswith("# Requirements:"):
                prompt = line.replace("# Task:", "").replace("# Requirements:", "").strip()
                break
        if not prompt:
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


# -- UI reward functions (adapted from Tinker blog) --

def _completeness_reward(completions, **kwargs):
    """Reward complete code (+7.5), heavily penalize truncated (-15.0)."""
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg).strip()
        has_closing = any([
            text.endswith("/>"), text.endswith(");"), text.endswith("</div>"),
            text.endswith("</main>"), text.endswith("</section>"),
            text.endswith("}"), "export default" in text,
            text.rstrip().endswith("```"),
        ])
        rewards.append(7.5 if has_closing else -15.0)
    return rewards


def _validity_reward(completions, **kwargs):
    """Balanced braces, brackets, parentheses (0-3 points)."""
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg)
        score = 0.0
        if text.count("{") == text.count("}"):
            score += 1.0
        if text.count("[") == text.count("]"):
            score += 1.0
        if text.count("(") == text.count(")"):
            score += 1.0
        rewards.append(score)
    return rewards


def _interactivity_reward(completions, **kwargs):
    """Reward React hooks and event handlers (0-5 points)."""
    patterns = [
        r"useState", r"useEffect", r"onClick",
        r"onChange", r"onSubmit|onKeyDown|onKeyPress|onFocus|onBlur",
    ]
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg)
        score = sum(1.0 for p in patterns if _re.search(p, text))
        rewards.append(score)
    return rewards


def _quote_balance_reward(completions, **kwargs):
    """Balanced quotes (0-2 points)."""
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg)
        score = 0.0
        if len(_re.findall(r'(?<!\\)"', text)) % 2 == 0:
            score += 1.0
        if len(_re.findall(r"(?<!\\)'", text)) % 2 == 0 and text.count("`") % 2 == 0:
            score += 1.0
        rewards.append(score)
    return rewards


def _length_penalty(completions, **kwargs):
    """Penalize extremely short (<50) or long (>8000) outputs."""
    rewards = []
    for cg in completions:
        text = _get_completion_text(cg)
        length = len(text)
        if length < 50:
            rewards.append(-5.0)
        elif length > 8000:
            rewards.append(-2.0)
        else:
            rewards.append(0.0)
    return rewards


# -- Quick eval functions --

def _run_grpo_quick_eval(model, tokenizer, eval_dataset, wandb_module):
    """Generate on held-out eval prompts and score with reward functions."""
    print(f"\nRunning quick GRPO eval on {len(eval_dataset)} held-out examples...")
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
            is_valid = tc is not None
            if is_valid:
                valid_json_count += 1

            is_correct_tool = False
            is_correct_params = False
            is_no_hallucination = False

            if tc:
                try:
                    gt = _json.loads(gt_json)
                    is_correct_tool = tc["name"] == gt["name"]
                except (_json.JSONDecodeError, KeyError):
                    pass
                try:
                    gt = _json.loads(gt_json)
                    gt_args = gt.get("arguments", {})
                    pred_args = tc.get("arguments", {})
                    if not gt_args:
                        is_correct_params = not pred_args
                    else:
                        correct = sum(1 for k, v in gt_args.items() if k in pred_args and str(pred_args[k]) == str(v))
                        is_correct_params = correct == len(gt_args)
                except (_json.JSONDecodeError, KeyError):
                    pass
                try:
                    tool_list = _json.loads(tools_json)
                    is_no_hallucination = tc["name"] in tool_list
                except (_json.JSONDecodeError, TypeError):
                    pass

            if is_correct_tool:
                correct_tool_count += 1
            if is_correct_params:
                correct_params_total += 1
            if is_no_hallucination:
                no_hallucination_count += 1
            if is_valid and is_correct_tool and is_correct_params and is_no_hallucination:
                overall_pass_count += 1

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
        print(f"Quick GRPO eval failed (non-fatal): {e}")


def _run_ui_quick_eval(model, tokenizer, eval_dataset, wandb_module):
    """Generate on held-out UI prompts and score with 5 reward functions."""
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

            # Score using inline reward functions
            comp = [response]
            completeness_scores.append(1.0 if _completeness_reward(comp)[0] == 7.5 else 0.0)
            validity_scores.append(_validity_reward(comp)[0] / 3.0)
            interactivity_scores.append(_interactivity_reward(comp)[0] / 5.0)
            quote_scores.append(_quote_balance_reward(comp)[0] / 2.0)
            length_scores.append(0.0 if _length_penalty(comp)[0] == 0.0 else 1.0)

        wandb_module.log({
            "eval/completeness_rate": sum(completeness_scores) / total,
            "eval/validity_avg": sum(validity_scores) / total,
            "eval/interactivity_avg": sum(interactivity_scores) / total,
            "eval/quote_balance_avg": sum(quote_scores) / total,
            "eval/length_penalty_rate": sum(length_scores) / total,
        })
        print(f"UI Eval results: completeness={sum(completeness_scores)/total:.2f}, "
              f"validity={sum(validity_scores)/total:.2f}, "
              f"interactivity={sum(interactivity_scores)/total:.2f}")

    except Exception as e:
        print(f"Quick UI eval failed (non-fatal): {e}")


# ---------------------------------------------------------------------------
# GRPO Modal functions
# ---------------------------------------------------------------------------

@app.function(
    image=train_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/checkpoints": checkpoint_vol,
    },
    secrets=[modal.Secret.from_name("wandb-secret"), modal.Secret.from_name("hf-secret")],
    timeout=GRPO_TIMEOUT_HOURS * 60 * 60,
)
def run_grpo(config_dict: dict) -> dict:
    """Run GRPO training for tool calling with Hermes function-calling dataset."""
    import wandb

    # Parse config
    model_name = config_dict.get("model_name", "Qwen/Qwen2.5-Coder-14B")
    dataset_name = config_dict.get("dataset_name", "NousResearch/hermes-function-calling-v1")
    lora_r = config_dict.get("lora_r", 32)
    max_steps = config_dict.get("max_steps", -1)
    num_epochs = config_dict.get("num_epochs", 1)
    train_size = config_dict.get("train_size")
    wandb_project = config_dict.get("wandb_project", "grpo-tool-calling")

    timestamp = _datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = config_dict.get(
        "experiment_name", f"{model_short}-grpo-r{lora_r}-{timestamp}"
    )
    if not config_dict.get("hf_repo_name"):
        config_dict["hf_repo_name"] = experiment_name

    # W&B
    wandb.init(project=wandb_project, name=experiment_name, config=config_dict)
    wandb_url = wandb.run.url
    print(f"W&B run: {wandb_url}\n")
    run_urls[experiment_name] = wandb_url

    # Model
    model, tokenizer = _load_model_with_lora(config_dict)

    # Dataset
    skip_eval = _should_skip_eval(config_dict)
    print(f"Loading dataset: {dataset_name}")
    dataset, eval_dataset = _prepare_hermes_for_grpo(
        dataset_name, ("func_calling_singleturn", "func_calling"), train_size,
        skip_eval=skip_eval,
    )
    print(f"Prepared {len(dataset)} GRPO train samples"
          + (f", {len(eval_dataset)} eval samples" if eval_dataset else " (eval skipped)"))

    # Train
    checkpoint_path = f"/checkpoints/{experiment_name}"
    _num_epochs = 1 if max_steps > 0 else num_epochs
    _max_steps = max_steps if max_steps > 0 else -1

    num_generations = config_dict.get("num_generations", 4)
    training_args = GRPOConfig(
        output_dir=checkpoint_path,
        learning_rate=config_dict.get("learning_rate", 5e-6),
        per_device_train_batch_size=num_generations,
        gradient_accumulation_steps=config_dict.get("gradient_accumulation_steps", 1),
        num_generations=num_generations,
        temperature=config_dict.get("temperature", 1.0),
        max_prompt_length=config_dict.get("max_prompt_length", 1024),
        max_completion_length=config_dict.get("max_completion_length", 512),
        num_train_epochs=_num_epochs,
        max_steps=_max_steps,
        optim="adamw_8bit",
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        logging_steps=1,
        report_to="wandb",
        save_steps=50,
        save_strategy="steps",
        seed=config_dict.get("seed", 3407),
    )
    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        args=training_args,
        train_dataset=dataset,
        reward_funcs=[
            _valid_json_reward, _correct_tool_reward,
            _correct_params_reward, _no_hallucination_reward,
        ],
    )
    print("Starting GRPO training...\n")
    trainer_stats = trainer.train()

    # Results
    runtime_seconds = trainer_stats.metrics.get("train_runtime", 0)
    runtime_minutes = round(runtime_seconds / 60, 2)
    final_reward = None
    if trainer.state.log_history:
        for entry in reversed(trainer.state.log_history):
            if "reward" in entry:
                final_reward = round(entry["reward"], 4)
                break
    print(f"Training complete! {runtime_minutes} min, final_reward={final_reward}")

    # Quick eval on held-out samples
    if eval_dataset is not None:
        _run_grpo_quick_eval(model, tokenizer, eval_dataset, wandb)

    hf_repo_url = _save_model(model, tokenizer, config_dict, checkpoint_path)
    wandb.finish()

    return {
        "experiment_name": experiment_name,
        "wandb_url": wandb_url,
        "final_reward": final_reward,
        "runtime_minutes": runtime_minutes,
        "hf_repo_url": hf_repo_url,
    }


@app.function(
    image=train_image,
    gpu="A100-80GB",
    volumes={
        "/model_cache": model_cache_vol,
        "/checkpoints": checkpoint_vol,
    },
    secrets=[modal.Secret.from_name("wandb-secret"), modal.Secret.from_name("hf-secret")],
    timeout=GRPO_TIMEOUT_HOURS * 60 * 60,
)
def run_grpo_ui(config_dict: dict) -> dict:
    """Run GRPO training for generative UI (React code generation)."""
    import wandb

    # Parse config
    model_name = config_dict.get("model_name", "Qwen/Qwen2.5-Coder-14B")
    dataset_name = config_dict.get("dataset_name", "lilyzhng/uigen-ui-code-gen")
    lora_r = config_dict.get("lora_r", 32)
    max_steps = config_dict.get("max_steps", -1)
    num_epochs = config_dict.get("num_epochs", 1)
    train_size = config_dict.get("train_size")
    wandb_project = config_dict.get("wandb_project", "grpo-ui-gen")

    timestamp = _datetime.now().strftime("%Y%m%d-%H%M%S")
    model_short = model_name.split("/")[-1]
    experiment_name = config_dict.get(
        "experiment_name", f"{model_short}-grpo-ui-r{lora_r}-{timestamp}"
    )
    if not config_dict.get("hf_repo_name"):
        config_dict["hf_repo_name"] = experiment_name

    # W&B
    wandb.init(project=wandb_project, name=experiment_name, config=config_dict)
    wandb_url = wandb.run.url
    print(f"W&B run: {wandb_url}\n")
    run_urls[experiment_name] = wandb_url

    # Model
    model, tokenizer = _load_model_with_lora(config_dict)

    # Dataset
    skip_eval = _should_skip_eval(config_dict)
    print(f"Loading dataset: {dataset_name}")
    dataset, eval_dataset = _prepare_ui_dataset(dataset_name, train_size, skip_eval=skip_eval)
    print(f"Prepared {len(dataset)} UI GRPO train samples"
          + (f", {len(eval_dataset)} eval samples" if eval_dataset else " (eval skipped)"))

    # Train
    checkpoint_path = f"/checkpoints/{experiment_name}"
    _num_epochs = 1 if max_steps > 0 else num_epochs
    _max_steps = max_steps if max_steps > 0 else -1

    num_generations = config_dict.get("num_generations", 4)
    training_args = GRPOConfig(
        output_dir=checkpoint_path,
        learning_rate=config_dict.get("learning_rate", 5e-6),
        per_device_train_batch_size=num_generations,
        gradient_accumulation_steps=config_dict.get("gradient_accumulation_steps", 1),
        num_generations=num_generations,
        temperature=config_dict.get("temperature", 1.0),
        max_prompt_length=config_dict.get("max_prompt_length", 1024),
        max_completion_length=config_dict.get("max_completion_length", 2048),
        num_train_epochs=_num_epochs,
        max_steps=_max_steps,
        optim="adamw_8bit",
        lr_scheduler_type="linear",
        warmup_ratio=0.1,
        logging_steps=1,
        report_to="wandb",
        save_steps=50,
        save_strategy="steps",
        seed=config_dict.get("seed", 3407),
    )
    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        args=training_args,
        train_dataset=dataset,
        reward_funcs=[
            _completeness_reward, _validity_reward,
            _interactivity_reward, _quote_balance_reward, _length_penalty,
        ],
    )
    print("Starting GRPO UI training...\n")
    trainer_stats = trainer.train()

    # Results
    runtime_seconds = trainer_stats.metrics.get("train_runtime", 0)
    runtime_minutes = round(runtime_seconds / 60, 2)
    final_reward = None
    if trainer.state.log_history:
        for entry in reversed(trainer.state.log_history):
            if "reward" in entry:
                final_reward = round(entry["reward"], 4)
                break
    print(f"Training complete! {runtime_minutes} min, final_reward={final_reward}")

    # Quick eval on held-out samples
    if eval_dataset is not None:
        _run_ui_quick_eval(model, tokenizer, eval_dataset, wandb)

    hf_repo_url = _save_model(model, tokenizer, config_dict, checkpoint_path)
    wandb.finish()

    return {
        "experiment_name": experiment_name,
        "wandb_url": wandb_url,
        "final_reward": final_reward,
        "runtime_minutes": runtime_minutes,
        "hf_repo_url": hf_repo_url,
    }


# ---------------------------------------------------------------------------
# CLI entrypoints — use these with `modal run` since bare `dict` params
# can't be parsed by Modal CLI. Pass config as a JSON string instead.
#
#   modal run --detach backend/modal_app/app.py::cli_grpo --config-json '{...}'
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def cli_grpo(config_json: str):
    """Launch GRPO tool-calling training from CLI."""
    import json as _j
    result = run_grpo.remote(_j.loads(config_json))
    print(_j.dumps(result, indent=2))


@app.local_entrypoint()
def cli_grpo_ui(config_json: str):
    """Launch GRPO UI training from CLI."""
    import json as _j
    result = run_grpo_ui.remote(_j.loads(config_json))
    print(_j.dumps(result, indent=2))


@app.local_entrypoint()
def cli_finetune(config_json: str):
    """Launch SFT fine-tuning from CLI."""
    import json as _j
    result = run_finetune.remote(_j.loads(config_json))
    print(_j.dumps(result, indent=2))
