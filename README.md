<p align="center">
  <img src="frontend/public/SofaGenius_v3.png" alt="SofaGenius" width="500" />
  <!-- <br><br>
  <strong style="font-size:1.5em;">Sofa Genius</strong>
  <br>
  <em>The research assistant that lets you stay on the sofa.</em> -->
</p>

---
> **Run your research like a CEO.** Your best ideas come when you're relaxed. Sofa Genius gives you an AI team that handles the grind — you stay in creative mode. [Built with Opus 4.6 Hackathon](https://cerebralvalley.ai/e/claude-code-hackathon/details)

## What Is This?

SofaGenius is two things:

### 1. ML Research Assistant (Web App)
For ML researchers and engineers — stop babysitting GPUs. Sofa Genius turns the boring, procedural parts of ML research (monitoring, data inspection, scouting, launching jobs) into a conversation. You speak your intent, approve the plan, and the agent handles the grind.

### 2. Multi-Agent Coordination Framework (Agent Org)
Run multiple AI coding agents as an organization — each with its own identity, role, and persistent memory. Agents coordinate through a file-based handoff protocol and Discord.

```
agents/
├── ceo/CLAUDE.md          # Genius CEO — knows what everyone is doing
├── builder/CLAUDE.md      # Genius Builder — ships code and tools
└── data-agent/CLAUDE.md   # Genius Researcher — research, data, deep dives

handoff/
├── ceo_status.md          # CEO's current state
├── builder_status.md      # Builder's current state
├── data_agent_status.md   # Data Agent's current state
└── README.md              # Handoff protocol docs
```

**Key design decisions:**
- **Separate processes, not role-switching.** Each agent is its own Claude Code session with a dedicated CLAUDE.md. No "pretend to be a QA engineer now" — agents have stable identities.
- **File-based handoff.** No database, no HTTP server, no orchestrator process. Just markdown files agents read and write. Simple, inspectable, version-controlled.
- **Discord as coordination layer.** Agents communicate through Discord channels, which doubles as a human-readable audit trail.
- **Human-in-the-loop.** The human supervises and approves. Agents propose, humans decide.

See [`agents/`](agents/) and [`handoff/`](handoff/) for the full setup.

---

## Project Structure

```
agents/                              # Multi-agent org (CLAUDE.md per agent)
├── ceo/CLAUDE.md                    # Coordinator + growth
├── builder/CLAUDE.md                # Code + infrastructure
└── data-agent/CLAUDE.md             # Research + data

handoff/                             # Agent coordination layer
├── README.md                        # Protocol docs
├── ceo_status.md                    # CEO status file
├── builder_status.md                # Builder status file
└── data_agent_status.md             # Data Agent status file

backend/
├── orchestrator.py          # Intent classifier + router (Haiku)
├── agents/
│   ├── base.py              # Parameterized agent loop (shared)
│   ├── training.py          # W&B Monitor (4 tools)
│   ├── data.py              # Data/SQL Analyst (8 tools)
│   ├── scout.py             # Scout + Draft (4 tools)
│   └── launch.py            # Modal Launch (6 tools)
├── tools/
│   ├── wandb_monitor.py     # W&B API + 7 anomaly detectors
│   ├── sql_analyst.py       # DuckDB + HF parquet queries + dataset search
│   ├── scout_draft.py       # HF Hub search + tweet drafting
│   ├── dataset_converter.py # Format detection + on-the-fly conversion
│   └── modal_launcher.py    # Propose/modify/launch with real cost estimates
├── modal_app/
│   ├── app.py               # Deployable Modal app (finetune + eval)
│   ├── finetune.py          # Unsloth QLoRA training
│   └── eval.py              # Side-by-side model comparison
├── models.py                # Pydantic models for all card types
└── main.py                  # FastAPI server + SSE streaming

frontend/src/
├── hooks/useChat.ts         # SSE streaming + state management
├── components/
│   ├── ChatPanel.tsx         # Left panel: chat + input
│   ├── CardsPanel.tsx        # Right panel: card router
│   ├── WandBHealthCard.tsx   # Training health visualization
│   ├── DataCard.tsx          # SQL results + stats + plots
│   ├── ScoutCard.tsx         # HF recommendations
│   ├── DraftPostCard.tsx     # Tweet preview + post button
│   ├── LaunchCard.tsx        # Job stepper + polling + cost
│   ├── ConversionCard.tsx    # Before/after format preview
│   └── LandingPage.tsx       # Mode selection landing
├── types.ts                  # TypeScript interfaces
└── App.tsx                   # Two-panel layout
```

---

## Architecture

