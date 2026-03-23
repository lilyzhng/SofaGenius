"""
Convert apex-agents (480 eval tasks) to Harbor task format.

Maps tasks to world files via world_id, extracts task_input_files
from world zips when available.

Usage:
    python scripts/convert_apex_eval.py
    python scripts/convert_apex_eval.py --domain Law
    python scripts/convert_apex_eval.py --skip-unzip  # if already unzipped
"""

import argparse
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_DIR = SCRIPT_DIR / "harbor_template"
REPO_DIR = SCRIPT_DIR.parent / "data" / "apex" / "apex-agents" / "repo"
OUTPUT_DIR = SCRIPT_DIR.parent / "tasks-eval"


def extract_keywords(rubric: list) -> list[str]:
    """Extract verification keywords from rubric criteria list."""
    keywords = set()
    for criterion in rubric:
        text = ""
        if isinstance(criterion, dict):
            text = criterion.get("criteria", "") or criterion.get("description", "")
        elif isinstance(criterion, str):
            text = criterion

        keywords.update(re.findall(r'\b[A-Z][a-z]{2,}\b', text))
        keywords.update(re.findall(r'"([^"]+)"', text))
        keywords.update(re.findall(r'\b[A-Z]{2,6}\b', text))
        keywords.update(re.findall(r'\$[\d,]+\.?\d*', text))
        keywords.update(re.findall(r'[\d,]+\.?\d*%', text))

    noise = {"The", "This", "That", "For", "And", "But", "Not", "Are", "Has",
             "Was", "Were", "Will", "Can", "May", "All", "Any", "Each", "Its"}
    return sorted(keywords - noise)


def unzip_worlds(repo_dir: Path) -> Path:
    """Unzip all world files. Returns extraction directory."""
    world_dir = repo_dir / "world_files_zipped"
    extract_dir = repo_dir.parent / "worlds_extracted"
    extract_dir.mkdir(exist_ok=True)

    if not world_dir.exists():
        print("  No world zips found")
        return extract_dir

    zips = list(world_dir.glob("*.zip"))
    print(f"=== Extracting {len(zips)} world zips ===")

    for i, zf in enumerate(sorted(zips)):
        world_name = zf.stem
        dest = extract_dir / world_name
        if dest.exists():
            continue

        print(f"  [{i+1}/{len(zips)}] {world_name} ({zf.stat().st_size / 1e6:.0f} MB)...")
        try:
            with zipfile.ZipFile(zf, "r") as z:
                z.extractall(dest)
        except Exception as e:
            print(f"    ERROR: {e}")

    return extract_dir


def find_task_files(task: dict, worlds_dir: Path, task_files_dir: Path) -> list[Path]:
    """Find input files for a task from world extractions or task_files."""
    found = []

    # Try task_files/ first
    task_id = task["task_id"]
    task_specific = task_files_dir / task_id
    if task_specific.exists():
        found.extend(f for f in task_specific.rglob("*") if f.is_file())

    # Try world extraction
    world_id = task.get("world_id", "")
    if world_id and worlds_dir.exists():
        world_dir = worlds_dir / world_id
        if world_dir.exists():
            # If task has specific input files listed, only grab those
            input_files = task.get("task_input_files", [])
            if input_files:
                for fname in input_files:
                    if isinstance(fname, str):
                        matches = list(world_dir.rglob(fname))
                        found.extend(matches)
            # Otherwise grab common document types
            elif not found:
                for ext in ["*.pdf", "*.docx", "*.xlsx", "*.csv", "*.txt"]:
                    found.extend(world_dir.rglob(ext))

    return found[:20]  # cap at 20 files per task


