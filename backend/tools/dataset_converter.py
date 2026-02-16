"""Dataset format detection and conversion preview tool.

Lightweight: streams a handful of rows to detect format and preview
conversion. No full download or Hub push — the actual conversion
happens on-the-fly at training time using the same row converters.
"""

from __future__ import annotations

import json
from typing import Any

from datasets import load_dataset

PREVIEW_ROWS = 10


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def _detect_format(sample_rows: list[dict[str, Any]], columns: list[str]) -> str:
    """Detect the dataset format from column names and sample values.

    Returns one of: chatml, instruction, qa, completion, preference, unknown.
    """
    col_set = set(columns)

    # ChatML: messages column with list of {role, content} dicts
    if "messages" in col_set:
        for row in sample_rows:
            msgs = row.get("messages")
            if isinstance(msgs, list) and len(msgs) > 0:
                first = msgs[0]
                if isinstance(first, dict) and "role" in first and "content" in first:
                    return "chatml"

    # Preference: chosen + rejected columns
    if "chosen" in col_set and "rejected" in col_set:
        return "preference"

    # Instruction: instruction + output columns
    if "instruction" in col_set and "output" in col_set:
        return "instruction"

    # QA: question + answer columns
    if "question" in col_set and "answer" in col_set:
        return "qa"

    # Completion: text column
    if "text" in col_set:
        return "completion"

    return "unknown"


# ---------------------------------------------------------------------------
# Row converters (also used at training time for on-the-fly conversion)
# ---------------------------------------------------------------------------

def convert_row_to_base(row: dict[str, Any], source_format: str) -> dict[str, str]:
    """Convert a single row to base/completion format ({text: "..."})."""
    if source_format == "completion":
        return {"text": str(row.get("text", ""))}

    if source_format == "chatml":
        parts = []
        for msg in row.get("messages", []):
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            parts.append(f"### {role}\n{content}")
        return {"text": "\n\n".join(parts)}

    if source_format == "instruction":
        instruction = row.get("instruction", "")
        inp = row.get("input", "")
        output = row.get("output", "")
        user_part = f"{instruction}\n{inp}".strip() if inp else instruction
        return {"text": f"### User\n{user_part}\n\n### Assistant\n{output}"}

    if source_format == "qa":
        question = row.get("question", "")
        answer = row.get("answer", "")
        return {"text": f"### User\n{question}\n\n### Assistant\n{answer}"}

    # Fallback: concatenate all string values
    parts = [str(v) for v in row.values() if isinstance(v, str)]
    return {"text": "\n\n".join(parts)}


def convert_row_to_chatml(row: dict[str, Any], source_format: str) -> dict[str, list[dict[str, str]]]:
    """Convert a single row to ChatML format ({messages: [...]})."""
    if source_format == "chatml":
        return {"messages": row.get("messages", [])}

    if source_format == "instruction":
        instruction = row.get("instruction", "")
        inp = row.get("input", "")
        output = row.get("output", "")
        user_content = f"{instruction}\n{inp}".strip() if inp else instruction
        return {"messages": [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": output},
        ]}

    if source_format == "qa":
        return {"messages": [
            {"role": "user", "content": row.get("question", "")},
            {"role": "assistant", "content": row.get("answer", "")},
        ]}

    if source_format == "completion":
        return {"messages": [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": str(row.get("text", ""))},
        ]}

    # Fallback
    text = " ".join(str(v) for v in row.values() if isinstance(v, str))
    return {"messages": [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": text},
    ]}


def get_converter(target_format: str):
    """Return the row converter function for a target format."""
    if target_format == "base":
        return convert_row_to_base
    return convert_row_to_chatml


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def _stream_samples(dataset_path: str, split: str, n: int) -> list[dict[str, Any]]:
    """Stream *n* rows from a HF dataset without downloading the whole thing."""
    ds = load_dataset(dataset_path, split=split, streaming=True)
    samples: list[dict[str, Any]] = []
    for i, row in enumerate(ds):
        if i >= n:
            break
        samples.append(row)
    return samples


def _truncate_sample(row: dict[str, Any], limit: int = 500) -> dict[str, str]:
    truncated: dict[str, str] = {}
    for k, v in row.items():
        s = str(v)
        truncated[k] = s[:limit] + "..." if len(s) > limit else s
    return truncated


def inspect_dataset_format(dataset_path: str, split: str = "train") -> str:
    """Load a few rows from HF (streaming) and detect the dataset format.

    Returns JSON with format name, columns, and sample rows.
    """
    try:
        samples = _stream_samples(dataset_path, split, 5)

        if not samples:
            return json.dumps({"error": "Dataset is empty or could not be loaded"})

        columns = list(samples[0].keys())
        fmt = _detect_format(samples, columns)

        display_samples = [_truncate_sample(row, 300) for row in samples[:2]]

        return json.dumps({
            "dataset_path": dataset_path,
            "split": split,
            "format": fmt,
            "columns": columns,
            "sample_rows": display_samples,
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to inspect dataset: {e}"})


def convert_dataset(
    dataset_path: str,
    target_format: str,
    split: str = "train",
) -> str:
    """Preview a format conversion by streaming a handful of rows.

    Streams PREVIEW_ROWS rows, detects format, converts them, and returns
    a ConversionCard with before/after samples.  Does NOT download the
    full dataset or push anything to Hub — the real conversion happens
    on-the-fly at training time.

    target_format: "base" (completion) or "chatml"
    """
    try:
        if target_format not in ("base", "chatml"):
            return json.dumps({"error": f"Unsupported target format: {target_format}. Use 'base' or 'chatml'."})

        samples = _stream_samples(dataset_path, split, PREVIEW_ROWS)
        if not samples:
            return json.dumps({"error": "Dataset is empty or could not be loaded"})

        columns = list(samples[0].keys())
        source_format = _detect_format(samples, columns)

        if source_format == "unknown":
            return json.dumps({"error": f"Cannot detect source format. Columns: {columns}"})

        # Check for no-op
        if source_format == "completion" and target_format == "base":
            return json.dumps({"error": "Dataset is already in completion/base format. No conversion needed."})
        if source_format == "chatml" and target_format == "chatml":
            return json.dumps({"error": "Dataset is already in ChatML format. No conversion needed."})

        converter = get_converter(target_format)

        # Convert preview rows
        converted = [converter(row, source_format) for row in samples]

        # Build before/after display samples (first 3)
        before_samples = [_truncate_sample(row) for row in samples[:3]]
        after_samples = [_truncate_sample(row) for row in converted[:3]]

        return json.dumps({
            "card_type": "conversion_card",
            "title": f"Preview: {dataset_path} as {target_format}",
            "source_dataset": dataset_path,
            "source_format": source_format,
            "target_format": target_format,
            "preview_count": len(converted),
            "source_columns": columns,
            "before_samples": before_samples,
            "after_samples": after_samples,
        })
    except Exception as e:
        return json.dumps({"error": f"Conversion preview failed: {e}"})
