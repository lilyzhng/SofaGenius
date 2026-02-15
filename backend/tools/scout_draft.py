"""Scout + Draft tools — search HF Hub for models/datasets, compose draft posts."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from backend.models import (
    ConfidenceLevel,
    DraftPostCard,
    EvidenceRef,
    ScoutCard,
    ScoutRecommendation,
)

# ---------------------------------------------------------------------------
# Tool 1: search_hf_models
# ---------------------------------------------------------------------------


def search_hf_models(query: str, limit: int = 10) -> str:
    """Search HuggingFace Hub for models matching a query."""
    params = urllib.parse.urlencode({
        "search": query,
        "sort": "downloads",
        "direction": "-1",
        "limit": min(limit, 20),
    })
    url = f"https://huggingface.co/api/models?{params}"

    headers: dict[str, str] = {"Accept": "application/json"}
    token = os.environ.get("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw: list[dict[str, Any]] = json.loads(resp.read().decode())
    except Exception as e:
        return json.dumps({"error": str(e), "query": query})

    results = []
    for model in raw:
        results.append({
            "id": model.get("id", ""),
            "description": (model.get("description") or "")[:200],
            "downloads": model.get("downloads", 0),
            "likes": model.get("likes", 0),
            "tags": model.get("tags", [])[:10],
            "pipeline_tag": model.get("pipeline_tag", ""),
            "last_modified": model.get("lastModified", ""),
            "url": f"https://huggingface.co/{model.get('id', '')}",
        })

    return json.dumps({"query": query, "count": len(results), "models": results})


# ---------------------------------------------------------------------------
# Tool 2: create_scout_card
# ---------------------------------------------------------------------------


def create_scout_card(
    title: str,
    query: str,
    summary: str,
    recommendations_json: str,
    resource_type_filter: str | None = None,
) -> str:
    """Assemble scout recommendations into a ScoutCard."""
    try:
        recs_raw = json.loads(recommendations_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid recommendations JSON"})

    if not isinstance(recs_raw, list):
        return json.dumps({"error": "recommendations_json must be a JSON array"})

    recommendations = []
    for rec in recs_raw:
        recommendations.append(ScoutRecommendation(
            name=rec.get("name", ""),
            resource_type=rec.get("resource_type", "dataset"),
            url=rec.get("url", ""),
            description=rec.get("description", ""),
            downloads=rec.get("downloads", 0),
            likes=rec.get("likes", 0),
            tags=rec.get("tags", []),
            reasoning=rec.get("reasoning", ""),
            tradeoffs=rec.get("tradeoffs", ""),
        ))

    card = ScoutCard(
        title=title,
        query=query,
        summary=summary,
        recommendations=recommendations,
        resource_type_filter=resource_type_filter,
    )
    return card.model_dump_json()


# ---------------------------------------------------------------------------
# Tool 3: create_draft_post_card
# ---------------------------------------------------------------------------


def create_draft_post_card(
    title: str,
    draft_text: str,
    evidence_json: str | None = None,
    tone: str = "professional",
    thread_json: str | None = None,
) -> str:
    """Compose a draft tweet/post with evidence references. Always requires approval."""
    evidence: list[EvidenceRef] = []
    if evidence_json:
        try:
            ev_raw = json.loads(evidence_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid evidence JSON"})

        if not isinstance(ev_raw, list):
            return json.dumps({"error": "evidence_json must be a JSON array"})

        for ev in ev_raw:
            # Enforce guardrail: claims without evidence must be "hypothesis"
            confidence_str = ev.get("confidence", "hypothesis")
            if confidence_str not in ("finding", "hypothesis"):
                confidence_str = "hypothesis"
            evidence.append(EvidenceRef(
                source=ev.get("source", ""),
                snippet=ev.get("snippet", ""),
                link=ev.get("link"),
                confidence=ConfidenceLevel(confidence_str),
            ))

    thread: list[str] = []
    if thread_json:
        try:
            thread = json.loads(thread_json)
            if not isinstance(thread, list):
                thread = []
        except json.JSONDecodeError:
            thread = []

    card = DraftPostCard(
        title=title,
        draft_text=draft_text,
        thread=thread,
        evidence=evidence,
        tone=tone,
        char_count=len(draft_text),
        requires_approval=True,  # Always requires human approval
    )
    return card.model_dump_json()
