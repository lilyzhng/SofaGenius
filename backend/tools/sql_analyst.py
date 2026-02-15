"""SQL analyst tools — query HuggingFace datasets via DuckDB's hf:// protocol."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

import duckdb

from backend.models import (
    ColumnInfo,
    DataCard,
    PlotData,
    QueryResult,
    StatsSummary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Common HF dataset splits in order of preference
_SPLITS = ["train", "test", "validation"]


def _conn() -> duckdb.DuckDBPyConnection:
    """Create a fresh in-memory DuckDB connection to avoid shared transaction state."""
    return duckdb.connect()


def _normalize_hf_path(dataset_path: str) -> str:
    """Turn 'user/dataset' into 'hf://datasets/user/dataset/train.parquet'.

    If the path already starts with hf:// or contains .parquet, return as-is.
    Tries train split first; falls back to test / validation.
    """
    if dataset_path.startswith("hf://") or ".parquet" in dataset_path:
        return dataset_path

    # Strip leading/trailing whitespace and slashes
    dataset_path = dataset_path.strip().strip("/")

    # Try each split — DuckDB will error on missing files, so we probe
    con = _conn()
    for split in _SPLITS:
        path = f"hf://datasets/{dataset_path}/{split}.parquet"
        try:
            con.sql(f"SELECT 1 FROM '{path}' LIMIT 1")
            con.close()
            return path
        except Exception:
            continue

    # Fallback: try wildcard for all parquet files in the dataset
    wildcard = f"hf://datasets/{dataset_path}/**/*.parquet"
    try:
        con.sql(f"SELECT 1 FROM '{wildcard}' LIMIT 1")
        con.close()
        return wildcard
    except Exception:
        pass

    con.close()
    # Last resort — return train.parquet and let the caller handle errors
    return f"hf://datasets/{dataset_path}/train.parquet"


def _is_select_only(sql: str) -> bool:
    """Reject anything that isn't a SELECT or DESCRIBE/SHOW statement."""
    normalized = sql.strip().upper()
    return normalized.startswith(("SELECT", "DESCRIBE", "SHOW", "WITH", "EXPLAIN"))


def _inject_limit(sql: str, limit: int = 1000) -> str:
    """Add LIMIT clause if the query doesn't already have one."""
    upper = sql.strip().upper()
    if "LIMIT" not in upper:
        return sql.rstrip("; \n") + f" LIMIT {limit}"
    return sql


# ---------------------------------------------------------------------------
# Tool 0: search_hf_datasets
# ---------------------------------------------------------------------------


def search_hf_datasets(query: str, limit: int = 10) -> str:
    """Search HuggingFace Hub for datasets matching a query."""
    params = urllib.parse.urlencode({
        "search": query,
        "sort": "downloads",
        "direction": "-1",
        "limit": min(limit, 20),
    })
    url = f"https://huggingface.co/api/datasets?{params}"

    headers = {"Accept": "application/json"}
    token = os.environ.get("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read().decode())
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})

    results = []
    for ds in raw:
        results.append({
            "id": ds.get("id", ""),
            "description": (ds.get("description") or "")[:200],
            "downloads": ds.get("downloads", 0),
            "likes": ds.get("likes", 0),
            "tags": ds.get("tags", [])[:10],
            "last_modified": ds.get("lastModified", ""),
            "url": f"https://huggingface.co/datasets/{ds.get('id', '')}",
        })

    return json.dumps({"query": query, "count": len(results), "datasets": results})


# ---------------------------------------------------------------------------
# Tool 1: discover_dataset_schema
# ---------------------------------------------------------------------------


def discover_dataset_schema(dataset_path: str) -> str:
    """Discover columns, types, sample values, and row count for an HF dataset."""
    path = _normalize_hf_path(dataset_path)
    con = _conn()
    try:
        # Get schema via DESCRIBE
        desc = con.sql(f"DESCRIBE SELECT * FROM '{path}'").fetchall()
        # desc rows: (column_name, column_type, null, key, default, extra)

        # Sample 5 rows for preview values
        samples = con.sql(f"SELECT * FROM '{path}' LIMIT 5").fetchall()

        columns: list[dict] = []
        for i, row in enumerate(desc):
            col_name = row[0]
            col_type = row[1]
            sample_vals = [str(s[i]) if s[i] is not None else "null" for s in samples]
            columns.append(
                ColumnInfo(
                    name=col_name, type=col_type, sample_values=sample_vals
                ).model_dump()
            )

        # Row count (approximate — DuckDB is fast on parquet)
        count_result = con.sql(f"SELECT COUNT(*) FROM '{path}'").fetchone()
        row_count = count_result[0] if count_result else 0

        return json.dumps(
            {
                "dataset_path": dataset_path,
                "hf_path": path,
                "columns": columns,
                "row_count": row_count,
            }
        )
    except Exception as e:
        return json.dumps({"error": str(e), "dataset_path": dataset_path})
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tool 2: run_sql_query
# ---------------------------------------------------------------------------


