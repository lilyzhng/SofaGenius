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
from backend.tools.sql_analyst import (
    compute_stats,
    create_data_card,
    discover_dataset_schema,
    generate_plot_data,
    run_sql_query,
    search_hf_datasets,
)
from backend.tools.scout_draft import (
    create_draft_post_card,
    create_scout_card,
    search_hf_models,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant that helps ML researchers monitor \
training runs on Weights & Biases and analyze HuggingFace datasets via SQL.

You have access to five sets of tools:

1) W&B TOOLS: list runs, fetch metrics, analyze run health.
2) DATASET SEARCH: search HuggingFace Hub for datasets matching a query.
3) DATA/SQL TOOLS: discover dataset schemas, run SQL queries, compute stats, \
generate plots, and create data cards for HuggingFace datasets.
4) SCOUT TOOLS: search HF Hub for models, assemble scout recommendation cards.
5) DRAFT TOOLS: compose draft Twitter/X posts with evidence references.

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

DATASET SEARCH WORKFLOW:
When the user asks to find datasets for a task (e.g. "find datasets for fine-tuning \
Qwen2.5-Coder"), call search_hf_datasets with relevant keywords. Present the \
results as a numbered list with dataset name, download count, and a brief \
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

When listing runs, present them in a clean readable format with run name, state, \
and key metrics.

Be concise and actionable. Focus on what matters: anomalies, their likely causes, \
and suggested next steps.

SCOUT WORKFLOW:
When the user asks to scout or find models and/or datasets for a task (e.g. \
"scout datasets and models for fine-tuning Qwen2.5-Coder-14B"):
1. Call search_hf_datasets with relevant keywords to find datasets.
2. Call search_hf_models with relevant keywords to find models.
3. Analyze the results — pick the top 3-5 best options across datasets and models.
4. Call create_scout_card with:
   - title: descriptive title for the scouting session
   - query: the original user query
   - summary: 1-2 sentence overview of what you found
   - recommendations_json: a JSON array of recommendations, each with:
     name, resource_type ("dataset" or "model"), url, description, downloads, \
     likes, tags, reasoning (why this is a good pick), tradeoffs (any downsides)
   - resource_type_filter: "dataset", "model", or omit for both
The Scout Card UI is rendered automatically by the frontend. Write a brief \
natural-language summary after calling create_scout_card.

DRAFT POST WORKFLOW:
When the user asks to draft a tweet, post, or announcement:
1. Gather evidence from the current session — reference specific cards, metrics, \
or findings that support the claims.
2. Compose a concise draft (aim for under 280 characters for single tweets).
3. Call create_draft_post_card with:
   - title: descriptive title
   - draft_text: the tweet/post text
   - evidence_json: a JSON array of evidence references, each with:
     source (e.g. "ScoutCard", "WandBHealthCard"), snippet (key fact), \
     link (optional URL), confidence ("finding" if backed by session data, \
     "hypothesis" if not)
   - tone: "professional", "casual", "technical", etc.
   - thread_json: optional JSON array of follow-up tweet strings for threads
CRITICAL GUARDRAIL: Claims without session evidence MUST be labeled as \
"hypothesis", not "finding". Every draft post requires human approval — \
requires_approval is always true. The Draft Post Card UI is rendered \
automatically by the frontend.

