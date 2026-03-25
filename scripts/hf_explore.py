#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HuggingFace Dataset Explorer CLI

Search, preview, and download datasets from the Hugging Face Hub.

Usage:
    python scripts/hf_explore.py search "tool calling" --limit 20
    python scripts/hf_explore.py preview nvidia/Nemotron-Agentic-v1 --rows 5
    python scripts/hf_explore.py download nvidia/Nemotron-Agentic-v1 --output ./data/
"""

import argparse
import json
import sys
import os
from datetime import datetime

try:
    from huggingface_hub import HfApi, list_datasets
except ImportError:
    print("Error: huggingface_hub not installed. Run: pip install huggingface_hub")
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    print("Error: tabulate not installed. Run: pip install tabulate")
    sys.exit(1)


def format_size(size_bytes):
    """Format byte count into human-readable string."""
    if size_bytes is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_number(n):
    """Format large numbers with K/M suffixes."""
    if n is None:
        return "N/A"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_date(dt):
    """Format datetime to readable string."""
    if dt is None:
        return "N/A"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def cmd_search(args):
    """Search HuggingFace datasets by keyword."""
    try:
        api = HfApi()
        results = list(api.list_datasets(
            search=args.query,
            sort="downloads",
            limit=args.limit,
        ))
    except Exception as e:
        print(f"Error searching datasets: {e}")
        sys.exit(1)

    if not results:
        print(f"No datasets found for query: '{args.query}'")
        return

    rows = []
    for ds in results:
        rows.append({
            "name": ds.id,
            "downloads": format_number(getattr(ds, "downloads", None)),
            "likes": format_number(getattr(ds, "likes", None)),
            "size": format_size(getattr(ds, "size_categories", None) if False else getattr(ds, "cardData", {}).get("dataset_size") if isinstance(getattr(ds, "cardData", None), dict) else None),
            "license": _extract_license(ds),
            "last_modified": format_date(getattr(ds, "lastModified", None)),
        })

    _output(rows, args.format,
            headers=["name", "downloads", "likes", "size", "license", "last_modified"])


def _extract_license(ds):
    """Pull license string from dataset info."""
    tags = getattr(ds, "tags", []) or []
    for tag in tags:
        if tag.startswith("license:"):
            return tag.split(":", 1)[1]
    return "N/A"


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def cmd_preview(args):
    """Preview a dataset — schema, sample rows, stats."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: datasets library not installed. Run: pip install datasets")
        sys.exit(1)

    dataset_id = args.dataset
    split = args.split
    rows = args.rows

    print(f"Loading dataset: {dataset_id} ...")

    try:
        # Try streaming first to avoid downloading the whole thing
        ds = load_dataset(dataset_id, split=split, streaming=True, trust_remote_code=True)
        # Grab sample rows
        samples = []
        for i, row in enumerate(ds):
            if i >= rows:
                break
            samples.append(row)

        if not samples:
            print("Dataset appears to be empty.")
            return

        # Schema info
        features = ds.features
        print(f"\n{'='*60}")
        print(f"Dataset: {dataset_id}  |  Split: {split}")
        print(f"{'='*60}")

        print(f"\n## Schema ({len(features)} columns)")
        schema_rows = []
        for col_name, col_type in features.items():
            schema_rows.append({"column": col_name, "dtype": str(col_type)})
        print(tabulate(schema_rows, headers="keys", tablefmt="simple"))

        # Try to get row count (non-streaming)
        try:
            info = HfApi().dataset_info(dataset_id)
            card = getattr(info, "cardData", {}) or {}
            if "dataset_size" in card:
                print(f"\nDataset size: {format_size(card['dataset_size'])}")
        except Exception:
            pass

        # Sample rows
        print(f"\n## Sample Rows ({len(samples)} shown)")
        # Truncate long values for display
        display_rows = []
        for row in samples:
            display_row = {}
            for k, v in row.items():
                s = str(v)
                display_row[k] = s[:120] + "..." if len(s) > 120 else s
            display_rows.append(display_row)

        if args.format == "json":
            print(json.dumps(samples, indent=2, default=str))
        elif args.format == "csv":
            import csv, io
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=display_rows[0].keys())
            writer.writeheader()
            writer.writerows(display_rows)
            print(buf.getvalue())
        else:
            print(tabulate(display_rows, headers="keys", tablefmt="simple", maxcolwidths=60))

    except Exception as e:
        print(f"Error loading dataset '{dataset_id}': {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def cmd_download(args):
    """Download a dataset to local storage."""
    try:
        from datasets import load_dataset
    except ImportError:
        print("Error: datasets library not installed. Run: pip install datasets")
        sys.exit(1)

    dataset_id = args.dataset
    output_dir = args.output
    split = args.split

    os.makedirs(output_dir, exist_ok=True)

    print(f"Downloading dataset: {dataset_id} (split={split or 'all'}) ...")
    print(f"Output directory: {os.path.abspath(output_dir)}")

    try:
        kwargs = {"trust_remote_code": True}
        if split:
            kwargs["split"] = split

        ds = load_dataset(dataset_id, **kwargs)

        # Save based on format
        safe_name = dataset_id.replace("/", "__")
        fmt = args.format

        if hasattr(ds, "keys"):
            # DatasetDict with multiple splits
            for split_name in ds.keys():
                _save_split(ds[split_name], output_dir, safe_name, split_name, fmt)
        else:
            split_label = split or "train"
            _save_split(ds, output_dir, safe_name, split_label, fmt)

        print(f"\nDone. Files saved to {os.path.abspath(output_dir)}")

    except Exception as e:
        print(f"Error downloading dataset '{dataset_id}': {e}")
        sys.exit(1)


def _save_split(ds, output_dir, safe_name, split_name, fmt):
    """Save a single split to disk."""
    if fmt == "json":
        path = os.path.join(output_dir, f"{safe_name}__{split_name}.jsonl")
        ds.to_json(path)
    elif fmt == "csv":
        path = os.path.join(output_dir, f"{safe_name}__{split_name}.csv")
        ds.to_csv(path)
    else:
        # Default to parquet
        path = os.path.join(output_dir, f"{safe_name}__{split_name}.parquet")
        ds.to_parquet(path)

    row_count = len(ds)
    file_size = format_size(os.path.getsize(path))
    print(f"  Saved {split_name}: {row_count} rows, {file_size} -> {path}")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _output(rows, fmt, headers):
    """Print rows in the requested format."""
    if fmt == "json":
        print(json.dumps(rows, indent=2, default=str))
    elif fmt == "csv":
        import csv, io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
        print(buf.getvalue())
    else:
        print(tabulate(rows, headers="keys", tablefmt="simple"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="HuggingFace Dataset Explorer CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s search "tool calling" --limit 20
  %(prog)s preview nvidia/Nemotron-Agentic-v1 --rows 5
  %(prog)s download nvidia/Nemotron-Agentic-v1 --output ./data/
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- search ---
    sp_search = subparsers.add_parser("search", help="Search datasets by keyword")
    sp_search.add_argument("query", help="Search query string")
    sp_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    sp_search.add_argument("--format", choices=["table", "json", "csv"], default="table",
                           help="Output format (default: table)")
    sp_search.set_defaults(func=cmd_search)

    # --- preview ---
    sp_preview = subparsers.add_parser("preview", help="Preview a dataset (schema + samples)")
    sp_preview.add_argument("dataset", help="Dataset ID (e.g. nvidia/Nemotron-Agentic-v1)")
    sp_preview.add_argument("--rows", type=int, default=5, help="Number of sample rows (default: 5)")
    sp_preview.add_argument("--split", default="train", help="Dataset split (default: train)")
    sp_preview.add_argument("--format", choices=["table", "json", "csv"], default="table",
                           help="Output format (default: table)")
    sp_preview.set_defaults(func=cmd_preview)

    # --- download ---
    sp_download = subparsers.add_parser("download", help="Download a dataset to local storage")
    sp_download.add_argument("dataset", help="Dataset ID (e.g. nvidia/Nemotron-Agentic-v1)")
    sp_download.add_argument("--output", default="./data/", help="Output directory (default: ./data/)")
    sp_download.add_argument("--split", default=None, help="Specific split to download (default: all)")
    sp_download.add_argument("--format", choices=["table", "json", "csv"], default="table",
                           help="Save format: table=parquet, json=jsonl, csv=csv (default: table/parquet)")
    sp_download.set_defaults(func=cmd_download)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
