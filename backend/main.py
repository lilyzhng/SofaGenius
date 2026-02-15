"""FastAPI server with SSE streaming for the Sofa Genius agent."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.agent import run_agent

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
        async for event in run_agent(req.message, req.history):
            yield event

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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