```
                            User message
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                       │
│                                                                      │
│   ┌──────────────────────┐         ┌───────────────────────────┐     │
│   │     Chat Panel       │         │       Cards Panel         │     │
│   │                      │         │                           │     │
│   │  User messages       │         │  WandBHealthCard          │     │
│   │  Agent responses     │         │  DataCard (SQL + plots)   │     │
│   │  Tool call indicators│         │  ScoutCard (HF picks)     │     │
│   │                      │         │  LaunchCard (GPU jobs)    │     │
│   │                      │         │  ComparisonCard           │     │
│   │                      │         │  DraftPostCard            │     │
│   │                      │         │  ConversionCard           │     │
│   └──────────────────────┘         └───────────────────────────┘     │
│              │  SSE stream (text, tool_call, tool_result, card)      │
└──────────────┼────────────────────────────────────────────────────── ┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI + SSE)                         │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐        │
│   │              Orchestrator (Claude Haiku, ~300ms)        │        │
│   │                                                         │        │
│   │   Classifies intent → routes to the right subagent      │        │
│   └─────┬──────────┬──────────────┬──────────────┬──────────┘        │
│         │          │              │              │                   │
│         ▼          ▼              ▼              ▼                   │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│   │ Training │ │   Data   │ │  Scout   │ │  Launch  │                │
│   │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │                │
│   │          │ │          │ │          │ │          │                │
│   │ 4 tools  │ │ 8 tools  │ │ 4 tools  │ │ 6 tools  │                │
│   │          │ │          │ │          │ │          │                │
│   │ W&B mon. │ │ SQL/Duck │ │ HF scout │ │ Propose  │                │
│   │ Anomaly  │ │ Stats    │ │ Personal │ │ Modify   │                │
│   │ Compare  │ │ Plots    │ │ + public │ │ Launch   │                │
│   │ Health   │ │ Convert  │ │ Draft    │ │ Cost est │                │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘                │
│        │            │            │            │                      │
└────────┼────────────┼────────────┼────────────┼──────────────────────┘
         │            │            │            │
         ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        External Services                             │
│                                                                      │
│   Anthropic API ─── Claude Sonnet (subagents) + Haiku (routing)      │
│   W&B API ───────── Training metrics, run history, anomaly data      │
│   HuggingFace ───── Dataset search, parquet SQL (via DuckDB)         │
│   Modal ─────────── Serverless A100 GPU jobs (finetune + eval)       │
│   Twitter/X ─────── Post drafts with human approval gate             │
└──────────────────────────────────────────────────────────────────────┘
```

### Why Subagents?

Started with a single agent with all tools. At 15+ tools, tool selection degraded badly. The fix: an **orchestrator (Haiku, ~300ms)** classifies intent and delegates to **4 specialized subagents**, each with only 4-8 tools. Like a hospital, a triage nurse routes you to the right specialist.

**How the loop works:** Each subagent runs an Anthropic tool_use loop (up to 10 turns). On every tool execution, the backend emits SSE events, `text` for agent prose, `tool_call`/`tool_result` for progress indicators, and `card` for structured visual cards that render in the right panel. The agent never outputs card JSON as text; cards are emitted as a side effect of tool execution.

| Subagent | Tools | Capabilities |
|----------|-------|-------------|
| **Training** | 4 | W&B monitoring, 7 anomaly detectors, multi-run comparison |
| **Data** | 8 | HF dataset search, DuckDB SQL, stats, plots, format detection + conversion |
| **Scout** | 4 | HF search (personal space first, then public), scout cards, draft tweets |
| **Launch** | 6 | Propose/modify/launch fine-tuning and eval jobs on Modal with cost estimates |

---

## Key Features

### 1. From Chat to GPU in 30 Seconds
Type "fine-tune Qwen2.5-Coder on my UI dataset" → Launch Card appears with exact config + real cost estimate → click Approve → A100 spins up on Modal → W&B link appears while training is running.

### 2. The Agent Catches What You'd Miss
Ask "check my W&B run" and the agent runs **7 anomaly detectors** (loss spikes, divergence, oscillation, gradient explosion, overfitting, plateaus, NaN detection) and tells you *what's wrong and what to do about it*.

### 3. SQL on HuggingFace Without Downloading Anything
"Show me the distribution of code lengths in my dataset." The agent writes SQL, runs it against HuggingFace parquet files via DuckDB, no download, no local storage, and packages it into a Data Card with stats and plots.

### 4. On-the-Fly Config Changes
"Change to 20 epochs instead of 10." The agent modifies the config and re-proposes. No YAML editing. The agent is the typo-proof layer between your intent and the machine.

### 5. Don't Break the Bank
Every Launch Card shows a real cost estimate computed from your actual dataset size and Modal's per-second pricing. A $0.08 overfit sanity check saves a $10 failed run.

### 6. Compare Runs in One Sentence
"Compare this run with my previous runs." Loss curves from multiple runs appear color-coded and aligned. What used to be 10 minutes of dashboard wrangling is now one sentence.

### 7. Dataset Format Conversion

Preview HuggingFace dataset format conversions directly from chat. Useful when a dataset is in the wrong format for your training task (e.g., QA format when you need completion format for base model fine-tuning).

The tool streams a handful of sample rows to detect the format and show a before/after preview, it does **not** download the full dataset or push anything to Hub. The actual conversion happens on-the-fly at training time.

