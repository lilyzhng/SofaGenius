"""Evaluation implementation for Sofa Genius Modal app.

Adapted from Qwen3-Coder/unsloth/modal_eval.py — same side-by-side comparison,
Playwright screenshots, OpenRouter judge logic, but accepts a plain dict config
and returns a result dict.
"""

from __future__ import annotations


def eval_impl(config_dict: dict) -> dict:
    """Run side-by-side evaluation. Returns result dict."""
    import os
    import json
    import time
    import base64
    import re

    # Disable Unsloth statistics check
    os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"

    import wandb
    from openai import OpenAI
    from playwright.sync_api import sync_playwright
    from unsloth import FastLanguageModel
    from transformers import AutoTokenizer

    # ---------------------------------------------------------------------------
    # Parse config
    # ---------------------------------------------------------------------------
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

    HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <title>{title}</title>
</head>
<body>
{content}
</body>
</html>
"""

    PROMPT_TEMPLATE = "# Task: Generate HTML/CSS code using Tailwind CSS\n# Requirements: {requirements}\n\n"

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------
    def load_test_data(ds_name: str) -> list[dict]:
        from datasets import load_dataset as _load_dataset
        dataset = _load_dataset(ds_name, split="test")
        samples = []
        for i, item in enumerate(dataset):
            text = item["text"]
            lines = text.split("\n")
            requirements = ""
            for line in lines:
                if line.startswith("# Requirements:"):
                    requirements = line.replace("# Requirements:", "").strip()
                    break
            full_prompt = PROMPT_TEMPLATE.format(requirements=requirements)
            code_match = re.search(r"```(?:html)?\s*\n(.*?)```", text, re.DOTALL)
            answer = code_match.group(1).strip() if code_match else ""
            samples.append({
                "id": f"test_{i}",
                "question": full_prompt,
                "requirements": requirements,
                "answer": answer,
            })
        return samples

    def extract_code(response_text: str) -> str:
        pattern = r"```(?:html|css|tsx|jsx|vue)?\s*\n(.*?)```"
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            return "\n".join(matches)
        stripped = response_text.strip()
        if stripped.startswith("<") or stripped.startswith("<!"):
            return stripped
        return stripped

    def wrap_in_html(code: str, title: str = "UI Output") -> str:
        if "<!DOCTYPE" in code.upper() or "<html" in code.lower():
            if "tailwindcss" not in code:
                code = code.replace("<head>", '<head>\n  <script src="https://cdn.tailwindcss.com"></script>', 1)
            return code
        return HTML_TEMPLATE.format(title=title, content=code)

    def render_screenshot(html_path: str, screenshot_path: str, browser) -> bool:
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

    def image_to_base64(path: str) -> str:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return ""

    def judge_output(client, prompt, model_output, reference, gen_img, gt_img, max_retries: int = 2) -> dict:
        model_output_text = model_output
        reference_text = reference

        part_before = f"""\
You are a UI code quality judge. Rate the generation from 1-10.

SCORING RUBRIC (start at 10, subtract for issues):
- broken-code (-4): syntax errors, blank page, no output
- broken-layout (-3): elements overlap, misaligned, unusable
- wrong-framework (-2): doesn't use Tailwind CSS
- generic-colors (-2): boring default palette
- no-design-thinking (-2): looks like developer prototype
- missing-states (-1): no hover/transition polish

TASK: {prompt}

GENERATION:
{model_output_text}

GROUND TRUTH:
{reference_text}

GENERATION_IMAGE:
"""
        part_between = "\n\nGROUND_TRUTH_IMAGE:\n"
        part_after = """

