"""Data / SQL Analyst subagent — 6 tools."""

from __future__ import annotations

from typing import Any

from backend.tools.sql_analyst import (
    compute_stats,
    create_data_card,
    discover_dataset_schema,
    generate_plot_data,
    run_sql_query,
    search_hf_datasets,
)
from backend.tools.dataset_converter import (
    convert_dataset,
    inspect_dataset_format,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in data analysis \
and SQL queries against HuggingFace datasets.

You have access to two sets of tools:

1) DATASET SEARCH: search HuggingFace Hub for datasets matching a query.
2) DATA/SQL TOOLS: discover dataset schemas, run SQL queries, compute stats, \
generate plots, and create data cards for HuggingFace datasets.

DATASET SEARCH WORKFLOW:
When the user asks to find datasets for a task, follow this TWO-PHASE strategy:
PHASE 1 — Search the user's own HF space first. If the system prompt includes \
the user's HF username, call search_hf_datasets with author=<username> and a \
broad query. This checks their personal/org datasets first.
PHASE 2 — If Phase 1 returns 0 results (or no HF username is available), call \
search_hf_datasets WITHOUT the author parameter to search all of HuggingFace.

IMPORTANT SEARCH TIPS:
- Use SHORT, BROAD keywords (2-3 words max). The HF search API does substring \
matching on dataset names, so overly specific queries like "coding agent UI/UX \
improvement data" will return nothing. Instead try "code", "coding", "UI", etc.
- If a search returns 0 results, simplify the query — drop adjectives and use \
root nouns (e.g. "code instruction" instead of "advanced coding agent instructions").
- Try at most 2-3 different queries before reporting what you found.

Present results as a numbered list with dataset name, download count, and a brief \
description. Let the user pick which one to explore further. Then proceed with \
the data/SQL analysis workflow below.

DATA/SQL ANALYSIS WORKFLOW — YOU MUST ALWAYS FOLLOW ALL STEPS:
When the user asks about a specific dataset (sample, query, explore, analyze, etc.), \
you MUST complete ALL of these steps. Do NOT stop after run_sql_query — you MUST \
always finish with create_data_card so the frontend can render the visual card.
1. Call discover_dataset_schema first to see column names, types, and sample values.
2. Write a SQL query based on the user's intent. Use 'dataset' as the table name \
in your SQL — the backend will substitute the real HF path automatically.
3. Call run_sql_query to execute it.
4. Call compute_stats — pass the FULL JSON string returned by run_sql_query as \
the query_result_json parameter.
5. Call generate_plot_data — pass the FULL JSON string returned by run_sql_query \
as the query_result_json parameter.
6. ALWAYS call create_data_card as the FINAL step. Pass:
   - title: a descriptive title for the analysis
   - dataset_path: the HF dataset path
   - sql_query: the SQL you executed
   - summary: a 1-2 sentence summary of what the data shows
   - query_result_json: the FULL JSON string from run_sql_query
   - stats_json: the FULL JSON string from compute_stats
   - plot_json: the FULL JSON string from generate_plot_data
   - next_suggestions: 2-3 follow-up query ideas as a string array

CRITICAL: You MUST call create_data_card every time you query a dataset. \
This is what renders the visual Data Card in the UI. If you skip it, the user \
sees nothing in the cards panel. Never just summarize query results in text — \
always create the card.

IMPORTANT for SQL queries: use 'dataset' as the table name \
(e.g. SELECT * FROM dataset WHERE ...). The backend auto-replaces it with the \
real HuggingFace parquet path. Only SELECT queries are allowed.

After calling create_data_card, write a brief 2-3 sentence natural-language \
summary. Do NOT include raw JSON or <card> blocks in your text response.

Be concise and actionable. Focus on what matters.

DATASET CONVERSION WORKFLOW:
When the user asks about dataset format or wants to convert/preview a dataset:
1. Call inspect_dataset_format first to detect the current format and see sample rows.
2. Report the detected format and columns to the user. Ask for confirmation \
before previewing (e.g. "This dataset is in QA format. Shall I show a preview converted to base format?").
3. Once the user confirms, call convert_dataset with the target format.
4. The conversion preview card will be rendered automatically in the UI, \
showing before/after samples so the user can verify the output looks right.
5. The actual conversion happens on-the-fly at training time — no need to \
download the full dataset or push a converted copy to Hub.

Supported source formats: chatml, instruction, qa, completion.
Supported target formats: base (completion with role markers) or chatml (messages list).