When you create a DraftPostCard, the frontend renders an "Approve & Post" button. \
If the user has configured their Twitter API credentials, clicking Approve will \
post the tweet directly to their Twitter/X account. You do not need to post tweets \
yourself — the human clicks the button. Tell the user they can click "Approve & Post" \
on the Draft Post Card to publish it.

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
    # --- Phase 2: Data / SQL Analyst tools ---
    {
        "name": "search_hf_datasets",
        "description": "Search HuggingFace Hub for datasets matching a query. Returns a ranked list with name, description, download count, and tags. Call this when the user wants to find datasets for a task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'code generation python' or 'instruction tuning'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10, max 20)",
                    "default": 10,
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
    # --- Phase 3: Scout + Draft tools ---
    {
        "name": "search_hf_models",
        "description": "Search HuggingFace Hub for models matching a query. Returns a ranked list with name, description, download count, likes, tags, and pipeline_tag.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'code generation' or 'Qwen2.5-Coder'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10, max 20)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_scout_card",
        "description": "Assemble scout recommendations (datasets and/or models) into a ScoutCard for frontend rendering. Call this after searching HF Hub and analyzing results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Card title summarizing the scouting session",
                },
                "query": {
                    "type": "string",
                    "description": "The original search query",
                },
                "summary": {
                    "type": "string",
                    "description": "1-2 sentence overview of findings",
                },
                "recommendations_json": {
                    "type": "string",
                    "description": "JSON array of recommendations. Each object: {name, resource_type ('dataset'|'model'), url, description, downloads, likes, tags, reasoning, tradeoffs}",
                },
                "resource_type_filter": {
                    "type": "string",
                    "description": "Filter: 'dataset', 'model', or omit for both",
                },
            },
            "required": ["title", "query", "summary", "recommendations_json"],
        },
    },
    {
        "name": "create_draft_post_card",
        "description": "Compose a draft Twitter/X post with evidence references. Always requires human approval before posting. Call this when the user wants to draft a tweet or post.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Card title",
                },
                "draft_text": {
                    "type": "string",
                    "description": "The tweet/post text",
                },
                "evidence_json": {
                    "type": "string",
                    "description": "JSON array of evidence refs. Each object: {source, snippet, link (optional), confidence ('finding'|'hypothesis')}",
                },
                "tone": {
                    "type": "string",
                    "description": "Tone: 'professional', 'casual', 'technical', etc. Default 'professional'.",
                    "default": "professional",
                },
                "thread_json": {
                    "type": "string",
                    "description": "Optional JSON array of follow-up tweet strings for a thread",
                },
            },
            "required": ["title", "draft_text"],
        },
    },
]

TOOL_DISPATCH: dict[str, Any] = {
    "get_wandb_info": get_wandb_info,
    "list_wandb_runs": list_wandb_runs,
    "get_run_metrics": get_run_metrics,
    "analyze_run_health": analyze_run_health,
    "search_hf_datasets": search_hf_datasets,
    "discover_dataset_schema": discover_dataset_schema,
    "run_sql_query": run_sql_query,
    "compute_stats": compute_stats,
    "generate_plot_data": generate_plot_data,
    "create_data_card": create_data_card,
    "search_hf_models": search_hf_models,
    "create_scout_card": create_scout_card,
    "create_draft_post_card": create_draft_post_card,
}


def _execute_tool(name: str, input_data: dict[str, Any]) -> str:
    fn = TOOL_DISPATCH.get(name)
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
    return "Completed"


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
            result = _execute_tool(tool_use["name"], tool_use["input"])

            # Emit tool_result SSE event with brief summary
            summary = _summarize_tool_result(tool_use["name"], result)
            yield f"data: {json.dumps({'type': 'tool_result', 'name': tool_use['name'], 'summary': summary})}\n\n"

            # If this is analyze_run_health, also emit card directly
            if tool_use["name"] == "analyze_run_health":
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': 'wandb_health', 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            # If this is create_data_card, emit data card
            if tool_use["name"] == "create_data_card":
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': 'data_card', 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            # If this is create_scout_card, emit scout card
            if tool_use["name"] == "create_scout_card":
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': 'scout_card', 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            # If this is create_draft_post_card, emit draft post card
            if tool_use["name"] == "create_draft_post_card":
                try:
                    card_data = json.loads(result)
                    yield f"data: {json.dumps({'type': 'card', 'card_type': 'draft_post_card', 'data': card_data})}\n\n"
                except json.JSONDecodeError:
                    pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use["id"],
                "content": result,
            })
        messages.append({"role": "user", "content": tool_results})

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
