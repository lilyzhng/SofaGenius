# /hf-explore

HuggingFace Dataset Explorer CLI tool for searching, previewing, and downloading datasets from the Hugging Face Hub.

## Location

`scripts/hf_explore.py`

## Dependencies

```bash
pip install huggingface_hub datasets tabulate
```

## Commands

### Search

Find datasets by keyword, sorted by downloads.

```bash
python scripts/hf_explore.py search "tool calling" --limit 20
python scripts/hf_explore.py search "agentic" --limit 5 --format json
```

**Options:**
- `--limit N` — Max results (default: 10)
- `--format table|json|csv` — Output format (default: table)

**Output columns:** name, downloads, likes, size, license, last_modified

### Preview

Inspect a dataset without downloading it fully (uses streaming).

```bash
python scripts/hf_explore.py preview nvidia/Nemotron-Agentic-v1 --rows 5
python scripts/hf_explore.py preview openai/gsm8k --rows 3 --split test --format json
```

**Options:**
- `--rows N` — Number of sample rows (default: 5)
- `--split SPLIT` — Dataset split (default: train)
- `--format table|json|csv` — Output format (default: table)

**Output:** schema (column names + dtypes), dataset size, sample rows

### Download

Download a dataset to local disk as parquet, JSONL, or CSV.

```bash
python scripts/hf_explore.py download nvidia/Nemotron-Agentic-v1 --output ./data/
python scripts/hf_explore.py download openai/gsm8k --output ./data/ --split train --format json
```

**Options:**
- `--output DIR` — Output directory (default: `./data/`)
- `--split SPLIT` — Specific split to download; omit for all splits
- `--format table|json|csv` — Save format: table=parquet, json=jsonl, csv=csv (default: parquet)

## Typical Workflow

```bash
# 1. Search for relevant datasets
python scripts/hf_explore.py search "multi-turn tool calling" --limit 20

# 2. Preview promising ones
python scripts/hf_explore.py preview glaiveai/glaive-function-calling-v2 --rows 3

# 3. Download the best candidate
python scripts/hf_explore.py download glaiveai/glaive-function-calling-v2 --output ./data/
```

## Notes

- Preview uses streaming mode to avoid downloading entire datasets
- Search results are sorted by download count (most popular first)
- The `--format` flag on download controls the file format (parquet by default)
- Handles errors gracefully: missing datasets, network issues, empty results