**Supported source formats:** chatml, instruction, qa, completion, preference (auto-detected).
**Supported target formats:** `base` (completion with role markers) or `chatml` (messages list).

### 8. Two-Phase Dataset Scouting

"Find me datasets for improving coding agent UI/UX." The agent first searches your own HuggingFace space (resolved automatically from your HF token), then broadens to all of HuggingFace if nothing is found locally. Results are packaged into a Scout Card with download counts, tags, and reasoned recommendations.

---

## Tech Stack

### Backend

| Tech | Why |
|------|-----|
| **Python + FastAPI** | Async, fast, great for SSE streaming. The ML ecosystem is Python. |
| **Anthropic API** | Sonnet for subagents, Haiku for orchestrator routing. |
| **DuckDB** | SQL on HuggingFace parquet files without downloading. Zero setup. |
| **Modal** | Serverless GPU compute. Deploy once, spawn jobs on A100s. Pay per second. |
| **W&B API** | Training metrics and anomaly detection data source. |

### Frontend

| Tech | Why |
|------|-----|
| **React + TypeScript + Vite** | Type safety, fast HMR, standard toolchain. |
| **Framer Motion** | Spring physics animations for card transitions. |
| **Tailwind CSS** | Utility-first styling with warm cream/gold design system. |
| **Recharts** | Interactive metric charts for Health Cards and Data Cards. |

### The Numbers

- **6 card types**, W&B Health, Comparison, Data, Scout, Draft Post, Launch
- **22 tools** across 4 subagents
- **7 anomaly detectors**, spike, divergence, oscillation, gradient explosion, overfitting, plateau, NaN
- **3 run modes**, overfit ($0.08), exp ($0.09), prod (varies)
- **~3,500 lines** of Python backend
- **~2,000 lines** of TypeScript frontend
- **5 external APIs**, Anthropic, W&B, HuggingFace, Modal, Twitter/X
- **2 Claude models**, Sonnet (subagents), Haiku (orchestrator)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Modal account (for GPU launches): `modal token set`

### Environment Variables

Create a `backend/.env` file with your API keys:

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes | Powers all agent interactions |
| `WANDB_API_KEY` | For training features | W&B run monitoring and anomaly detection |
| `HF_TOKEN` | For scouting/data features | HuggingFace dataset search, SQL queries, identity resolution |
| `WANDB_ENTITY` | No | W&B entity override (auto-resolved from API key if omitted) |
| `OPENROUTER_API_KEY` | For eval jobs | Modal eval jobs using OpenRouter |
| `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` | For posting | Twitter/X posting from Draft Post cards |

### Setup

```bash
# Clone
git clone https://github.com/lilyzhng/SofaGenius.git
cd SofaGenius

# Backend
cd backend
pip install -r requirements.txt

# Frontend (new terminal)
cd frontend
npm install
```

### Running

Start the backend first, then the frontend in a separate terminal.

**1. Backend** (port 8000):

```bash
cd backend && uvicorn backend.main:app --reload --port 8000 --app-dir ..
```

**2. Frontend** (port 5173, proxies `/api` to backend):

```bash
cd frontend && npm run dev
```

**3. Deploy Modal App** (for GPU launches):

```bash
modal deploy backend/modal_app/app.py
```

Open http://localhost:5173 and start chatting.

---

## Lessons Learned

### Let the LLM Decide, Let Code Execute
We routed the "Approve & Launch" button through the agent, asking it to call the launch tool. Worked once, then failed silently. The fix: the button calls the API directly. **Use agents for decisions, use code for actions.** Never route deterministic actions through a language model.

### A $0.08 Sanity Check Saves a $10 Failed Run
The overfit → exp → prod progression came from painful experience. Each early failure cost $3-5 in wasted GPU time.

| Mode | Samples | Cost | What It Catches |
|------|---------|------|----------------|
| overfit | 1 | $0.08 | Import errors, data format, credentials, pipeline bugs |
| exp | 100 | $0.09 | Learning dynamics, divergence, data quality |
| prod | full | varies | Nothing new, just scales what's already validated |

### Never Let an LLM Estimate Costs
It will hallucinate numbers. Cost calculations should be deterministic functions of real inputs, actual dataset size, actual GPU rates, actual step counts.

### Start Monolithic, Split When It Hurts
We didn't design the subagent architecture upfront. We built a single agent with all tools, and only split when tool selection degraded at 15+ tools.

---

## Building with Opus 4.6

**What surprised me:** Opus has deep ML infrastructure knowledge, Modal, multi-GPU training, Unsloth, W&B integration, resource allocation, it worked out of the box in one shot. And even at the 1 million token context window, it didn't hallucinate on long-horizon tasks.

**How I built with it:** Designed in 4 phases upfront. For each phase, Opus produced a detailed implementation plan, I reviewed and corrected, then let it build. Human-in-the-loop the entire time. Every mistake got documented in a lessons learned file. CLAUDE.md reminded the model to check it at the start of every new session, persistent memory across context resets.

---
