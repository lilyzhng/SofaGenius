# Sofa Genius

Research agent for delegating procedural work (W&B monitoring, dataset scouting, post drafting, job launching) via chat. Speak a goal, get an actionable brief, approve, and the agent executes.

## Prerequisites

- Python 3.10+
- Node.js 18+
- An `ANTHROPIC_API_KEY` set in `backend/.env`

Optional keys (depending on which features you use):

| Variable | Purpose |
|---|---|
| `WANDB_API_KEY` | W&B run monitoring |
| `HF_TOKEN` | HuggingFace dataset scouting / downloads |
| `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` | Twitter/X posting |
| `WANDB_ENTITY` | W&B entity override (auto-resolved from API key if omitted) |
| `OPENROUTER_API_KEY` | Modal eval jobs using OpenRouter |

## Setup

**Backend:**

```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**

```bash
cd frontend
npm install
```

## Running

Start the backend first, then the frontend in a separate terminal.

**1. Backend** (port 8000):

```bash
cd backend && uvicorn backend.main:app --reload --port 8000 --app-dir ..
```

**2. Frontend** (port 5173, proxies `/api` to backend):

```bash
cd frontend && npm run dev
```

Then open http://localhost:5173 in your browser.

## Tech Stack

- **Backend:** FastAPI, Anthropic API (tool_use loop), SSE streaming
- **Frontend:** Vite + React 19 + TypeScript, Tailwind CSS, Recharts, Framer Motion
- **Integrations:** W&B, HuggingFace Hub, Modal, Tweepy
