"""Anthropic tool_use agent loop with SSE streaming."""

from __future__ import annotations

import json
import re
from typing import Any, AsyncGenerator

import anthropic

from backend.tools.wandb_monitor import (
    analyze_run_health,
    get_run_metrics,
    get_wandb_info,
    list_wandb_runs,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant that helps ML researchers monitor \
and analyze their training runs on Weights & Biases (W&B).

You have access to tools that can list runs, fetch metrics, and analyze run health.

IMPORTANT BEHAVIOR:
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

IMPORTANT: Never use emojis in your responses. Use plain text only. \
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


def _execute_tool(name: str, input_data: dict[str, Any]) -> str:
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return fn(**input_data)
    except Exception as e:
        return json.dumps({"error": str(e)})


async def run_agent(
    message: str,
    history: list[dict[str, Any]] | None = None,
) -> AsyncGenerator[str, None]:
    """Run the Anthropic tool_use agent loop, yielding SSE events."""
    client = anthropic.AsyncAnthropic()

    messages: list[dict[str, Any]] = []
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    max_iterations = 10
    for _ in range(max_iterations):
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Process content blocks
        tool_uses: list[dict[str, Any]] = []
        text_parts: list[str] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                yield f"data: {json.dumps({'type': 'tool_call', 'name': block.name, 'input': block.input})}\n\n"

        # Emit text
        if text_parts:
            full_text = "\n".join(text_parts)

            # Strip any <card> blocks that Claude may have included
            full_text = re.sub(
                r'<card[^>]*>.*?</card>',
                '', full_text, flags=re.DOTALL,
            )
            # Strip large JSON blobs that leak into text
            full_text = re.sub(
                r'```json\s*\{["\']card_type["\'].*?```',
                '', full_text, flags=re.DOTALL,
            )
            full_text = re.sub(
                r'\{[\s\n]*"card_type"\s*:.*',
                '', full_text, flags=re.DOTALL,
            )

            clean_text = full_text.strip()
            if clean_text:
                yield f"data: {json.dumps({'type': 'text', 'content': clean_text})}\n\n"

        # If no tool use, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            break

        # Execute tools and feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_use in tool_uses:
            result = _execute_tool(tool_use["name"], tool_use["input"])

            # If this is analyze_run_health, also emit card directly
            if tool_use["name"] == "analyze_run_health":
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': 'wandb_health', 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": result,
            })
        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
