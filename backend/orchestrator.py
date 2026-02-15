"""Orchestrator — classify intent and route to the right subagent."""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

import anthropic

from backend.agents.base import run_subagent
from backend.agents import training, data, scout, launch

_ROUTING_PROMPT = """\
Classify the user message into exactly one category. Reply with ONLY the category name, nothing else.

Categories:
- training: W&B monitoring, listing runs, checking run health, fetching metrics, training anomalies
- data: SQL queries, dataset exploration, dataset search for analysis, data statistics, plotting data
- scout: scouting/finding models or datasets for a task, creating scout cards, drafting tweets/posts
- launch: fine-tuning jobs, launching training, evaluation jobs, Modal GPU jobs, proposing/approving launches
- general: greetings, general questions, help, anything that doesn't need tools

User message: {message}\
"""

_AGENT_MAP = {
    "training": training,
    "data": data,
    "scout": scout,
    "launch": launch,
}


async def _classify_intent(message: str) -> str:
    """Lightweight Claude call to classify the user's intent."""
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=20,
        messages=[{"role": "user", "content": _ROUTING_PROMPT.format(message=message)}],
    )
    category = response.content[0].text.strip().lower()
    # Normalize: strip punctuation and validate
    category = category.strip(".")
    if category not in _AGENT_MAP and category != "general":
        # Fallback: if the classifier gives something unexpected, try to match
        for key in _AGENT_MAP:
            if key in category:
                return key
        return "general"
    return category


async def run_orchestrator(
    message: str,
    history: list[dict[str, Any]] | None = None,
) -> AsyncGenerator[str, None]:
    """Route the user message to the appropriate subagent."""
    category = await _classify_intent(message)

    if category == "general":
        # Respond directly without tools
        client = anthropic.AsyncAnthropic()
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            system=(
                "You are Sofa Genius, an AI research assistant. "
                "Answer the user's question helpfully and concisely. "
                "Never use emojis. You help with W&B monitoring, data analysis, "
                "ML resource scouting, drafting posts, and launching fine-tuning/eval jobs on Modal."
            ),
            messages=(history or []) + [{"role": "user", "content": message}],
        )
        text = response.content[0].text
        yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    agent_module = _AGENT_MAP[category]
    async for event in run_subagent(
        message,
        history,
        system_prompt=agent_module.SYSTEM_PROMPT,
        tools=agent_module.TOOLS,
        tool_dispatch=agent_module.TOOL_DISPATCH,
        card_tool_mapping=agent_module.CARD_TOOL_MAPPING,
    ):
        yield event