def run_sql_query(dataset_path: str, sql_query: str) -> str:
    """Execute a read-only SQL query against an HF dataset via DuckDB."""
    if not _is_select_only(sql_query):
        return json.dumps({"error": "Only SELECT / DESCRIBE / SHOW queries are allowed."})

    path = _normalize_hf_path(dataset_path)

    # Replace dataset reference placeholders so the agent can write natural SQL.
    # The agent may reference the table as 'dataset', 'data', or the dataset name.
    # We replace it with the actual hf:// path.
    query = sql_query
    # Replace common table references with the actual path
    for placeholder in ["FROM dataset", "FROM data", "FROM tbl"]:
        if placeholder.upper() in query.upper():
            idx = query.upper().index(placeholder.upper())
            after = query[idx + len(placeholder):]
            query = query[:idx] + f"FROM '{path}'" + after
            break
    else:
        # If the query doesn't reference any of our placeholders,
        # check if it already has the hf:// path; if not, it likely
        # references the dataset by its HF name — try to replace that too.
        if "hf://" not in query:
            # Try to replace the dataset name itself
            ds_name = dataset_path.strip().strip("/")
            short_name = ds_name.split("/")[-1] if "/" in ds_name else ds_name
            for name in [ds_name, short_name]:
                pattern = re.compile(rf"FROM\s+['\"]?{re.escape(name)}['\"]?", re.IGNORECASE)
                if pattern.search(query):
                    query = pattern.sub(f"FROM '{path}'", query)
                    break

    query = _inject_limit(query)

    con = _conn()
    try:
        t0 = time.time()
        result = con.sql(query)
        elapsed_ms = (time.time() - t0) * 1000

        columns = [col[0] for col in result.description]
        rows = result.fetchall()

        truncated = len(rows) >= 1000
        qr = QueryResult(
            columns=columns,
            rows=[list(r) for r in rows],
            row_count=len(rows),
            execution_time_ms=round(elapsed_ms, 1),
            truncated=truncated,
        )
        return qr.model_dump_json()
    except Exception as e:
        return json.dumps({"error": str(e), "sql_query": sql_query})
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Tool 3: compute_stats
# ---------------------------------------------------------------------------


