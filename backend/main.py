"""FastAPI server with SSE streaming for the Sofa Genius agent."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.orchestrator import run_orchestrator

app = FastAPI(title="Sofa Genius API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None


@app.post("/api/chat")
async def chat(req: ChatRequest):
    async def event_stream():
        async for event in run_orchestrator(req.message, req.history):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class LaunchRequest(BaseModel):
    launch_type: str  # "finetune" or "eval"
    config: dict


@app.post("/api/launch")
async def launch_job(req: LaunchRequest):
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
async def launch_status(function_call_id: str):
    """Poll a Modal function call for its status and result.

    Returns:
    - status: "running" | "completed" | "failed"
    - result: the function's return dict (includes wandb_url) if completed
    - error: error message if failed
    """
    try:
        import modal
    except ImportError:
        return JSONResponse(status_code=500, content={"error": "Modal not installed"})

    try:
        call = modal.functions.FunctionCall.from_id(function_call_id)
        try:
            result = call.get(timeout=0)
            # Job completed — result contains wandb_url, experiment_name, etc.
            return {"status": "completed", "result": result}
        except TimeoutError:
            # Still running
            return {"status": "running"}
        except modal.exception.ExecutionError as e:
            return {"status": "failed", "error": str(e)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to check status: {str(e)}"})


class TweetRequest(BaseModel):
    text: str
    thread: list[str] | None = None


@app.post("/api/tweet")
async def post_tweet(req: TweetRequest):
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
