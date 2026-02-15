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
    from datasets import load_dataset
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

    # -- Load data --
    if not dataset_name:
        raise ValueError("dataset_name is required")
    print(f"Loading dataset: {dataset_name}")
    train_size = config_dict.get("train_size")
    if train_size:
        dataset = load_dataset(dataset_name, split=f"train[:{train_size}]")
    else:
        dataset = load_dataset(dataset_name, split="train")
    print(f"Loaded {len(dataset)} samples")

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
