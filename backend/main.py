"""FastAPI server with SSE streaming for the Sofa Genius agent."""

from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
