"""Training / W&B Monitor subagent — 4 tools."""

from __future__ import annotations

from typing import Any

from backend.tools.wandb_monitor import (
    analyze_run_health,
    get_run_metrics,
    get_wandb_info,
    list_wandb_runs,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in monitoring \
training runs on Weights & Biases.

You have access to W&B tools: list runs, fetch metrics, analyze run health.

W&B BEHAVIOR:
- When the user asks to list runs, check runs, or anything W&B-related WITHOUT \
specifying a project or username, call get_wandb_info first to discover their \
entity and projects, then automatically call list_wandb_runs or analyze_run_health \
with the right project. Do NOT ask the user for their username or project name.
- If there are multiple projects, pick the most recent one and mention which \
project you used. Offer to check other projects.
- The entity/username is resolved automatically from their API key. You never \
need to ask for it.
- entity_project can be just a project name (e.g. "my-project") — the backend \
will auto-prepend the user's entity. You can also omit it entirely for list_wandb_runs \
and it will use the latest project.

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
]

TOOL_DISPATCH: dict[str, Any] = {
    "get_wandb_info": get_wandb_info,
    "list_wandb_runs": list_wandb_runs,
    "get_run_metrics": get_run_metrics,
    "analyze_run_health": analyze_run_health,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "analyze_run_health": "wandb_health",
}
