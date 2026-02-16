"""Training / W&B Monitor subagent — 4 tools."""

from __future__ import annotations

from typing import Any

from backend.tools.wandb_monitor import (
    analyze_run_health,
    compare_runs,
    get_run_metrics,
    get_wandb_info,
    list_wandb_runs,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in monitoring \
training runs on Weights & Biases.

You have access to W&B tools: list runs, fetch metrics, analyze run health, and compare runs.

W&B BEHAVIOR:
- The user's W&B entity, projects, and current run info are pre-resolved and \
provided in the sections below (W&B IDENTITY, SESSION CONTEXT). Use this \
information directly — do NOT call get_wandb_info unless the identity section \
is missing.
- When SESSION CONTEXT provides a run ID, use it directly with analyze_run_health. \
Do NOT call list_wandb_runs first — you already have what you need.
- When SESSION CONTEXT provides only a display name (no run ID), call \
list_wandb_runs to find the matching run, then use its ID.
- Always use the full entity/project path (e.g. "entity/project-name") for \
tool calls. Pick the most recent project if the user doesn't specify one.
- Do NOT ask the user for their username or project name.

TOOL SELECTION:
- analyze_run_health: Use this whenever the user wants to SEE a run — plots, \
charts, visualizations, training curves, loss plots, or any visual overview. \
This is the ONLY tool that renders a visual Health Card with charts in the UI.
- get_run_metrics: Use this ONLY when you need raw metric numbers for internal \
reasoning (e.g. to answer a specific numeric question). It does NOT produce \
any visualization. Never use get_run_metrics when the user asks to "show", \
"plot", "visualize", or "see" training progress.
- compare_runs: Use this when comparing multiple runs side by side.

When you call analyze_run_health, the Health Card UI is rendered automatically \
by the frontend. Do NOT include the raw JSON or any <card> blocks in your text \
response. Instead, write a brief natural-language summary of the findings: \
overall status, key metrics, any anomalies found, and recommended actions.

When listing runs, present them in a clean readable format with run name, state, \
and key metrics.

Be concise and actionable. Focus on what matters: anomalies, their likely causes, \
and suggested next steps.

IMPORTANT: Never over use emojis in your responses. Use emojis only if it is suitable. \
Never output raw JSON in your response.\
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_wandb_info",
        "description": "Get the authenticated W&B user's entity (username) and list their projects. Call this first when the user doesn't specify a project.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_wandb_runs",
        "description": "List recent W&B runs for a project. If entity_project is omitted, uses the latest project automatically.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_project": {
                    "type": "string",
                    "description": "W&B entity/project path (e.g. 'myteam/my-project') or just project name. If omitted, uses the latest project.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of runs to return (default 10)",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_run_metrics",
        "description": "Fetch metric time series for a specific W&B run.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_project": {
                    "type": "string",
                    "description": "W&B entity/project path or just project name",
                },
                "run_id": {
                    "type": "string",
                    "description": "The run ID to fetch metrics for",
                },
                "keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metric keys to fetch (default: auto-discovers all numeric metrics)",
                },
                "max_samples": {
                    "type": "integer",
                    "description": "Max sample points (default 500)",
                    "default": 500,
                },
            },
            "required": ["entity_project", "run_id"],
        },
    },
    {
        "name": "analyze_run_health",
        "description": "Analyze a W&B run's health: fetches metrics, runs anomaly detection, and returns a structured Health Card with status, anomalies, charts data, and suggested actions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_project": {
                    "type": "string",
                    "description": "W&B entity/project path or just project name",
                },
                "run_id": {
                    "type": "string",
                    "description": "The run ID to analyze",
                },
            },
            "required": ["entity_project", "run_id"],
        },
    },
    {
        "name": "compare_runs",
        "description": "Compare metrics across multiple W&B runs. Overlays loss curves, learning rates, etc. on the same chart for visual comparison.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_project": {
                    "type": "string",
                    "description": "W&B entity/project path",
                },
                "run_ids_json": {
                    "type": "string",
                    "description": "JSON array of run IDs to compare",
                },
                "metric_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific metrics to compare (default: auto-discover common metrics)",
                },
            },
            "required": ["entity_project", "run_ids_json"],
        },
    },
]

TOOL_DISPATCH: dict[str, Any] = {
    "get_wandb_info": get_wandb_info,
    "list_wandb_runs": list_wandb_runs,
    "get_run_metrics": get_run_metrics,
    "analyze_run_health": analyze_run_health,
    "compare_runs": compare_runs,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "analyze_run_health": "wandb_health",
    "compare_runs": "comparison_card",
}
