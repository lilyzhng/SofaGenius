"""Parameterized agent loop shared by all subagents."""

from __future__ import annotations

import json
import re
from typing import Any, AsyncGenerator, Callable

import anthropic


def _execute_tool(
    name: str,
    input_data: dict[str, Any],
    tool_dispatch: dict[str, Callable],
) -> str:
    fn = tool_dispatch.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return fn(**input_data)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _summarize_tool_result(name: str, result: str) -> str:
    """Generate a brief human-readable summary of a tool result."""
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return "Completed"

    if "error" in data:
        return f"Error: {data['error'][:100]}"

    if name == "get_wandb_info":
        projects = data.get("projects", [])
        return f"Found {len(projects)} project{'s' if len(projects) != 1 else ''}"
    if name == "list_wandb_runs":
        runs = data if isinstance(data, list) else data.get("runs", [])
        return f"Found {len(runs)} run{'s' if len(runs) != 1 else ''}"
    if name == "analyze_run_health":
        status = data.get("status", "unknown")
        anomalies = data.get("anomalies", [])
        return f"Status: {status}, {len(anomalies)} anomal{'ies' if len(anomalies) != 1 else 'y'}"
    if name == "compare_runs":
        runs = data.get("runs", [])
        return f"Comparison card with {len(runs)} runs"
    if name == "search_hf_datasets":
        count = data.get("count", 0)
        return f"Found {count} dataset{'s' if count != 1 else ''}"
    if name == "discover_dataset_schema":
        cols = data.get("columns", [])
        rows = data.get("row_count", 0)
        return f"{len(cols)} columns, {rows:,} rows"
    if name == "run_sql_query":
        rc = data.get("row_count", 0)
        ms = data.get("execution_time_ms", 0)
        return f"{rc} rows in {ms:.0f}ms"
    if name == "compute_stats":
        stats = data.get("stats", [])
        return f"Stats for {len(stats)} column{'s' if len(stats) != 1 else ''}"
    if name == "generate_plot_data":
        pt = data.get("plot_type", "chart")
        return f"Generated {pt} chart"
    if name == "create_data_card":
        return "Data card created"
    if name == "search_hf_models":
        count = data.get("count", 0)
        return f"Found {count} model{'s' if count != 1 else ''}"
    if name == "create_scout_card":
        recs = data.get("recommendations", [])
        return f"Scout card created with {len(recs)} recommendation{'s' if len(recs) != 1 else ''}"
    if name == "create_draft_post_card":
        chars = data.get("char_count", 0)
        return f"Draft created ({chars} chars)"
    if name == "propose_finetune":
        return "Fine-tuning job proposed"
    if name == "modify_and_propose":
        return "Config updated, new proposal created"
    if name == "propose_eval":
        return "Evaluation job proposed"
    if name == "launch_finetune":
        status = data.get("status", "unknown")
        return f"Fine-tuning job {status}"
    if name == "launch_eval":
        status = data.get("status", "unknown")
        return f"Evaluation job {status}"
    return "Completed"


async def run_subagent(
    message: str,
    history: list[dict[str, Any]] | None,
    *,
    system_prompt: str,
    tools: list[dict[str, Any]],
    tool_dispatch: dict[str, Callable],
    card_tool_mapping: dict[str, str],
) -> AsyncGenerator[str, None]:
    """Run the Anthropic tool_use agent loop, yielding SSE events.

    Parameters
    ----------
    message : str
        The new user message.
    history : list or None
        Previous conversation turns.
    system_prompt : str
        System prompt for this subagent.
    tools : list
        Tool schemas available to this subagent.
    tool_dispatch : dict
        Maps tool names to callable functions.
    card_tool_mapping : dict
        Maps tool names to their card_type (e.g. {"analyze_run_health": "wandb_health"}).
        When one of these tools returns, a card SSE event is emitted.
    """
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
            system=system_prompt,
            tools=tools,
            messages=messages,
        )

        # Process content blocks — collect first, then emit text before tool calls
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

        # Emit text first
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

        # Then emit tool calls
        for tool_use in tool_uses:
            yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_use['name'], 'input': tool_use['input']})}\n\n"

        # If no tool use, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            break

        # Execute tools and feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_use in tool_uses:
            result = _execute_tool(tool_use["name"], tool_use["input"], tool_dispatch)

            # Emit tool_result SSE event with brief summary
            summary = _summarize_tool_result(tool_use["name"], result)
            yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_use['name'], 'summary': summary})}\n\n"

            # Emit card event if this tool is in card_tool_mapping
            card_type = card_tool_mapping.get(tool_use["name"])
            if card_type:
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': card_type, 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": result,
            })
        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
