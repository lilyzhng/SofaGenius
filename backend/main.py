"""FastAPI server with SSE streaming for the Sofa Genius agent."""

from __future__ import annotations

import json
import os
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.orchestrator import run_orchestrator

log = logging.getLogger(__name__)

app = FastAPI(title="Sofa Genius API")

_origins = ["http://localhost:5173", "http://localhost:3000"]
_frontend_url = os.environ.get("FRONTEND_URL", "")
if _frontend_url:
    _origins.extend(u.strip() for u in _frontend_url.split(",") if u.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id"],
)


class ActiveRun(BaseModel):
    wandb_url: str


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None
    active_run: ActiveRun | None = None
    session_id: str | None = None


@app.post("/api/chat")
async def chat(req: ChatRequest, user_id: str = Depends(get_current_user)):
    from backend import db

    # Pass active run context from frontend cards to orchestrator
    if req.active_run:
        from backend.orchestrator import update_run_context
        update_run_context(req.active_run.wandb_url, session_id=req.session_id)

    # Create or reuse session
    session_id = req.session_id
    if not session_id:
        preview = req.message[:200]
        title = req.message[:80] if len(req.message) <= 80 else req.message[:77] + "..."
        session = db.create_session(user_id, title=title, preview=preview)
        session_id = session["id"]

    # Persist user message
    db.save_message(session_id, "user", req.message)

    # Load user credentials from profile
    profile = db.get_user_profile(user_id)
    wandb_api_key = profile.get("wandb_api_key") if profile else None
    hf_token = profile.get("hf_token") if profile else None

    async def event_stream():
        collected_text = ""
        collected_segments: list[dict] = []
        collected_cards: list[dict] = []

        async for event in run_orchestrator(
            req.message,
            req.history,
            wandb_api_key=wandb_api_key,
            hf_token=hf_token,
            session_id=session_id,
        ):
            # Parse event to collect for persistence
            try:
                payload = json.loads(event.removeprefix("data: ").strip())
                etype = payload.get("type")
                if etype == "text" and payload.get("content"):
                    collected_text += payload["content"]
                    # Merge into text segments
                    if collected_segments and collected_segments[-1].get("type") == "text":
                        collected_segments[-1]["content"] += payload["content"]
                    else:
                        collected_segments.append({"type": "text", "content": payload["content"]})
                elif etype == "tool_call":
                    collected_segments.append({
                        "type": "tool",
                        "tool": {"name": payload.get("name", ""), "status": "running"},
                    })
                elif etype == "tool_result":
                    # Update last matching tool segment
                    for seg in reversed(collected_segments):
                        if (
                            seg.get("type") == "tool"
                            and seg.get("tool", {}).get("name") == payload.get("name")
                            and seg.get("tool", {}).get("status") == "running"
                        ):
                            summary = payload.get("summary", "")
                            seg["tool"]["status"] = "error" if summary.startswith("Error") else "done"
                            seg["tool"]["result"] = summary
                            break
                elif etype == "card" and payload.get("data"):
                    card_data = payload["data"]
                    collected_cards.append(card_data)
            except (json.JSONDecodeError, AttributeError):
                pass

            yield event

        # Persist assistant message + cards after stream completes
        try:
            if collected_text or collected_segments:
                db.save_message(session_id, "assistant", collected_text, collected_segments or None)
            for card in collected_cards:
                db.save_card(
                    session_id,
                    card.get("card_type", "unknown"),
                    card.get("title", ""),
                    card,
                )
            # Update session timestamp
            db.update_session(session_id, {"updated_at": "now()"})
        except Exception as e:
            log.warning("Failed to persist chat data: %s", e)

    headers = {"X-Session-Id": session_id}
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


class LaunchRequest(BaseModel):
    launch_type: str  # "finetune" or "eval"
    config: dict


@app.post("/api/launch")
async def launch_job(req: LaunchRequest, user_id: str = Depends(get_current_user)):
    """Launch a fine-tuning or evaluation job on Modal (button path)."""
    try:
        import modal
    except ImportError:
        return JSONResponse(
            status_code=500,
            content={"error": "Modal is not installed. Run: pip install modal"},
        )

    try:
        if req.launch_type == "finetune":
            fn = modal.Function.from_name("sofa-genius-launcher", "run_finetune")
            call = fn.spawn(req.config)
            wandb_project = req.config.get("wandb_project", "qwen-coder-code-gen")
        elif req.launch_type == "eval":
            fn = modal.Function.from_name("sofa-genius-launcher", "run_evaluation")
            call = fn.spawn(req.config)
            wandb_project = req.config.get("wandb_project", "uiux-eval")
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown launch_type: {req.launch_type}. Use 'finetune' or 'eval'."},
            )

        return {
            "success": True,
            "function_call_id": call.object_id,
            "wandb_project": wandb_project,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to launch Modal job: {str(e)}"},
        )