IMPORTANT: Respond with ONLY a valid JSON object.
```json
{"score": <1-10>, "failure_modes": ["<mode1>"], "reasoning": "<brief explanation>"}
```
"""
        content_parts = [{"type": "text", "text": part_before}]
        if gen_img and os.path.exists(gen_img):
            b64 = image_to_base64(gen_img)
            if b64:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        content_parts.append({"type": "text", "text": part_between})
        if gt_img and os.path.exists(gt_img):
            b64 = image_to_base64(gt_img)
            if b64:
                content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}})
        content_parts.append({"type": "text", "text": part_after})

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    time.sleep(1)
                response = client.chat.completions.create(
                    model=judge_model,
                    messages=[{"role": "user", "content": content_parts}],
                    max_tokens=8192,
                    temperature=0.0,
                )
                raw = response.choices[0].message.content or ""
                content = raw.strip()
                if content.startswith("```"):
                    content = re.sub(r"^```(?:json)?\s*\n?", "", content)
                    content = re.sub(r"\n?```\s*$", "", content)
                json_match = re.search(r"\{[^{}]*(?:\[[^\[\]]*\][^{}]*)*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    json_str = re.sub(r'(?<=: ")(.*?)(?=")', lambda m: m.group(1).replace('\n', ' '), json_str, flags=re.DOTALL)
                    parsed = json.loads(json_str)
                    if "score" in parsed:
                        return parsed
            except Exception as e:
                print(f"  Judge attempt {attempt} error: {e}")
                continue

        return {"score": 0, "failure_modes": ["judge-error"], "reasoning": "All judge attempts failed"}

    def generate_response(model, tokenizer, question: str, max_new_tokens: int = 4096) -> str:
        inputs = tokenizer(question, return_tensors="pt").to("cuda")
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            top_p=0.9,
            top_k=20,
            do_sample=True,
        )
        return tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

    # ---------------------------------------------------------------------------
    # Main evaluation flow
    # ---------------------------------------------------------------------------
    print(f"Base model: {base_model_name}")
    print(f"LoRA model: {lora_model_name}")
    print(f"Dataset: {hf_dataset}, Limit: {limit}")

    samples = load_test_data(hf_dataset)
    if limit:
        samples = samples[:limit]
    print(f"Loaded {len(samples)} test samples")

    # OpenRouter client
    openrouter_client = None
    if use_judge:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            openrouter_client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=openrouter_key)
        else:
            print("WARNING: No OPENROUTER_API_KEY, disabling judge")
            use_judge = False

    # Load models
    print(f"Loading base model: {base_model_name}")
    base_model, base_tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model_name, max_seq_length=4096, load_in_4bit=True,
    )
    FastLanguageModel.for_inference(base_model)

    print(f"Loading LoRA model: {lora_model_name}")
    lora_model, _ = FastLanguageModel.from_pretrained(
        model_name=lora_model_name, max_seq_length=4096, load_in_4bit=True,
    )
    lora_tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    FastLanguageModel.for_inference(lora_model)

    # W&B
    base_short = base_model_name.split("/")[-1]
    lora_short = lora_model_name.split("/")[-1]
    run_name = f"comparison-{base_short}-vs-{lora_short}-{time.strftime('%m%d-%H%M')}"

    output_dir = f"/results/{run_name}"
    screenshots_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    run = wandb.init(
        project=wandb_project,
        name=run_name,
        config=config_dict,
    )
    wandb_url = run.url

    # Browser
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)

    base_judgments = []
    lora_judgments = []

    for i, sample in enumerate(samples):
        sample_id = sample["id"]
        question = sample["question"]
        requirements = sample.get("requirements", question[:100])
        reference = sample["answer"]

        print(f"\n[{i+1}/{len(samples)}] {requirements[:50]}...")

        # Generate
        try:
            base_raw = generate_response(base_model, base_tokenizer, question)
        except Exception as e:
            base_raw = f"ERROR: {e}"
        try:
            lora_raw = generate_response(lora_model, lora_tokenizer, question)
        except Exception as e:
            lora_raw = f"ERROR: {e}"

        base_extracted = extract_code(base_raw)
        lora_extracted = extract_code(lora_raw)
        base_html = wrap_in_html(base_extracted, f"Base-{sample_id}")
        lora_html = wrap_in_html(lora_extracted, f"Finetuned-{sample_id}")
        gt_html = wrap_in_html(reference, f"GT-{sample_id}")

        base_path = os.path.join(output_dir, f"{sample_id}_base.html")
        lora_path = os.path.join(output_dir, f"{sample_id}_lora.html")
        gt_path = os.path.join(output_dir, f"{sample_id}_gt.html")
        base_img = os.path.join(screenshots_dir, f"{sample_id}_base.png")
        lora_img = os.path.join(screenshots_dir, f"{sample_id}_lora.png")
        gt_img = os.path.join(screenshots_dir, f"{sample_id}_gt.png")

        with open(base_path, "w") as f:
            f.write(base_html)
        with open(lora_path, "w") as f:
            f.write(lora_html)
        with open(gt_path, "w") as f:
            f.write(gt_html)

        render_screenshot(base_path, base_img, browser)
        render_screenshot(lora_path, lora_img, browser)
        render_screenshot(gt_path, gt_img, browser)

        if use_judge and openrouter_client:
            base_judgment = judge_output(openrouter_client, question, base_extracted, reference, base_img, gt_img)
            base_judgments.append(base_judgment)
            lora_judgment = judge_output(openrouter_client, question, lora_extracted, reference, lora_img, gt_img)
            lora_judgments.append(lora_judgment)

            wandb.log({
                "base_score": base_judgment.get("score", 0),
                "lora_score": lora_judgment.get("score", 0),
                "score_diff": lora_judgment.get("score", 0) - base_judgment.get("score", 0),
                "sample_idx": i,
            })

    browser.close()
    pw.stop()

    # Summary
    base_avg = 0.0
    lora_avg = 0.0
    if base_judgments:
        scores = [j.get("score", 0) for j in base_judgments if j.get("score", 0) > 0]
        base_avg = sum(scores) / len(scores) if scores else 0
        wandb.summary["base_avg_score"] = round(base_avg, 2)
    if lora_judgments:
        scores = [j.get("score", 0) for j in lora_judgments if j.get("score", 0) > 0]
        lora_avg = sum(scores) / len(scores) if scores else 0
        wandb.summary["lora_avg_score"] = round(lora_avg, 2)

    wandb.summary["score_improvement"] = round(lora_avg - base_avg, 2)
    wandb.summary["num_samples"] = len(samples)

    wandb.finish()

    return {
        "base_avg_score": round(base_avg, 2) if base_judgments else None,
        "lora_avg_score": round(lora_avg, 2) if lora_judgments else None,
        "wandb_url": wandb_url,
        "run_name": run_name,
    }
