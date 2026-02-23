"""Orchestrator — classify intent and route to the right subagent.

Resolves W&B identity per-request (using user's credentials) and maintains
per-session context so agents always know the user's entity, projects, and
last-launched run without wasting tool calls to rediscover them.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
from typing import Any, AsyncGenerator

import anthropic

from backend.agents.base import run_subagent
from backend.agents import training, data, scout, launch, evaluation

log = logging.getLogger(__name__)

_ROUTING_PROMPT = """\
Classify the user message into exactly one category. Reply with ONLY the category name, nothing else.

Categories:
- training: W&B monitoring, listing runs, checking run health, fetching metrics, training anomalies
- data: SQL queries, dataset exploration, dataset search for analysis, data statistics, plotting data, dataset conversion, format conversion, inspect dataset format
- scout: scouting/finding models or datasets for a task, creating scout cards, drafting tweets/posts
- launch: fine-tuning jobs, launching training, Modal GPU jobs for fine-tuning, proposing/approving fine-tune launches
- evaluation: evaluating models or agents, benchmarks, MMLU, HumanEval, SWE-bench, agent testing, model quality, eval results, comparing scores, running evaluations, coding agent evaluation
- general: greetings, general questions, help, anything that doesn't need tools

User message: {message}\
"""

_AGENT_MAP = {
    "training": training,
    "data": data,
    "scout": scout,
    "launch": launch,
    "evaluation": evaluation,
}

# ---------------------------------------------------------------------------
# HF identity cache — keyed by token so per-user resolution works
# ---------------------------------------------------------------------------
_hf_cache: dict[str, dict[str, Any]] = {}


def _resolve_hf_info(token: str | None = None) -> dict[str, Any]:
    """Resolve HuggingFace username. Uses per-user token if provided, else env."""
    import urllib.request, urllib.error
    token = token or os.environ.get("HF_TOKEN")
    if not token:
        return {"username": None}
    if token in _hf_cache:
        return _hf_cache[token]
    try:
        req = urllib.request.Request(
            "https://huggingface.co/api/whoami-v2",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode())
        username = resp_data.get("name") or resp_data.get("user", "")
        info = {"username": username}
        log.info("HF identity resolved: username=%s", username)
    except Exception as e:
        log.warning("Could not resolve HF info: %s", e)
        info = {"username": None}
    _hf_cache[token] = info
    return info


def _build_hf_context(hf_token: str | None = None) -> str:
    """Build the HF identity block for system prompts."""
    info = _resolve_hf_info(hf_token)
    username = info.get("username")
    if not username:
        return ""
    return (
        f"\n\nHF IDENTITY (pre-resolved, do not ask the user):\n"
        f"- HuggingFace username: {username}\n"
        f"When scouting for datasets or models, ALWAYS search the user's own "
        f"HF space first by passing author=\"{username}\" to the search tools. "
        f"If that returns 0 results, then do a broader public search without the author filter."
    )


# ---------------------------------------------------------------------------
# W&B identity cache — keyed by api_key so per-user resolution works
# ---------------------------------------------------------------------------
_wandb_cache: dict[str, dict[str, Any]] = {}


def _resolve_wandb_info(api_key: str | None = None) -> dict[str, Any]:
    """Resolve W&B entity and projects. Uses per-user key if provided, else env."""
    key = api_key or os.environ.get("WANDB_API_KEY", "")
    cache_key = key or "__env__"
    if cache_key in _wandb_cache:
        return _wandb_cache[cache_key]
    try:
        import wandb
        api = wandb.Api(api_key=key) if key else wandb.Api()
        entity = api.default_entity
        projects = [
            {"name": p.name, "entity": p.entity}
            for p in api.projects(entity)
        ]
        info = {"entity": entity, "projects": projects[:20]}
        log.info("W&B identity resolved: entity=%s, %d projects", entity, len(projects))
    except Exception as e:
        log.warning("Could not resolve W&B info: %s", e)
        info = {"entity": None, "projects": []}
    _wandb_cache[cache_key] = info
    return info


def _build_wandb_context(wandb_api_key: str | None = None) -> str:
    """Build the W&B identity block for system prompts."""
    info = _resolve_wandb_info(wandb_api_key)
    if not info.get("entity"):
        return ""
    project_names = [p["name"] for p in info["projects"]]
    return (
        f"\n\nW&B IDENTITY (pre-resolved, do not call get_wandb_info):\n"
        f"- Entity: {info['entity']}\n"
        f"- Projects: {', '.join(project_names)}\n"
        f"Use entity_project=\"{info['entity']}/<project>\" for all W&B tool calls. "
        f"The most recent project is \"{project_names[0]}\" if the user doesn't specify one."
        if project_names else ""
    )


# ---------------------------------------------------------------------------
# Session context — tracks the most recently launched run per session so
# cross-agent references work.
# ---------------------------------------------------------------------------
_session_contexts: dict[str, dict[str, Any]] = {}


def _get_session_context(session_id: str | None = None) -> dict[str, Any]:
    """Get the context dict for a session. Falls back to a global default."""
    key = session_id or "__default__"
    if key not in _session_contexts:
        _session_contexts[key] = {}
    return _session_contexts[key]


# Keep module-level alias for backwards compatibility with update_run_context
_session_context: dict[str, Any] = _get_session_context()


def _run_id_from_wandb_url(url: str) -> str | None:
    """Extract the short run ID from a W&B URL like .../runs/5p5rsbyn."""
    if "/runs/" in url:
        return url.rstrip("/").split("/runs/")[-1].split("?")[0]
    return None


def _project_from_wandb_url(url: str) -> str | None:
    """Extract entity/project from a W&B URL like .../entity/project/runs/..."""
    # URL format: https://wandb.ai/entity/project/runs/run_id
    try:
        parts = url.rstrip("/").split("/")
        runs_idx = parts.index("runs")
        if runs_idx >= 2:
            return f"{parts[runs_idx - 2]}/{parts[runs_idx - 1]}"
    except (ValueError, IndexError):
        pass
    return None


def update_run_context(wandb_url: str, session_id: str | None = None) -> None:
    """Called by the API layer when the frontend sends an active_run with a W&B URL.

    This is the most authoritative source of run info — it comes directly
    from the LaunchCard's polling of Modal, which gets the real URL.
    """
    ctx = _get_session_context(session_id)
    run_id = _run_id_from_wandb_url(wandb_url)
    entity_project = _project_from_wandb_url(wandb_url)
    if not run_id:
        return

    launch_ctx = ctx.get("last_launch")
    if launch_ctx:
        launch_ctx["run_id"] = run_id
        launch_ctx["wandb_url"] = wandb_url
        if entity_project:
            project = entity_project.split("/")[-1] if "/" in entity_project else entity_project
            launch_ctx["wandb_project"] = project
    else:
        project = entity_project.split("/")[-1] if entity_project and "/" in entity_project else ""
        ctx["last_launch"] = {
            "experiment_name": "",
            "wandb_project": project,
            "wandb_url": wandb_url,
            "launch_type": "finetune",
            "dataset": "",
            "function_call_id": "",
            "run_id": run_id,
        }
    log.info("Run context updated from frontend: run_id=%s, url=%s", run_id, wandb_url)


def _resolve_run_id_from_modal(function_call_id: str, run_key: str) -> str | None:
    """Poll Modal once to get the W&B run URL, extract the run ID."""
    try:
        import modal
        call = modal.functions.FunctionCall.from_id(function_call_id)
        # Check if completed — result may contain wandb_url
        try:
            result = call.get(timeout=0)
            url = result.get("wandb_url", "") if isinstance(result, dict) else ""
            if url:
                return _run_id_from_wandb_url(url)
        except TimeoutError:
            pass
        # Still running — check modal.Dict
        if run_key:
            try:
                run_urls = modal.Dict.from_name("sofa-genius-run-urls")
                url = run_urls.get(run_key)
                if url:
                    return _run_id_from_wandb_url(url)
            except Exception:
                pass
    except Exception as e:
        log.debug("Could not resolve run ID from Modal: %s", e)
    return None


def _extract_event_context(event_json: str, session_id: str | None = None) -> None:
    """Extract and cache useful context from SSE events.

    Launch cards: capture experiment_name, wandb_project, function_call_id.
    Health cards: capture the resolved run_id.
    """
    ctx = _get_session_context(session_id)
    try:
        payload = json.loads(event_json.removeprefix("data: ").strip())
    except (json.JSONDecodeError, AttributeError):
        return

    event_type = payload.get("type")

    # --- Launch card: capture experiment name + project + function_call_id ---
    if event_type == "card" and payload.get("card_type") == "launch_card":
        card = payload.get("data", {})
        config = card.get("config", {})
        experiment_name = config.get("experiment_name", "")
        wandb_project = config.get("wandb_project", "")
        function_call_id = card.get("modal_function_call_id", "")
        if experiment_name or wandb_project:
            ctx["last_launch"] = {
                "experiment_name": experiment_name,
                "wandb_project": wandb_project,
                "wandb_url": card.get("wandb_url", ""),
                "launch_type": card.get("launch_type", ""),
                "dataset": config.get("dataset_name", ""),
                "function_call_id": function_call_id,
                "run_id": None,
            }
            if function_call_id and experiment_name:
                rid = _resolve_run_id_from_modal(function_call_id, experiment_name)
                if rid:
                    ctx["last_launch"]["run_id"] = rid

    # --- Health card: capture the resolved run_id ---
    if event_type == "card" and payload.get("card_type") == "wandb_health":
        card = payload.get("data", {})
        run_id = card.get("run_id")
        launch_ctx = ctx.get("last_launch")
        if run_id and launch_ctx and not launch_ctx.get("run_id"):
            launch_ctx["run_id"] = run_id
            launch_ctx["wandb_url"] = card.get("url") or launch_ctx.get("wandb_url", "")


def _ensure_run_id_resolved(session_id: str | None = None) -> None:
    """If we have a launch without a run_id, try resolving via Modal."""
    ctx = _get_session_context(session_id)
    launch_ctx = ctx.get("last_launch")
    if not launch_ctx or launch_ctx.get("run_id"):
        return
    fcid = launch_ctx.get("function_call_id")
    exp_name = launch_ctx.get("experiment_name")
    if fcid and exp_name:
        rid = _resolve_run_id_from_modal(fcid, exp_name)
        if rid:
            launch_ctx["run_id"] = rid
            log.info("Resolved W&B run ID from Modal: %s", rid)


def _build_launch_context(
    wandb_api_key: str | None = None,
    session_id: str | None = None,
) -> str:
    """Build a system prompt suffix from the last launched run."""
    ctx = _get_session_context(session_id)
    launch_ctx = ctx.get("last_launch")
    if not launch_ctx:
        return ""

    # Try to resolve the run ID if we don't have it yet
    _ensure_run_id_resolved(session_id)

    parts = []
    run_id = launch_ctx.get("run_id")
    wandb_info = _resolve_wandb_info(wandb_api_key)
    entity = wandb_info.get("entity", "")
    project = launch_ctx.get("wandb_project", "")

    if run_id:
        parts.append(f"W&B run ID: {run_id}")
        if entity and project:
            parts.append(f"entity_project: {entity}/{project}")
        parts.append("Use this run ID directly with analyze_run_health — no need to list runs first.")
    else:
        if launch_ctx.get("experiment_name"):
            parts.append(f"run display name: {launch_ctx['experiment_name']}")
        if entity and project:
            parts.append(f"entity_project: {entity}/{project}")
        parts.append(
            "The W&B run ID is not yet available (job may still be starting). "
            "Call list_wandb_runs to find the run matching this display name."
        )
    if launch_ctx.get("dataset"):
        parts.append(f"dataset: {launch_ctx['dataset']}")
    if not parts:
        return ""
    return (
        "\n\nSESSION CONTEXT — The user recently launched a "
        f"{launch_ctx.get('launch_type', 'training')} job:\n"
        + "\n".join(f"- {p}" for p in parts)
        + "\nWhen the user refers to 'the run', 'my run', 'the training', etc., "
        "they mean this run."
    )


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


@contextlib.contextmanager
def _inject_credentials(wandb_api_key: str | None, hf_token: str | None):
    """Temporarily set env vars for per-user credentials during tool execution."""
    old_wandb = os.environ.get("WANDB_API_KEY")
    old_hf = os.environ.get("HF_TOKEN")
    try:
        if wandb_api_key:
            os.environ["WANDB_API_KEY"] = wandb_api_key
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token
        yield
    finally:
        # Restore originals
        if old_wandb is not None:
            os.environ["WANDB_API_KEY"] = old_wandb
        elif wandb_api_key and "WANDB_API_KEY" in os.environ:
            del os.environ["WANDB_API_KEY"]
        if old_hf is not None:
            os.environ["HF_TOKEN"] = old_hf
        elif hf_token and "HF_TOKEN" in os.environ:
            del os.environ["HF_TOKEN"]


async def run_orchestrator(
    message: str,
    history: list[dict[str, Any]] | None = None,
    *,
    wandb_api_key: str | None = None,
    hf_token: str | None = None,
    session_id: str | None = None,
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

    # Build system prompt with injected context (per-user credentials)
    system_prompt = agent_module.SYSTEM_PROMPT
    if category in ("training", "launch", "evaluation"):
        system_prompt += _build_wandb_context(wandb_api_key)
    if category in ("training", "data", "evaluation"):
        system_prompt += _build_launch_context(wandb_api_key, session_id)
    if category in ("data", "scout", "evaluation"):
        system_prompt += _build_hf_context(hf_token)

    with _inject_credentials(wandb_api_key, hf_token):
        async for event in run_subagent(
            message,
            history,
            system_prompt=system_prompt,
            tools=agent_module.TOOLS,
            tool_dispatch=agent_module.TOOL_DISPATCH,
            card_tool_mapping=agent_module.CARD_TOOL_MAPPING,
        ):
            # Capture launch context from SSE events for cross-agent memory
            _extract_event_context(event, session_id)
            yield event
