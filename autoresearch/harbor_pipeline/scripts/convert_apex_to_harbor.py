"""
Convert APEX-v1-extended (100 tasks) to Harbor task format.

Reads from downloaded data (scripts/download_apex_files.py must run first).
Generates Harbor task directories with:
  - instruction.md (task prompt)
  - task.toml (metadata)
  - environment/Dockerfile
  - environment/data/ (PDF attachments)
  - tests/test.sh + reward_scorer.py + rubric.json + keywords.json
  - solution/solve.sh

Usage:
    python scripts/convert_apex_to_harbor.py
    python scripts/convert_apex_to_harbor.py --domain Finance  # single domain
"""

import argparse
import json
import os
import re
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "harbor_template"
DATA_DIR = SCRIPT_DIR.parent / "data" / "apex" / "v1-extended"
OUTPUT_DIR = SCRIPT_DIR.parent / "tasks"


def extract_keywords(rubric: dict) -> list[str]:
    """Extract verification keywords from rubric criteria."""
    keywords = set()
    for key, criterion in rubric.items():
        desc = criterion.get("description", "") if isinstance(criterion, dict) else str(criterion)

        # Proper nouns
        keywords.update(re.findall(r'\b[A-Z][a-z]{2,}\b', desc))
        # Quoted phrases
        keywords.update(re.findall(r'"([^"]+)"', desc))
        # Acronyms
        keywords.update(re.findall(r'\b[A-Z]{2,6}\b', desc))
        # Numbers with context
        keywords.update(re.findall(r'\$[\d,]+\.?\d*', desc))
        keywords.update(re.findall(r'[\d,]+\.?\d*%', desc))

    # Filter noise
    noise = {"The", "This", "That", "For", "And", "But", "Not", "Are", "Has",
             "Was", "Were", "Will", "Can", "May", "All", "Any", "Each", "Its"}
    return sorted(keywords - noise)


def generate_task(task: dict, docs_dir: Path, output_dir: Path):
    """Generate a single Harbor task directory."""
    task_id = task["task_id"]
    domain = task["domain"].lower()
    task_name = f"apex-{domain}-{task_id:04d}"
    task_dir = output_dir / task_name

    if task_dir.exists():
        shutil.rmtree(task_dir)

    # Create directory structure
    (task_dir / "environment" / "data").mkdir(parents=True)
    (task_dir / "tests").mkdir(parents=True)
    (task_dir / "solution").mkdir(parents=True)

    # --- instruction.md ---
    instruction = f"""# Task: {domain.title()} Analysis

{task["prompt"]}

## Instructions

- Your workspace has data files in `/app/data/`
- Use bash commands to explore, analyze, and solve the task
- Write your final answer to `/app/output/answer.txt`
- You can create Python scripts to help with analysis
- When done, respond with: done
"""
    (task_dir / "instruction.md").write_text(instruction)

    # --- task.toml ---
    rubric = json.loads(task["rubric_json"]) if isinstance(task["rubric_json"], str) else task["rubric_json"]
    num_criteria = len(rubric) if rubric else 0

    difficulty = "easy" if num_criteria <= 5 else "medium" if num_criteria <= 8 else "hard"

    toml_content = f"""[metadata]
author = "APEX-v1-extended (Mercor)"
difficulty = "{difficulty}"
category = "{domain}"
tags = ["professional", "{domain}", "tool-use"]
num_criteria = {num_criteria}
license = "CC-BY-4.0"

[verifier]
timeout_sec = 120

[agent]
timeout_sec = 600

[environment]
build_timeout_sec = 300
cpus = 2
memory = "2048m"
storage = "4g"
"""
    (task_dir / "task.toml").write_text(toml_content)

    # --- environment/Dockerfile ---
    shutil.copy(TEMPLATE_DIR / "environment" / "Dockerfile", task_dir / "environment" / "Dockerfile")

    # --- environment/data/ (PDF attachments) ---
    attachments = task.get("file_attachments", "") or ""
    files_copied = 0
    if attachments:
        for line in attachments.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            src = docs_dir / line
            if src.exists():
                dst = task_dir / "environment" / "data" / src.name
                shutil.copy2(src, dst)
                files_copied += 1
            else:
                print(f"  WARNING: {src} not found")

    # --- tests/ ---
    shutil.copy(TEMPLATE_DIR / "tests" / "test.sh", task_dir / "tests" / "test.sh")
    os.chmod(task_dir / "tests" / "test.sh", 0o755)
    shutil.copy(TEMPLATE_DIR / "tests" / "reward_scorer.py", task_dir / "tests" / "reward_scorer.py")

    # rubric.json
    (task_dir / "tests" / "rubric.json").write_text(json.dumps(rubric, indent=2))

    # keywords.json
    keywords = extract_keywords(rubric) if rubric else []
    (task_dir / "tests" / "keywords.json").write_text(json.dumps(keywords, indent=2))

    # --- solution/solve.sh ---
    solve = '#!/bin/bash\necho "No oracle solution available" > /app/output/answer.txt\n'
    (task_dir / "solution" / "solve.sh").write_text(solve)
    os.chmod(task_dir / "solution" / "solve.sh", 0o755)

    return task_name, files_copied, num_criteria, difficulty


def main():
    import os

    parser = argparse.ArgumentParser(description="Convert APEX-v1-extended to Harbor format")
    parser.add_argument("--domain", type=str, default=None, help="Filter by domain (Finance, Legal, etc.)")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    # Load tasks
    tasks_file = DATA_DIR / "tasks.json"
    if not tasks_file.exists():
        print(f"ERROR: {tasks_file} not found. Run download_apex_files.py first.")
        return

    with open(tasks_file) as f:
        tasks = json.load(f)

    if args.domain:
        tasks = [t for t in tasks if t["domain"].lower() == args.domain.lower()]
        print(f"Filtered to {len(tasks)} {args.domain} tasks")

    # File attachments reference paths like "documents/13/file.pdf"
    # The repo root contains the documents/ directory directly
    docs_dir = DATA_DIR / "repo"
    if not docs_dir.exists():
        print(f"ERROR: {docs_dir} not found. Run download_apex_files.py first.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Converting {len(tasks)} tasks to Harbor format ===")
    print(f"  Source: {DATA_DIR}")
    print(f"  Output: {args.output_dir}")
    print()

    stats = {"total": 0, "files_total": 0, "by_domain": {}, "by_difficulty": {}}

    for task in tasks:
        name, files, criteria, difficulty = generate_task(task, docs_dir, args.output_dir)
        stats["total"] += 1
        stats["files_total"] += files

        domain = task["domain"]
        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1

        print(f"  ✓ {name} — {criteria} criteria, {files} files, {difficulty}")

    print(f"\n=== Done: {stats['total']} tasks ===")
    print(f"  Files copied: {stats['files_total']}")
    print(f"  By domain: {stats['by_domain']}")
    print(f"  By difficulty: {stats['by_difficulty']}")


if __name__ == "__main__":
    main()
