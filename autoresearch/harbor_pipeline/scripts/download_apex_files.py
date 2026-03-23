"""
Download all APEX dataset files for Harbor task conversion.

Downloads:
1. mercor/APEX-v1-extended (100 tasks, CC-BY-4.0, trainable)
   - documents/ directory with PDFs
   - dataset rows with prompts + rubrics

2. mercor/apex-agents (480 tasks, eval-only)
   - world_files_zipped/ (33 world zips)
   - task_files/ (222 task folders)
   - metadata (world_descriptions.json, tasks_and_rubrics.json)

Usage:
    python scripts/download_apex_files.py --output-dir data/apex
    python scripts/download_apex_files.py --training-only  # skip eval data
"""

import argparse
import json
import zipfile
from pathlib import Path

from datasets import load_dataset
from huggingface_hub import snapshot_download


def download_v1_extended(output_dir: Path):
    """Download APEX-v1-extended (100 trainable tasks + PDFs)."""
    print("=== Downloading APEX-v1-extended (training) ===")

    dest = output_dir / "v1-extended"
    dest.mkdir(parents=True, exist_ok=True)

    # Download full repo (includes documents/ with PDFs)
    repo_path = snapshot_download(
        repo_id="mercor/APEX-v1-extended",
        repo_type="dataset",
        local_dir=dest / "repo",
    )
    print(f"  Downloaded to: {repo_path}")

    # Also load as dataset for structured access
    ds = load_dataset("mercor/APEX-v1-extended", split="train")
    print(f"  Loaded {len(ds)} tasks")

    # Save as JSON for easy access
    tasks = []
    for row in ds:
        tasks.append({
            "task_id": row.get("Task_ID"),
            "domain": row.get("Domain"),
            "prompt": row.get("Prompt"),
            "rubric_json": row.get("Rubric_JSON"),
            "file_attachments": row.get("File_Attachments"),
        })

    tasks_file = dest / "tasks.json"
    with open(tasks_file, "w") as f:
        json.dump(tasks, f, indent=2)
    print(f"  Saved {len(tasks)} tasks to {tasks_file}")

    # Check documents
    docs_dir = dest / "repo" / "documents"
    if docs_dir.exists():
        pdf_count = len(list(docs_dir.rglob("*.pdf")))
        print(f"  Found {pdf_count} PDFs in documents/")
    else:
        print("  WARNING: documents/ directory not found")

    return dest


def download_apex_agents(output_dir: Path):
    """Download apex-agents (480 eval tasks + world files)."""
    print("\n=== Downloading apex-agents (evaluation) ===")

    dest = output_dir / "apex-agents"
    dest.mkdir(parents=True, exist_ok=True)

    # Download full repo (includes world_files_zipped/, task_files/, metadata)
    repo_path = snapshot_download(
        repo_id="mercor/apex-agents",
        repo_type="dataset",
        local_dir=dest / "repo",
    )
    print(f"  Downloaded to: {repo_path}")

    # Check world zips
    world_dir = dest / "repo" / "world_files_zipped"
    if world_dir.exists():
        zips = list(world_dir.glob("*.zip"))
        print(f"  Found {len(zips)} world zip files")
        total_size = sum(z.stat().st_size for z in zips)
        print(f"  Total size: {total_size / 1e9:.2f} GB")
    else:
        print("  WARNING: world_files_zipped/ not found")

    # Check task files
    task_dir = dest / "repo" / "task_files"
    if task_dir.exists():
        task_folders = [d for d in task_dir.iterdir() if d.is_dir()]
        print(f"  Found {len(task_folders)} task file folders")
    else:
        print("  WARNING: task_files/ not found")

    # Load metadata
    for meta_file in ["tasks_and_rubrics.json", "world_descriptions.json"]:
        meta_path = dest / "repo" / meta_file
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
            print(f"  {meta_file}: {len(data)} entries")
        else:
            print(f"  WARNING: {meta_file} not found")

    return dest


def unzip_worlds(apex_agents_dir: Path):
    """Unzip all world files for easy access."""
    world_dir = apex_agents_dir / "repo" / "world_files_zipped"
    extract_dir = apex_agents_dir / "worlds_extracted"
    extract_dir.mkdir(exist_ok=True)

    if not world_dir.exists():
        print("  No world zips to extract")
        return

    zips = list(world_dir.glob("*.zip"))
    print(f"\n=== Extracting {len(zips)} world zips ===")

    for i, zf in enumerate(sorted(zips)):
        world_name = zf.stem
        dest = extract_dir / world_name
        if dest.exists():
            print(f"  [{i+1}/{len(zips)}] {world_name} — already extracted")
            continue

        print(f"  [{i+1}/{len(zips)}] {world_name} ({zf.stat().st_size / 1e6:.1f} MB)...")
        try:
            with zipfile.ZipFile(zf, "r") as z:
                z.extractall(dest)
            file_count = len(list(dest.rglob("*")))
            print(f"    → {file_count} files extracted")
        except Exception as e:
            print(f"    ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download APEX datasets for Harbor conversion")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/Users/lilyzhang/Documents/lilyzhng/claude/builder/data/apex"),
        help="Output directory",
    )
    parser.add_argument(
        "--training-only",
        action="store_true",
        help="Only download training data (v1-extended), skip eval",
    )
    parser.add_argument(
        "--skip-unzip",
        action="store_true",
        help="Skip unzipping world files",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Download training data
    v1_dir = download_v1_extended(args.output_dir)

    # Step 2: Download eval data
    if not args.training_only:
        agents_dir = download_apex_agents(args.output_dir)

        # Step 3: Unzip world files
        if not args.skip_unzip:
            unzip_worlds(agents_dir)
    else:
        print("\n  Skipping eval data (--training-only)")

    print("\n=== Done ===")
    print(f"  Output: {args.output_dir}")


if __name__ == "__main__":
    main()