def generate_eval_task(task: dict, worlds_dir: Path, task_files_dir: Path, output_dir: Path):
    """Generate a single Harbor eval task directory."""
    task_id = task["task_id"]
    domain = task["domain"].lower().replace(" ", "_")
    short_id = task_id.replace("task_", "")[:12]
    task_name = f"eval-{domain}-{short_id}"
    task_dir = output_dir / task_name

    if task_dir.exists():
        shutil.rmtree(task_dir)

    (task_dir / "environment" / "data").mkdir(parents=True)
    (task_dir / "tests").mkdir(parents=True)
    (task_dir / "solution").mkdir(parents=True)

    # --- instruction.md ---
    instruction = f"""# Task: {task['domain']} Analysis

{task['prompt']}

## Instructions

- Your workspace has data files in `/app/data/` (if applicable)
- Use bash commands to explore, analyze, and solve the task
- Write your final answer to `/app/output/answer.txt`
- When done, respond with: done
"""
    (task_dir / "instruction.md").write_text(instruction)

    # --- Copy data files ---
    files = find_task_files(task, worlds_dir, task_files_dir)
    files_copied = 0
    for f in files:
        dst = task_dir / "environment" / "data" / f.name
        if not dst.exists():
            try:
                shutil.copy2(f, dst)
                files_copied += 1
            except Exception:
                pass

    # --- task.toml ---
    rubric = task.get("rubric", [])
    num_criteria = len(rubric) if isinstance(rubric, list) else 0
    difficulty = "easy" if num_criteria <= 3 else "medium" if num_criteria <= 6 else "hard"

    toml_content = f"""[metadata]
author = "apex-agents (Mercor)"
difficulty = "{difficulty}"
category = "{domain}"
tags = ["professional", "{domain}", "eval-only"]
num_criteria = {num_criteria}
license = "eval-only"
note = "BENCHMARK DATA — NOT FOR TRAINING"

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

    # --- Dockerfile, test.sh, reward_scorer.py ---
    shutil.copy(TEMPLATE_DIR / "environment" / "Dockerfile", task_dir / "environment" / "Dockerfile")
    shutil.copy(TEMPLATE_DIR / "tests" / "test.sh", task_dir / "tests" / "test.sh")
    os.chmod(task_dir / "tests" / "test.sh", 0o755)
    shutil.copy(TEMPLATE_DIR / "tests" / "reward_scorer.py", task_dir / "tests" / "reward_scorer.py")

    # --- rubric.json (convert list to dict) ---
    rubric_dict = {}
    if isinstance(rubric, list):
        for i, criterion in enumerate(rubric):
            if isinstance(criterion, dict):
                rubric_dict[f"criterion {i+1}"] = criterion
            else:
                rubric_dict[f"criterion {i+1}"] = {"description": str(criterion)}
    (task_dir / "tests" / "rubric.json").write_text(json.dumps(rubric_dict, indent=2))

    # --- keywords.json ---
    keywords = extract_keywords(rubric) if rubric else []
    (task_dir / "tests" / "keywords.json").write_text(json.dumps(keywords, indent=2))

    # --- solution/solve.sh ---
    gold = task.get("gold_response", "")
    if gold:
        solve = f'#!/bin/bash\ncat > /app/output/answer.txt << \'GOLD_EOF\'\n{gold[:5000]}\nGOLD_EOF\n'
    else:
        solve = '#!/bin/bash\necho "No oracle" > /app/output/answer.txt\n'
    (task_dir / "solution" / "solve.sh").write_text(solve)
    os.chmod(task_dir / "solution" / "solve.sh", 0o755)

    return task_name, files_copied, num_criteria, difficulty


def main():
    parser = argparse.ArgumentParser(description="Convert apex-agents to Harbor eval format")
    parser.add_argument("--domain", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--skip-unzip", action="store_true")
    args = parser.parse_args()

    # Load tasks
    tasks_file = REPO_DIR / "tasks_and_rubrics.json"
    if not tasks_file.exists():
        print(f"ERROR: {tasks_file} not found. Run download_apex_files.py first.")
        return

    with open(tasks_file) as f:
        tasks = json.load(f)

    if args.domain:
        tasks = [t for t in tasks if args.domain.lower() in t["domain"].lower()]
        print(f"Filtered to {len(tasks)} {args.domain} tasks")

    # Unzip worlds
    if not args.skip_unzip:
        worlds_dir = unzip_worlds(REPO_DIR)
    else:
        worlds_dir = REPO_DIR.parent / "worlds_extracted"

    task_files_dir = REPO_DIR / "task_files"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Converting {len(tasks)} eval tasks to Harbor format ===\n")

    stats = {"total": 0, "with_files": 0, "by_domain": {}, "by_difficulty": {}}

    for task in tasks:
        name, files, criteria, difficulty = generate_eval_task(
            task, worlds_dir, task_files_dir, args.output_dir
        )
        stats["total"] += 1
        if files > 0:
            stats["with_files"] += 1

        domain = task["domain"]
        stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
        stats["by_difficulty"][difficulty] = stats["by_difficulty"].get(difficulty, 0) + 1

        marker = "+" if files > 0 else " "
        print(f"  {marker} {name} — {criteria} criteria, {files} files, {difficulty}")

    print(f"\n=== Done: {stats['total']} eval tasks ===")
    print(f"  With files: {stats['with_files']}")
    print(f"  By domain: {stats['by_domain']}")
    print(f"  By difficulty: {stats['by_difficulty']}")


if __name__ == "__main__":
    main()
