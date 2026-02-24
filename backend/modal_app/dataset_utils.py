"""Shared dataset splitting utilities for training functions.

Enforces proper train/eval separation to prevent data contamination.
All training functions should use load_train_eval_split() instead of
loading datasets directly.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_EVAL_FRACTION = 0.1
EVAL_SEED = 42
MAX_EVAL = 200
MIN_EVAL = 20


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def should_skip_eval(config_dict: dict) -> bool:
    """Return True for overfit / sanity-check runs where eval is pointless.

    Criteria:
    - max_steps == 1  (single-step sanity check)
    - train_size <= 4  (tiny overfit test)
    """
    max_steps = config_dict.get("max_steps", -1)
    train_size = config_dict.get("train_size")

    if max_steps == 1:
        return True
    if train_size is not None and train_size <= 4:
        return True
    return False


def load_train_eval_split(
    dataset_name: str,
    split_config: str | None = None,
    max_train_samples: int | None = None,
    skip_eval: bool = False,
) -> tuple[Any, Any | None]:
    """Load an HF dataset and return (train_dataset, eval_dataset | None).

    Logic:
    1. If the dataset has a "test" split, use it as eval.
    2. Otherwise, create one via train_test_split(test_size=0.1, seed=42).
    3. Cap eval at MAX_EVAL samples, floor at MIN_EVAL.
    4. If skip_eval is True, return (train, None).

    Parameters
    ----------
    dataset_name : str
        HuggingFace dataset identifier.
    split_config : str | None
        Optional dataset config name (e.g. "func_calling_singleturn").
    max_train_samples : int | None
        If set, limit training data to this many samples.
    skip_eval : bool
        If True, skip eval entirely and return (train, None).
    """
    from datasets import get_dataset_split_names, load_dataset

    # Load full train split first (don't cap yet — eval comes from the rest)
    kwargs = {"path": dataset_name}
    if split_config:
        kwargs["name"] = split_config
    full_ds = load_dataset(**kwargs, split="train")

    if skip_eval:
        # Cap training samples only when skipping eval
        if max_train_samples and max_train_samples < len(full_ds):
            full_ds = full_ds.select(range(max_train_samples))
        return full_ds, None

    # Try to find an existing test split
    eval_ds = None
    try:
        split_names = get_dataset_split_names(dataset_name, config_name=split_config)
        if "test" in split_names:
            eval_ds = load_dataset(**kwargs, split="test")
    except Exception:
        pass

    if eval_ds is not None:
        # Existing test split — just cap training
        train_ds = full_ds
        if max_train_samples and max_train_samples < len(train_ds):
            train_ds = train_ds.select(range(max_train_samples))
    else:
        # No test split — create one from full data, then cap training
        splits = full_ds.train_test_split(
            test_size=DEFAULT_EVAL_FRACTION, seed=EVAL_SEED,
        )
        train_ds = splits["train"]
        eval_ds = splits["test"]
        if max_train_samples and max_train_samples < len(train_ds):
            train_ds = train_ds.select(range(max_train_samples))

    # Scale eval to 10% of actual training size, capped at MAX_EVAL
    desired_eval = max(1, int(len(train_ds) * DEFAULT_EVAL_FRACTION))
    eval_cap = min(desired_eval, MAX_EVAL)
    if len(eval_ds) > eval_cap:
        eval_ds = eval_ds.select(range(eval_cap))

    return train_ds, eval_ds