IMPORTANT: Never over use emojis in your responses. Use emojis only if it is suitable. \
Never output raw JSON in your response.\
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_hf_datasets",
        "description": "Search HuggingFace Hub for datasets matching a query. Returns a ranked list with name, description, download count, and tags. When author is provided, lists that user's datasets and filters by keyword client-side. Call this when the user wants to find datasets for a task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keywords — keep short and broad (e.g. 'code instruction', 'chat', 'math'). Overly specific queries return 0 results.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10, max 20)",
                    "default": 10,
                },
                "author": {
                    "type": "string",
                    "description": "HuggingFace username or org to filter by. When set, lists datasets owned by this author and filters client-side by query keywords.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "discover_dataset_schema",
        "description": "Discover columns, types, sample values, and row count for a HuggingFace dataset. Call this first when the user mentions a dataset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_path": {
                    "type": "string",
                    "description": "HuggingFace dataset path, e.g. 'nyu-mll/glue' or 'user/dataset'",
                },
            },
            "required": ["dataset_path"],
        },
    },
    {
        "name": "run_sql_query",
        "description": "Execute a read-only SQL query against a HuggingFace dataset via DuckDB. Use 'dataset' as the table name in SQL — it will be auto-replaced with the actual HF parquet path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_path": {
                    "type": "string",
                    "description": "HuggingFace dataset path",
                },
                "sql_query": {
                    "type": "string",
                    "description": "SQL query to execute (SELECT only). Use 'dataset' as the table name.",
                },
            },
            "required": ["dataset_path", "sql_query"],
        },
    },
    {
        "name": "compute_stats",
        "description": "Compute per-column statistics (mean/std/min/max for numeric, unique_count/top_values for categorical) from a query result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_result_json": {
                    "type": "string",
                    "description": "The JSON string returned by run_sql_query",
                },
            },
            "required": ["query_result_json"],
        },
    },
    {
        "name": "generate_plot_data",
        "description": "Generate plot data from query results. Auto-detects best plot type: 1 numeric col -> histogram, categorical+numeric -> bar, 2 numeric -> scatter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_result_json": {
                    "type": "string",
                    "description": "The JSON string returned by run_sql_query",
                },
                "plot_type": {
                    "type": "string",
                    "description": "Plot type: 'auto', 'bar', 'line', 'scatter', 'histogram'. Default 'auto'.",
                    "default": "auto",
                },
            },
            "required": ["query_result_json"],
        },
    },
    {
        "name": "create_data_card",
        "description": "Assemble all data analysis components into a DataCard for frontend rendering. Call this after running the query, stats, and plot tools.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Card title summarizing the analysis",
                },
                "dataset_path": {
                    "type": "string",
                    "description": "HuggingFace dataset path",
                },
                "sql_query": {
                    "type": "string",
                    "description": "The SQL query that was executed",
                },
                "summary": {
                    "type": "string",
                    "description": "Human-readable summary of findings",
                },
                "query_result_json": {
                    "type": "string",
                    "description": "JSON from run_sql_query (optional)",
                },
                "stats_json": {
                    "type": "string",
                    "description": "JSON from compute_stats (optional)",
                },
                "plot_json": {
                    "type": "string",
                    "description": "JSON from generate_plot_data (optional)",
                },
                "next_suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-3 suggested follow-up queries",
                },
            },
            "required": ["title", "dataset_path", "sql_query", "summary"],
        },
    },
    {
        "name": "inspect_dataset_format",
        "description": "Detect the format of a HuggingFace dataset by loading a few sample rows. Returns format name (chatml, instruction, qa, completion, preference, unknown), column names, and sample rows. Call this before convert_dataset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_path": {
                    "type": "string",
                    "description": "HuggingFace dataset path, e.g. 'user/dataset-name'",
                },
                "split": {
                    "type": "string",
                    "description": "Dataset split to inspect (default 'train')",
                    "default": "train",
                },
            },
            "required": ["dataset_path"],
        },
    },
    {
        "name": "convert_dataset",
        "description": "Preview a dataset format conversion by streaming a few sample rows and converting them. Does NOT download or push the full dataset — the actual conversion happens on-the-fly at training time. Returns a ConversionCard with before/after sample comparison.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_path": {
                    "type": "string",
                    "description": "Source HuggingFace dataset path",
                },
                "target_format": {
                    "type": "string",
                    "description": "Target format: 'base' or 'chatml'",
                    "enum": ["base", "chatml"],
                },
                "split": {
                    "type": "string",
                    "description": "Dataset split to preview (default 'train')",
                    "default": "train",
                },
            },
            "required": ["dataset_path", "target_format"],
        },
    },
]

TOOL_DISPATCH: dict[str, Any] = {
    "search_hf_datasets": search_hf_datasets,
    "discover_dataset_schema": discover_dataset_schema,
    "run_sql_query": run_sql_query,
    "compute_stats": compute_stats,
    "generate_plot_data": generate_plot_data,
    "create_data_card": create_data_card,
    "inspect_dataset_format": inspect_dataset_format,
    "convert_dataset": convert_dataset,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "create_data_card": "data_card",
    "convert_dataset": "conversion_card",
}
