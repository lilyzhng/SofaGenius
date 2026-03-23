"""
Verify generated Harbor tasks are correctly structured.

Checks:
1. Directory structure (all required files present)
2. File attachments exist
3. Rubric JSON is valid
4. Keywords extracted
5. (Optional) Run oracle + test.sh to confirm reward

Usage:
    python scripts/verify_harbor_tasks.py --quick           # structure only
    python scripts/verify_harbor_tasks.py --domain finance   # single domain
    python scripts/verify_harbor_tasks.py --sample 5         # check N random tasks in detail
"""

import argparse
import json
import sys
from pathlib import Path

TASKS_DIR = Path(__file__).parent.parent / "tasks"

REQUIRED_FILES = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "tests/test.sh",
    "tests/reward_scorer.py",
    "tests/rubric.json",
    "tests/keywords.json",
    "solution/solve.sh",
]


def check_structure(task_dir: Path) -> list[str]:
    """Check all required files exist. Returns list of issues."""
    issues = []
    for rel_path in REQUIRED_FILES:
        full_path = task_dir / rel_path
        if not full_path.exists():
            issues.append(f"Missing: {rel_path}")
        elif full_path.stat().st_size == 0:
            issues.append(f"Empty: {rel_path}")
    return issues


def check_data(task_dir: Path) -> dict:
    """Check data files and rubric."""
    info = {}

    # Data files
    data_dir = task_dir / "environment" / "data"
    if data_dir.exists():
        files = list(data_dir.iterdir())
        info["data_files"] = len(files)
        info["data_size_mb"] = round(sum(f.stat().st_size for f in files) / 1e6, 2)
    else:
        info["data_files"] = 0
        info["data_size_mb"] = 0

    # Rubric
    rubric_path = task_dir / "tests" / "rubric.json"
    try:
        with open(rubric_path) as f:
            rubric = json.load(f)
        info["criteria"] = len(rubric)
        info["rubric_valid"] = True
    except Exception as e:
        info["criteria"] = 0
        info["rubric_valid"] = False
        info["rubric_error"] = str(e)

    # Keywords
    kw_path = task_dir / "tests" / "keywords.json"
    try:
        with open(kw_path) as f:
            keywords = json.load(f)
        info["keywords"] = len(keywords)
    except Exception:
        info["keywords"] = 0

    # Instruction length
    instr_path = task_dir / "instruction.md"
    if instr_path.exists():
        info["instruction_chars"] = len(instr_path.read_text())

    return info


def main():
    parser = argparse.ArgumentParser(description="Verify Harbor tasks")
    parser.add_argument("--tasks-dir", type=Path, default=TASKS_DIR)
    parser.add_argument("--domain", type=str, default=None)
    parser.add_argument("--quick", action="store_true", help="Structure check only")
    parser.add_argument("--sample", type=int, default=0, help="Detailed check on N tasks")
    args = parser.parse_args()

    if not args.tasks_dir.exists():
        print(f"ERROR: {args.tasks_dir} not found")
        sys.exit(1)

    task_dirs = sorted(args.tasks_dir.iterdir())
    if args.domain:
        task_dirs = [d for d in task_dirs if args.domain.lower() in d.name]

    print(f"=== Verifying {len(task_dirs)} Harbor tasks ===\n")

    # Structure check
    ok = 0
    issues_total = 0
    domain_counts = {}
    difficulty_counts = {}

    for td in task_dirs:
        if not td.is_dir():
            continue

        issues = check_structure(td)

        # Parse domain from name
        parts = td.name.split("-")
        domain = parts[1] if len(parts) >= 3 else "unknown"
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        # Parse difficulty from task.toml
        toml_path = td / "task.toml"
        if toml_path.exists():
            for line in toml_path.read_text().split("\n"):
                if line.startswith("difficulty"):
                    diff = line.split("=")[1].strip().strip('"')
                    difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

        if issues:
            print(f"  ✗ {td.name}: {', '.join(issues)}")
            issues_total += len(issues)
        else:
            ok += 1

    print(f"\n  Structure: {ok}/{len(task_dirs)} OK")
    if issues_total:
        print(f"  Issues: {issues_total}")
    print(f"  Domains: {domain_counts}")
    print(f"  Difficulty: {difficulty_counts}")

    if args.quick:
        sys.exit(0 if issues_total == 0 else 1)

    # Detailed check
    import random
    sample_dirs = task_dirs
    if args.sample > 0:
        sample_dirs = random.sample(task_dirs, min(args.sample, len(task_dirs)))

    print(f"\n=== Detailed check on {len(sample_dirs)} tasks ===\n")

    for td in sample_dirs:
        if not td.is_dir():
            continue
        info = check_data(td)
        status = "✓" if info.get("rubric_valid") and info["data_files"] > 0 else "!"
        print(f"  {status} {td.name}")
        print(f"    Data: {info['data_files']} files ({info['data_size_mb']} MB)")
        print(f"    Rubric: {info['criteria']} criteria, valid={info.get('rubric_valid')}")
        print(f"    Keywords: {info['keywords']}")
        print(f"    Instruction: {info.get('instruction_chars', 0)} chars")
        print()

    # Summary stats
    all_info = [check_data(td) for td in task_dirs if td.is_dir()]
    total_files = sum(i["data_files"] for i in all_info)
    total_criteria = sum(i["criteria"] for i in all_info)
    avg_criteria = total_criteria / max(len(all_info), 1)
    total_keywords = sum(i["keywords"] for i in all_info)

    print(f"=== Summary ===")
    print(f"  Total data files: {total_files}")
    print(f"  Total criteria: {total_criteria} (avg {avg_criteria:.1f}/task)")
    print(f"  Total keywords: {total_keywords}")


if __name__ == "__main__":
    main()
