"""Scout + Draft subagent — 4 tools."""

from __future__ import annotations

from typing import Any

from backend.tools.sql_analyst import search_hf_datasets
from backend.tools.scout_draft import (
    create_draft_post_card,
    create_scout_card,
    search_hf_models,
)

SYSTEM_PROMPT = """\
You are Sofa Genius, an AI research assistant specializing in scouting ML \
resources and drafting posts.

You have access to:
1) SCOUT TOOLS: search HF Hub for datasets and models, assemble scout recommendation cards.
2) DRAFT TOOLS: compose draft Twitter/X posts with evidence references.

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
    "search_hf_datasets": search_hf_datasets,
    "search_hf_models": search_hf_models,
    "create_scout_card": create_scout_card,
    "create_draft_post_card": create_draft_post_card,
}

CARD_TOOL_MAPPING: dict[str, str] = {
    "create_scout_card": "scout_card",
    "create_draft_post_card": "draft_post_card",
}
