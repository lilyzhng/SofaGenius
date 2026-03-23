"""
Convert APEX tasks from HuggingFace to Harbor task format.

Supports:
- mercor/APEX-v1-extended (100 tasks, trainable)
- mercor/apex-agents (480 tasks, eval only)

Usage:
    python scripts/convert_apex_to_harbor.py --dataset mercor/APEX-v1-extended --output tasks/
    python scripts/convert_apex_to_harbor.py --dataset mercor/apex-agents --output tasks-eval/ --limit 10
"""

import argparse
import json
import logging
import re
import shutil
from pathlib import Path

from datasets import load_dataset

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "harbor_template"

KEYWORD_NOISE = {
    "The", "This", "That", "These", "Those", "Each", "For", "And",
    "But", "Not", "All", "Any", "Has", "Are", "Was", "Were", "Can",
    "May", "Should", "Would", "Could", "Will", "Must", "Also",
    "Based", "Using", "FROM", "INTO", "WITH", "THEN", "WHEN",
    "NULL", "TRUE", "ELSE", "CASE", "JSON",
}


def extract_keywords(rubric_raw) -> list[str]:
    """Extract meaningful keywords from rubric for verification."""
    if isinstance(rubric_raw, str):
        try:
            rubric = json.loads(rubric_raw)
        except json.JSONDecodeError:
            return []
    else:
        rubric = rubric_raw

    criteria = []
    if isinstance(rubric, dict):
        criteria = list(rubric.values())
    elif isinstance(rubric, list):
        criteria = rubric
    else:
        return []

    keywords = set()
    for criterion in criteria:
        if isinstance(criterion, str):
            text = criterion
        elif isinstance(criterion, dict):
            text = " ".join([
                criterion.get("criteria", ""),
                criterion.get("criterion", ""),
                criterion.get("description", ""),
                criterion.get("justification", ""),
            ])
        else:
            continue

        keywords.update(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text))
        keywords.update(re.findall(r'"([^"]+)"', text))
        keywords.update(re.findall(r"\b[A-Z]{2,6}\b", text))
        keywords.update(re.findall(r"\$?[\d,.]+[%BMK]?\b", text))

    keywords -= KEYWORD_NOISE
    keywords = {kw for kw in keywords if len(kw) > 1}
    return sorted(keywords)


def get_difficulty(rubric_raw) -> str:
    if isinstance(rubric_raw, str):
        try:
            rubric = json.loads(rubric_raw)
        except json.JSONDecodeError:
            return "medium"
    else:
        rubric = rubric_raw

    n = len(rubric) if isinstance(rubric, (dict, list)) else 0
    if n <= 3:
        return "easy"
    elif n <= 6:
        return "medium"
    return "hard"


def generate_task(row, source_idx: int, output_dir: Path) -> str:
    """Generate a single Harbor task directory. Returns task_id."""
    domain = row.get("Domain", row.get("domain", "unknown"))
    prompt = row.get("Prompt", row.get("prompt", ""))
    rubric_raw = row.get("Rubric JSON", row.get("rubric", []))
    expected_output = row.get("expected_output", "text")
    gold_response = row.get("gold_response", "")

    normalized_domain = domain.lower().replace(" ", "-")
    task_id = f"apex-{normalized_domain}-{source_idx:03d}"
    task_dir = output_dir / task_id

    if task_dir.exists():
        shutil.rmtree(task_dir)
    task_dir.mkdir(parents=True)

    # Copy template
    if TEMPLATE_DIR.exists():
        for item in TEMPLATE_DIR.iterdir():
            dst = task_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)

    # Write instruction.md
    instruction = f"""You are a professional analyst specializing in {domain}.

Solve the following task using bash commands. You have access to:
- Python 3 with pandas, openpyxl, pdfplumber
- Standard unix tools (grep, awk, sed, jq, etc.)
- Any files in /app/data/

## Task

{prompt}

## Instructions

1. Read and analyze any provided files in /app/data/
2. Perform calculations or analysis as needed
3. Write your final answer to /app/answer.txt

Your answer should be thorough and address all aspects of the task.
When finished, write your complete analysis to /app/answer.txt.
"""
    (task_dir / "instruction.md").write_text(instruction)

    # Extract keywords and write test config
    keywords = extract_keywords(rubric_raw)

    test_config = {
        "task_id": task_id,
        "source_index": source_idx,
        "domain": domain,
        "keywords": keywords,
        "num_keywords": len(keywords),
        "expected_output": expected_output,
        "gold_response": gold_response[:500] if gold_response else "",
    }
    if isinstance(rubric_raw, (dict, list)):
        test_config["rubric"] = rubric_raw
    elif isinstance(rubric_raw, str):
        try:
            test_config["rubric"] = json.loads(rubric_raw)
        except json.JSONDecodeError:
            test_config["rubric"] = rubric_raw

    (task_dir / "tests" / "config.json").write_text(
        json.dumps(test_config, indent=2, ensure_ascii=False)
    )
    (task_dir / "tests" / "keywords.json").write_text(
        json.dumps(keywords, ensure_ascii=False)
    )

    # Customize task.toml
    task_toml = task_dir / "task.toml"
    if task_toml.exists():
        content = task_toml.read_text()
        content = content.replace("{domain}", domain)
        content = content.replace("{difficulty}", get_difficulty(rubric_raw))
        task_toml.write_text(content)

    # Write oracle solution
    solve_path = task_dir / "solution" / "solve.sh"
    if solve_path.exists() and gold_response:
        escaped = gold_response.replace("'", "'\\''")
        content = solve_path.read_text()
        content = content.replace("{GOLD_RESPONSE}", escaped)
        solve_path.write_text(content)

    return task_id


def main():
    parser = argparse.ArgumentParser(description="Convert APEX tasks to Harbor format")
    parser.add_argument("--dataset", default="mercor/APEX-v1-extended",
                        help="HuggingFace dataset name")
    parser.add_argument("--output", default="tasks/",
                        help="Output directory for Harbor tasks")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of tasks (0 = all)")
    parser.add_argument("--split", default="train",
                        help="Dataset split to use")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading dataset: {args.dataset}")
    ds = load_dataset(args.dataset, split=args.split)

    n = len(ds) if args.limit == 0 else min(args.limit, len(ds))
    logger.info(f"Converting {n} tasks to Harbor format → {output_dir}")

    task_ids = []
    for i in range(n):
        row = ds[i]
        task_id = generate_task(row, i, output_dir)
        task_ids.append(task_id)
        if (i + 1) % 10 == 0:
            logger.info(f"  Converted {i + 1}/{n}")

    logger.info(f"Done. {len(task_ids)} tasks written to {output_dir}")

    # Write manifest
    manifest = {
        "source": args.dataset,
        "split": args.split,
        "count": len(task_ids),
        "task_ids": task_ids,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    logger.info(f"Manifest written to {output_dir / 'manifest.json'}")


if __name__ == "__main__":
    main()