@app.get("/api/launch/status/{function_call_id}")
async def launch_status(function_call_id: str, run_key: str | None = None):
    """Poll a Modal function call for its status and result."""
    try:
        import modal
    except ImportError:
        return JSONResponse(status_code=500, content={"error": "Modal not installed"})

    try:
        call = modal.functions.FunctionCall.from_id(function_call_id)

        execution_time = None
        try:
            graph = call.get_call_graph()
            if graph:
                item = graph[0]
                if item.started_at and item.finished_at:
                    execution_time = (item.finished_at - item.started_at).total_seconds()
        except Exception:
            pass

        try:
            result = call.get(timeout=0)
            return {
                "status": "completed",
                "result": result,
                "execution_seconds": execution_time,
            }
        except TimeoutError:
            wandb_url = None
            if run_key:
                try:
                    run_urls = modal.Dict.from_name("sofa-genius-run-urls")
                    wandb_url = run_urls.get(run_key)
                except Exception:
                    pass
            return {
                "status": "running",
                "wandb_url": wandb_url,
                "execution_seconds": execution_time,
            }
        except modal.exception.ExecutionError as e:
            return {"status": "failed", "error": str(e), "execution_seconds": execution_time}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to check status: {str(e)}"})


class TweetRequest(BaseModel):
    text: str
    thread: list[str] | None = None


@app.post("/api/tweet")
async def post_tweet(req: TweetRequest, user_id: str = Depends(get_current_user)):
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        return JSONResponse(
            status_code=400,
            content={"error": "Twitter API credentials not configured. Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, and TWITTER_ACCESS_SECRET in your .env file."},
        )

    try:
        import tweepy

        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )

        response = client.create_tweet(text=req.text)
        tweet_id = response.data["id"]
        tweet_url = f"https://x.com/i/web/status/{tweet_id}"

        thread_ids = []
        if req.thread:
            prev_id = tweet_id
            for thread_text in req.thread:
                thread_resp = client.create_tweet(
                    text=thread_text,
                    in_reply_to_tweet_id=prev_id,
                )
                tid = thread_resp.data["id"]
                thread_ids.append(tid)
                prev_id = tid

        result = {"tweet_id": tweet_id, "tweet_url": tweet_url}
        if thread_ids:
            result["thread_ids"] = thread_ids
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to post tweet: {str(e)}"},
        )


# ---------------------------------------------------------------------------
# Profile & Session endpoints
# ---------------------------------------------------------------------------

class ProfileUpdate(BaseModel):
    wandb_api_key: str | None = None
    hf_token: str | None = None


@app.get("/api/profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    """Return the user's profile (masks raw API keys)."""
    from backend import db
    profile = db.get_user_profile(user_id)
    if not profile:
        return {"error": "Profile not found"}, 404
    return {
        "id": profile["id"],
        "display_name": profile.get("display_name", ""),
        "email": profile.get("email", ""),
        "avatar_url": profile.get("avatar_url", ""),
        "has_wandb_key": bool(profile.get("wandb_api_key")),
        "wandb_entity": profile.get("wandb_entity", ""),
        "has_hf_token": bool(profile.get("hf_token")),
        "hf_username": profile.get("hf_username", ""),
    }


@app.patch("/api/profile")
async def update_profile(req: ProfileUpdate, user_id: str = Depends(get_current_user)):
    """Update W&B key or HF token. Validates immediately."""
    from backend import db
    import urllib.request
    import urllib.error

    updates: dict = {}
    result: dict = {"success": True}

    # Validate W&B key
    if req.wandb_api_key is not None:
        if req.wandb_api_key == "":
            updates["wandb_api_key"] = None
            updates["wandb_entity"] = None
            result["wandb_entity"] = None
        else:
            try:
                import wandb
                api = wandb.Api(api_key=req.wandb_api_key)
                entity = api.default_entity
                updates["wandb_api_key"] = req.wandb_api_key
                updates["wandb_entity"] = entity
                result["wandb_entity"] = entity
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid W&B API key: {e}"},
                )

    # Validate HF token
    if req.hf_token is not None:
        if req.hf_token == "":
            updates["hf_token"] = None
            updates["hf_username"] = None
            result["hf_username"] = None
        else:
            try:
                api_req = urllib.request.Request(
                    "https://huggingface.co/api/whoami-v2",
                    headers={"Authorization": f"Bearer {req.hf_token}"},
                )
                with urllib.request.urlopen(api_req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                username = data.get("name") or data.get("user", "")
                updates["hf_token"] = req.hf_token
                updates["hf_username"] = username
                result["hf_username"] = username
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid HF token: {e}"},
                )

    if updates:
        db.update_user_profile(user_id, updates)

    return result


@app.get("/api/sessions")
async def list_user_sessions(user_id: str = Depends(get_current_user)):
    """List the user's chat sessions."""
    from backend import db
    sessions = db.list_sessions(user_id)
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_current_user)):
    """Get a full session with messages and cards."""
    from backend import db
    messages = db.get_session_messages(session_id)
    cards = db.get_session_cards(session_id)
    # Unwrap card data — the `data` column holds the full card JSON
    unwrapped_cards = [c["data"] for c in cards if c.get("data")]
    return {
        "messages": messages,
        "cards": unwrapped_cards,
    }


class SessionUpdate(BaseModel):
    title: str


@app.patch("/api/sessions/{session_id}")
async def rename_session(session_id: str, req: SessionUpdate, user_id: str = Depends(get_current_user)):
    """Rename a session."""
    from backend import db
    db.update_session(session_id, {"title": req.title})
    return {"success": True}


@app.delete("/api/sessions/{session_id}")
async def delete_user_session(session_id: str, user_id: str = Depends(get_current_user)):
    """Delete a session."""
    from backend import db
    db.delete_session(session_id)
    return {"success": True}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