def compute_stats(query_result_json: str) -> str:
    """Compute per-column statistics from a QueryResult JSON string."""
    try:
        data = json.loads(query_result_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    columns = data.get("columns", [])
    rows = data.get("rows", [])

    if not columns or not rows:
        return json.dumps({"stats": [], "error": None})

    stats: list[dict] = []
    for col_idx, col_name in enumerate(columns):
        values = [row[col_idx] for row in rows if row[col_idx] is not None]
        if not values:
            continue

        # Check if numeric
        numeric_vals = []
        for v in values:
            if isinstance(v, (int, float)):
                numeric_vals.append(float(v))
            else:
                try:
                    numeric_vals.append(float(v))
                except (ValueError, TypeError):
                    pass

        if len(numeric_vals) > len(values) * 0.5:
            # Numeric column
            import numpy as np

            arr = np.array(numeric_vals)
            stats.append(
                StatsSummary(
                    column=col_name,
                    kind="numeric",
                    mean=round(float(np.mean(arr)), 4),
                    std=round(float(np.std(arr)), 4),
                    min=round(float(np.min(arr)), 4),
                    max=round(float(np.max(arr)), 4),
                ).model_dump()
            )
        else:
            # Categorical column
            str_vals = [str(v) for v in values]
            counter = Counter(str_vals)
            top = [
                {k: v} for k, v in counter.most_common(10)
            ]
            stats.append(
                StatsSummary(
                    column=col_name,
                    kind="categorical",
                    unique_count=len(counter),
                    top_values=top,
                ).model_dump()
            )

    return json.dumps({"stats": stats})


# ---------------------------------------------------------------------------
# Tool 4: generate_plot_data
# ---------------------------------------------------------------------------


def generate_plot_data(query_result_json: str, plot_type: str = "auto") -> str:
    """Generate plot data from a QueryResult. Auto-detects best plot type."""
    try:
        data = json.loads(query_result_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    columns = data.get("columns", [])
    rows = data.get("rows", [])

    if not columns or not rows:
        return json.dumps({"error": "No data to plot"})

    # Classify columns as numeric or categorical
    col_types: dict[str, str] = {}
    for col_idx, col_name in enumerate(columns):
        values = [row[col_idx] for row in rows if row[col_idx] is not None]
        numeric_count = 0
        for v in values:
            if isinstance(v, (int, float)):
                numeric_count += 1
            else:
                try:
                    float(v)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
        col_types[col_name] = "numeric" if numeric_count > len(values) * 0.5 else "categorical"

    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    cat_cols = [c for c, t in col_types.items() if t == "categorical"]

    # Auto-detect plot type
    if plot_type == "auto":
        if len(numeric_cols) == 1 and len(cat_cols) == 0:
            plot_type = "histogram"
        elif len(cat_cols) >= 1 and len(numeric_cols) >= 1:
            plot_type = "bar"
        elif len(numeric_cols) >= 2:
            plot_type = "scatter"
        else:
            plot_type = "bar"

    def _col_values(col_name: str) -> list[Any]:
        idx = columns.index(col_name)
        return [row[idx] for row in rows]

    if plot_type == "histogram":
        col = numeric_cols[0] if numeric_cols else columns[0]
        vals = [v for v in _col_values(col) if v is not None]
        # Bin into 20 buckets
        numeric_vals = []
        for v in vals:
            try:
                numeric_vals.append(float(v))
            except (ValueError, TypeError):
                pass
        if numeric_vals:
            import numpy as np

            counts, bin_edges = np.histogram(numeric_vals, bins=min(20, len(set(numeric_vals))))
            x_values = [round((bin_edges[i] + bin_edges[i + 1]) / 2, 4) for i in range(len(counts))]
            y_values = [int(c) for c in counts]
        else:
            x_values, y_values = [], []

        plot = PlotData(
            plot_type="histogram",
            title=f"Distribution of {col}",
            x_label=col,
            y_label="Count",
            x_values=x_values,
            y_values=y_values,
        )

    elif plot_type == "bar":
        x_col = cat_cols[0] if cat_cols else columns[0]
        y_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])

        x_vals = _col_values(x_col)
        y_vals = _col_values(y_col)

        # Aggregate: group by x, mean of y
        groups: dict[str, list[float]] = {}
        for x, y in zip(x_vals, y_vals):
            if x is None:
                continue
            key = str(x)
            try:
                groups.setdefault(key, []).append(float(y))
            except (ValueError, TypeError):
                pass

        x_values = list(groups.keys())
        y_values = [round(sum(v) / len(v), 4) if v else 0 for v in groups.values()]

        # Sort bars by leading number if labels look like numeric ranges
        def _sort_key(label: str) -> float:
            m = re.match(r"[\d,.]+", label.replace("k", "000").replace("K", "000").replace("M", "000000"))
            if m:
                try:
                    return float(m.group().replace(",", ""))
                except ValueError:
                    pass
            return float("inf")

        if x_values and any(re.match(r"\d", str(x)) for x in x_values):
            paired = sorted(zip(x_values, y_values), key=lambda p: _sort_key(str(p[0])))
            x_values = [p[0] for p in paired]
            y_values = [p[1] for p in paired]

        plot = PlotData(
            plot_type="bar",
            title=f"{y_col} by {x_col}",
            x_label=x_col,
            y_label=y_col,
            x_values=x_values,
            y_values=y_values,
        )

    elif plot_type == "scatter":
        x_col = numeric_cols[0]
        y_col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
        x_vals = _col_values(x_col)
        y_vals = _col_values(y_col)

        pairs = []
        for x, y in zip(x_vals, y_vals):
            try:
                pairs.append((float(x), float(y)))
            except (ValueError, TypeError):
                pass
        # Limit scatter points
        pairs = pairs[:500]

        plot = PlotData(
            plot_type="scatter",
            title=f"{y_col} vs {x_col}",
            x_label=x_col,
            y_label=y_col,
            x_values=[p[0] for p in pairs],
            y_values=[p[1] for p in pairs],
        )

    else:
        # Fallback: line chart
        x_col = columns[0]
        y_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])

        plot = PlotData(
            plot_type="line",
            title=f"{y_col} over {x_col}",
            x_label=x_col,
            y_label=y_col,
            x_values=_col_values(x_col),
            y_values=_col_values(y_col),
        )

    return plot.model_dump_json()


# ---------------------------------------------------------------------------
# Tool 5: create_data_card
# ---------------------------------------------------------------------------


def create_data_card(
    title: str,
    dataset_path: str,
    sql_query: str,
    summary: str,
    query_result_json: str | None = None,
    stats_json: str | None = None,
    plot_json: str | None = None,
    next_suggestions: list[str] | None = None,
) -> str:
    """Assemble all data analysis components into a DataCard."""
    query_result = None
    if query_result_json:
        try:
            qr_data = json.loads(query_result_json)
            if "error" not in qr_data:
                query_result = QueryResult(**qr_data)
        except (json.JSONDecodeError, Exception):
            pass

    stats = None
    if stats_json:
        try:
            stats_data = json.loads(stats_json)
            stats_list = stats_data.get("stats", stats_data)
            if isinstance(stats_list, list):
                stats = [StatsSummary(**s) for s in stats_list]
        except (json.JSONDecodeError, Exception):
            pass

    plot = None
    if plot_json:
        try:
            plot_data = json.loads(plot_json)
            if "error" not in plot_data:
                plot = PlotData(**plot_data)
        except (json.JSONDecodeError, Exception):
            pass

    card = DataCard(
        title=title,
        dataset_path=dataset_path,
        sql_query=sql_query,
        summary=summary,
        query_result=query_result,
        stats=stats,
        plot=plot,
        next_suggestions=next_suggestions,
    )
    return card.model_dump_json()
