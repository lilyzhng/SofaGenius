# Sofa Genius

*The research assistant that lets you stay on the sofa.*

---

## What Is This?

Picture this: you're a machine learning researcher. You've just kicked off a fine-tuning run on a 14-billion parameter model. It's going to take hours. You *could* keep refreshing your W&B dashboard, running SQL queries to sanity-check your training data, and hunting for the right HuggingFace models to compare against. Or you could lean back on the sofa and tell your AI assistant to do all of that for you.

That's Sofa Genius. It's a research agent built for the Anthropic hackathon that turns the boring, procedural parts of ML research — monitoring, data inspection, scouting, launching jobs — into a conversation. You speak your intent ("check my latest training run"), approve the plan, and the agent handles the grunt work. You get back a clean summary with evidence, charts, and suggested next steps.

The core promise: **your best ideas come when you're relaxed. Sofa Genius removes the procedural grind so you can stay in creative mode.**

---

## The "Aha" Moments

### 1. From Chat to GPU in 30 Seconds

The biggest aha: you type "fine-tune Qwen2.5-Coder on my UI dataset" and within seconds you're looking at a Launch Card with the exact config, a real cost estimate pulled from your HuggingFace dataset size and Modal's per-second GPU pricing. You click one button. An A100 spins up on Modal. The W&B link appears on the card — while training is still running — so you can watch the loss curve live. When it finishes, the card shows the exact cost from Modal's execution time. The entire journey from thought to running GPU happened in the chat window.

### 2. The Agent Catches What You'd Miss

You ask "check my W&B run" and the agent doesn't just show you a dashboard — it runs 7 different anomaly detectors (loss spikes, divergence, oscillation, gradient explosion, overfitting, plateaus, NaN detection) and tells you *what's wrong and what to do about it*. "Loss spiked 3 times after step 2k. Likely cause: learning rate too high. Suggested action: reduce LR to 1e-5 and restart." That's not a dashboard — that's a research assistant.

### 3. SQL on HuggingFace Without Downloading Anything

"Show me the distribution of code lengths in lilyzhng/uigen-ui-code-gen." The agent writes SQL, runs it against the HuggingFace parquet files via DuckDB (no download, no local storage), computes statistics, generates a plot, and packages it all into a Data Card. You never left the chat.

### 4. On-the-Fly Config Changes, Zero Friction

You're staring at a launch card and realize you want 20 epochs instead of 10. You just say it: "Change it to use 20 epochs instead of 10. Change to use 10,000 frames instead of 5,000." The agent understands the intent, modifies the config, and re-proposes — no YAML editing, no hunting through parameter files. Traditionally, you keep your eyes glued to a config file, hoping you don't make a typo that wastes an hour of GPU time. By doing config modification through conversation, the entire mode of training and research becomes easier to handle. The agent is the typo-proof layer between your intent and the machine.

### 5. Don't Break the Bank

When you're an independent researcher, your GPU budget *is* your runway. Sofa Genius makes cost visible before you commit. Every launch card shows a real cost estimate computed from your actual dataset size and Modal's per-second pricing. You can ask "how much will this cost?" before clicking approve. No more surprise bills from a job you forgot was running on H100s. The agent turns GPU spending from a scary unknown into a transparent, controllable decision.

### 6. Compare 10,000 Runs Without Losing Your Mind

W&B is powerful, but it gets overwhelming when you have thousands of experiments launched throughout the year. Manually finding runs, navigating between them, and overlaying charts is tedious. With Sofa Genius, you just say "compare these jobs with my previous jobs, overlay them on top of each other, and show me what's the difference." A Comparison Card appears with loss curves from multiple runs color-coded and aligned on the same axes. Toggle metrics on and off with pill buttons. Click through to W&B for any run. What used to be 10 minutes of dashboard wrangling is now one sentence.

### 7. Scout, Draft, Ship

"Find the best models and datasets for fine-tuning a code generation model." The agent searches HuggingFace, ranks the results, creates a Scout Card with tradeoffs. Then: "Draft a tweet about what we found." A Draft Post Card appears with evidence references — every claim tagged as "Finding" (backed by session data) or "Hypothesis" (not verified). Click "Approve & Post" and it goes to Twitter/X. The guardrail isn't just a checkbox — it's epistemically honest.

---

## Did We Democratize Research?

Kind of. Here's the thing about ML research: the *ideas* aren't the bottleneck. The bottleneck is the plumbing. Checking if your training run is healthy. Writing SQL to inspect your data. Figuring out which HuggingFace models are worth trying. Calculating if you can afford to run this experiment on H100s.

Sofa Genius doesn't make you a better researcher. It makes you a *faster* one by handling the procedural work. A PhD student who used to spend 30 minutes every morning checking W&B and writing SQL queries can now do it in 2 minutes of conversation. That's not democratization in the "everyone can do ML" sense — it's democratization in the "you don't need to be an ops expert to run experiments efficiently" sense.

The launch workflow makes this concrete. You say "fine-tune this model." The agent proposes an overfit run first (1 step, $0.08 — catches pipeline errors for almost nothing). Then an experimental run (100 samples, $0.09 — validates learning). Then production (full dataset, push to HuggingFace). This overfit → exp → prod progression is how experienced ML engineers work. Sofa Genius encodes that discipline into the tool, so even someone running their first fine-tuning job follows best practices.

---

## Technical Architecture

### The Big Picture

```
┌─────────────────────┐     ┌──────────────────────┐
│   Frontend (React)   │────▶│   Backend (FastAPI)    │
│                     │◀────│                        │
│  Left: Chat thread  │ SSE │  Orchestrator          │
│  Right: Cards panel │     │    ├─ Training Agent    │
│                     │     │    ├─ Data Agent         │
│  LaunchCard polls   │────▶│    ├─ Scout Agent        │
│  /api/launch/status │     │    └─ Launch Agent       │
└─────────────────────┘     └──────────┬───────────────┘
                                       │
                            ┌──────────▼───────────────┐
                            │     External Services     │
                            │  ├─ Anthropic API (Claude) │
                            │  ├─ W&B API               │
                            │  ├─ HuggingFace API       │
                            │  ├─ Modal (GPU jobs)      │
                            │  └─ Twitter/X API         │
                            └───────────────────────────┘
```

The frontend is a two-panel React app. Left panel: chat. Right panel: cards (visual summaries of what the agent found). They share state through a `useChat` hook that streams SSE events from the backend.

The backend is a FastAPI server with an orchestrator that routes messages to specialized subagents. Each subagent has a focused set of tools and a domain-specific system prompt.

### Why Subagents?

We started with a single monolithic agent that had all 13 tools. It worked fine for Phases 1-3. But when we added Modal launch tools (Phase 4), we hit 17 tools, and the agent started picking the wrong tool or hallucinating parameters. This is a known problem: LLMs degrade at tool selection when the tool count gets too high.

The fix: split into an orchestrator + 4 specialized subagents. The orchestrator is a lightweight Haiku call (~300ms) that classifies intent into one of 5 categories: training, data, scout, launch, general. Then it delegates to the matching subagent, which only sees its own 4-6 tools.

Think of it like a hospital. Instead of one doctor who does everything (and inevitably mixes up cardiology with dermatology), you have a triage nurse (orchestrator) who sends you to the right specialist (subagent). Each specialist is an expert in their narrow domain.

| Subagent | Tools | What It Does |
|----------|-------|-------------|
| Training | 4 | W&B monitoring, anomaly detection |
| Data | 6 | SQL queries, stats, plots, data cards |
| Scout | 4 | HF search, scout cards, draft posts |
| Launch | 6 | Propose/modify/launch fine-tuning and eval jobs |

### The SSE Streaming Protocol

The chat uses Server-Sent Events (not WebSockets). Here's why: the conversation is always request-response. The user sends a message, the agent responds. There's no bidirectional real-time communication needed. SSE is simpler, works through proxies, and auto-reconnects.

The event types:
- `text` — agent's natural language response (streamed incrementally)
- `tool_call` — agent is calling a tool (shows spinner in chat)
- `tool_result` — tool finished (shows check/error + summary)
- `card` — structured data for the right panel (health card, data card, launch card, etc.)
- `done` — response complete

Each card type has a matching React component that renders it. The `useChat` hook maintains two arrays: `messages[]` (for the chat) and `cards[]` (for the right panel). When a `card` event arrives, it gets pushed to the cards array and the right panel updates with a spring animation.

### The Card System

Cards are the core UX innovation. Instead of dumping raw data into chat, the agent returns structured JSON that the frontend renders as rich, interactive components. Each card type has a Pydantic model on the backend and a TypeScript interface + React component on the frontend.

```
Agent calls tool → Tool returns JSON → Backend emits SSE card event
    → Frontend receives → useChat pushes to cards[] → CardsPanel renders component
```

The `card_tool_mapping` dict in each subagent declares which tools produce cards:
```python
CARD_TOOL_MAPPING = {
    "analyze_run_health": "wandb_health",
    "create_data_card": "data_card",
    "create_scout_card": "scout_card",
    "propose_finetune": "launch_card",
}
```

This replaced a hardcoded if/elif chain in the original monolithic agent. Now each subagent just declares its mappings and the base agent loop handles emission automatically.

---

## Codebase Structure

```
backend/
├── orchestrator.py          # Intent classifier + router (Haiku)
├── agents/
│   ├── base.py              # Parameterized agent loop (shared)
│   ├── training.py          # W&B Monitor (4 tools)
│   ├── data.py              # Data/SQL Analyst (6 tools)
│   ├── scout.py             # Scout + Draft (4 tools)
│   └── launch.py            # Modal Launch (6 tools)
├── tools/
│   ├── wandb_monitor.py     # W&B API + 7 anomaly detectors (542 lines)
│   ├── sql_analyst.py       # DuckDB + HF parquet queries (529 lines)
│   ├── scout_draft.py       # HF Hub search + tweet drafting
│   └── modal_launcher.py    # Propose/modify/launch with real cost estimates
├── modal_app/
│   ├── app.py               # Deployable Modal app (finetune + eval)
│   ├── finetune.py          # Unsloth QLoRA training
│   └── eval.py              # Side-by-side model comparison
├── models.py                # Pydantic models for all card types
├── main.py                  # FastAPI server + /api/chat, /api/launch, /api/tweet
└── .env                     # API keys (never committed)

frontend/src/
├── hooks/useChat.ts         # SSE streaming + state management
├── components/
│   ├── ChatPanel.tsx         # Left panel: chat + inline approval buttons
│   ├── CardsPanel.tsx        # Right panel: card router
│   ├── MessageBubble.tsx     # Message rendering with tool steps
│   ├── WandBHealthCard.tsx   # Training health visualization
│   ├── DataCard.tsx          # SQL results + stats + plots
│   ├── ScoutCard.tsx         # HF recommendations
│   ├── DraftPostCard.tsx     # Tweet preview + post button
│   └── LaunchCard.tsx        # Job stepper + polling + cost
├── types.ts                  # TypeScript interfaces (mirrors Pydantic models)
└── App.tsx                   # Two-panel layout
```

### How the Pieces Connect

1. **User types in ChatPanel** → `useChat.sendMessage()` → POST to `/api/chat`
2. **FastAPI** calls `run_orchestrator()` → Haiku classifies intent → delegates to subagent
3. **Subagent** (e.g., training agent) calls Claude Sonnet with its focused tools + prompt
4. **Claude** decides to call tools → agent loop executes them → feeds results back
5. **Tool results** that match `card_tool_mapping` emit SSE card events
6. **Frontend** receives events → updates `messages[]` and `cards[]` → re-renders
7. **LaunchCard** polls `/api/launch/status/{id}` for job status + W&B URL from `modal.Dict`

---

## Technologies and Why We Chose Them

### Backend

| Tech | Why |
|------|-----|
| **Python + FastAPI** | Async, fast, great for SSE streaming. The ML ecosystem is Python. |
| **Anthropic API (Claude Sonnet)** | Powers the agent reasoning. Sonnet for subagents, Haiku for orchestrator routing. |
| **DuckDB** | SQL on HuggingFace parquet files without downloading. Zero setup, in-process. |
| **Modal** | Serverless GPU compute. Deploy once, spawn jobs on A100s with `.spawn()`. Pay per second. |
| **W&B API** | Training metrics, anomaly detection data source. Already what researchers use. |
| **modal.Dict** | Shared key-value store for passing W&B URLs from running Modal functions to the backend. The idiom for cross-environment data passing in Modal. |

### Frontend

| Tech | Why |
|------|-----|
| **React + TypeScript + Vite** | Type safety, fast HMR, standard toolchain. |
| **Framer Motion** | Spring physics animations for card transitions. Makes the UI feel alive. |
| **ReactMarkdown + remark-gfm** | Renders agent responses as rich markdown (tables, code blocks, links). |
| **Lucide React** | Clean, consistent icons. |
| **Tailwind CSS** | Utility-first styling. The design system (warm cream backgrounds, gold accents, Playfair Display serif) is codified in Tailwind classes. |

### Why Not the Claude Agent SDK?

The hackathon spec mentioned the Claude Agent SDK. We chose to implement the agent loop directly using the Anthropic API's `tool_use` feature instead. Why? The SDK adds a layer of abstraction we didn't need. Our agent loop is ~150 lines (`agents/base.py`) and gives us full control over SSE event emission, card handling, and tool dispatch. When you need to emit a `card` SSE event mid-loop (between tool result and continuing), having direct control matters.

### Why SSE Instead of WebSockets?

SSE (Server-Sent Events) is unidirectional: server → client. Our chat is request-response: user sends a message, server streams back the response. No need for bidirectional communication. SSE is simpler (just HTTP), works through CDNs and proxies, and the browser handles reconnection automatically. WebSockets would have been overkill.

---

## Lessons Learned (The Hard Way)

### 1. Import Order Can Break Everything

**The bug:** After deploying our Modal fine-tuning app, `SFTTrainer.__init__()` raised `TypeError: got an unexpected keyword argument 'tokenizer'`. The same code worked in a standalone file.

**The cause:** Unsloth monkey-patches TRL's `SFTTrainer` to accept `tokenizer`. But the patch only applies when `import unsloth` runs *before* `from trl import SFTTrainer`. Our import order was wrong.

**The fix:**
```python
# This fails silently — SFTTrainer never gets patched
from trl import SFTTrainer
from unsloth import FastLanguageModel

# This works — unsloth patches trl before we import SFTTrainer
import unsloth  # must be first!
from trl import SFTTrainer
from unsloth import FastLanguageModel
```

**The lesson:** When a library says "import me first," they mean it. Monkey-patching is order-dependent. Always check the library's import requirements, and when you move code between files (like we did from standalone script to Modal app), bring the import order with you.

### 2. Never Route Deterministic Actions Through an LLM

**The bug:** Clicking "Approve & Launch" sent a chat message ("Approved. Go ahead and launch it.") to the agent, hoping it would call the `launch_finetune` tool. It worked for the first job but not for subsequent ones — the agent just responded with text saying "it's launching!" without actually calling the tool.

**The cause:** We were asking an LLM to do something deterministic (call a specific API) through a non-deterministic path (natural language interpretation). The agent might: respond with text instead of calling the tool, call the wrong tool, or lose context in longer conversations.

**The fix:** The "Approve & Launch" button now calls `POST /api/launch` directly. No agent involved. The card updates deterministically.

**The lesson:** This is perhaps the most important engineering insight from the project. **Use agents for decisions, use code for actions.** If clicking a button should always produce the same outcome, don't route it through an LLM. The agent's job is to *decide what to propose*. The button's job is to *execute the approved action*. Mixing these up is a recipe for unreliable software.

### 3. One Job, One Card

**The bug:** When the agent proposed a fine-tuning job, a "Proposed" card appeared. When the job launched, a second "Running" card appeared. Two cards for one job.

**The cause:** Both `propose_finetune` and `launch_finetune` emitted separate SSE card events. The frontend appended each as a new card.

**The fix:** When a `launch_card` SSE event arrives with status != "proposed", merge its status fields into the existing proposed card instead of appending. The card updates in-place: Proposed → Running → Completed.

```typescript
// Merge: keep the proposal's rich info, update only status fields
updated[i] = {
  ...existingCard,
  status: newCard.status,
  modal_function_call_id: newCard.modal_function_call_id,
  wandb_url: newCard.wandb_url || existingCard.wandb_url,
};
```

**The lesson:** State transitions for a single entity should update in-place, not create duplicates. Think of it like a shipping tracker — you don't get a new package every time the status changes from "shipped" to "out for delivery."

### 4. Get Execution Time from the Platform, Not Your Timer

**The bug:** Our cost calculation used `trainer_stats.metrics["train_runtime"]` — which only measured the training step (18 seconds). But Modal billed for the entire container: model loading, data loading, training, saving, HF push (1 minute 45 seconds). We were showing costs 5x lower than reality.

**The fix:** Use Modal's `FunctionCall.get_call_graph()` which returns `started_at` and `finished_at` timestamps — the exact execution time Modal bills for.

**The lesson:** Always use the platform's own metrics rather than self-measured timers. Your timer only sees what your code does. The platform's timer sees everything: cold starts, imports, cleanup, and the overhead you can't measure.

### 5. A $0.08 Sanity Check Saves a $10 Failed Run

The overfit → exp → prod progression wasn't in the original plan. It came from experience: the first few fine-tuning runs failed due to import errors, wrong data formats, and missing Modal secrets. Each failure cost $3-5 in wasted GPU time.

The overfit run (1 step, 1 sample) costs $0.08 and catches all of these issues. The exp run (100 samples) costs $0.09 and validates that the model actually learns. Only then do you commit to production.

| Mode | Samples | Cost | What It Catches |
|------|---------|------|----------------|
| overfit | 1 | $0.08 | Import errors, data format, credentials, pipeline bugs |
| exp | 100 | $0.09 | Learning dynamics, divergence, data quality |
| prod | full | varies | Nothing new — just scales what's already validated |

**The lesson:** Never skip validation steps, especially when the failure mode is "burn GPU money for nothing." Make the validation so cheap that there's no excuse to skip it.

### 6. modal.Dict: The Missing Link for Running Jobs

**The problem:** After launching a fine-tuning job, the UI needed the W&B run URL so users could monitor training live. But Modal's `.spawn()` is fire-and-forget — you can't get intermediate outputs from a running function.

**What we tried:**
- Generic project link (`wandb.ai/user/project`) — useless with many runs
- Query W&B API for the latest run — fragile, could match the wrong run
- Wait for completion — defeats the purpose

**What worked:** `modal.Dict`, a serverless key-value store. The Modal function writes the W&B URL immediately after `wandb.init()`:
```python
run_urls = modal.Dict.from_name("sofa-genius-run-urls", create_if_missing=True)
run_urls[experiment_name] = wandb.run.url  # available within seconds of job start
```

The backend reads it during status polling. The URL appears on the card while training is still running.

**The lesson:** When you need to pass data from a running serverless function to outside code, look for the platform's built-in shared state primitives. For Modal, that's `modal.Dict`. For AWS Lambda, it might be DynamoDB. Don't try to hack it with logs or file systems.

### 7. Cost Estimates Should Be Based on Real Data

**The bug:** The agent told the user a production run would cost "$0.22-$0.28" and the card said "$5.25." The real cost was $0.09. Both numbers were wrong because they were based on hallucinated sample counts and incorrect GPU pricing.

**The fix:** The `propose_finetune` tool now:
1. Queries the HuggingFace API for the real training split size
2. Computes actual steps: `ceil(samples / (batch_size * grad_accum)) * epochs`
3. Estimates time: `120s overhead + steps * 1s/step`
4. Uses Modal's exact per-second pricing ($0.000694/sec for A100-80GB)

**The lesson:** Never let an LLM estimate costs. It will hallucinate numbers. Cost calculations should be deterministic functions of real inputs — actual dataset size, actual GPU rates, actual step counts. The agent's job is to *present* the cost, not *compute* it.

---

## How Good Engineers Think

A few meta-lessons from building this:

**Start monolithic, split when it hurts.** We didn't design the subagent architecture upfront. We built a single agent with all tools, and only split into subagents when tool selection degraded at 15+ tools. Premature architecture is as bad as premature optimization. Wait for the pain, then fix it.

**The UI is the product.** A health card with a stepper, anomaly badges, and suggested actions is 10x more useful than the same information dumped as text in a chat. We spent more time on card components than on agent logic. That's the right ratio.

**Let the LLM decide, let code execute.** The agent is brilliant at understanding "fine-tune Qwen on my dataset with 2 epochs" and translating it into a config. It's terrible at reliably calling `POST /api/launch`. The boundary between LLM and code should be at the decision/action interface.

**Make failure cheap.** The overfit/exp/prod progression, the "Approve & Launch" button, the cost estimates — they all serve the same purpose: make it safe to experiment. When failure costs $0.08 instead of $10, people try more things. That's how you get better models.

**Polls beat pushes for simplicity.** The LaunchCard polls `/api/launch/status` every 5 seconds. We could have built a WebSocket push system. But polling is simpler, stateless, and works through any infrastructure. For a hackathon (and most real products), simple beats clever.

---

## The Numbers

- **6 card types:** W&B Health, Comparison, Data, Scout, Draft Post, Launch
- **20 tools** across 4 subagents
- **7 anomaly detectors:** spike, divergence, oscillation, gradient explosion, overfitting, plateau, NaN
- **3 run modes:** overfit ($0.08), exp ($0.09), prod (varies)
- **~3,500 lines of Python** backend
- **~2,000 lines of TypeScript** frontend
- **4 external APIs:** Anthropic, W&B, HuggingFace, Modal
- **2 Claude models:** Sonnet (subagents), Haiku (orchestrator routing)

---

## What's Next

The spec includes two modes we haven't built:

- **Mode A (Audio/Sofa Mode):** Push-to-talk voice input via Pipecat or Web Speech API. The "sofa" in Sofa Genius — you literally lean back and talk to it.
- **Mode C (Task Runner):** One-click deterministic flows with stepper UI. The LaunchCard stepper is a prototype of this, but a full task runner would cover all flows (Monitor Run, Analyze Data, Scout, Launch, Draft).

And some ideas that emerged during development:

- **Config modification via chat:** Already built — "change epochs to 2" updates the config and re-proposes. Could extend to more natural language ("make it train longer" → increase epochs).
- **Cross-agent workflows:** "Scout datasets, pick the best one, fine-tune on it, evaluate, draft a post about the results." Currently requires manual handoffs between agents. An orchestrator that chains agents would enable end-to-end automation.
- **Cost tracking across sessions:** Accumulate actual costs from Modal across all jobs. "How much have I spent this week?" with a breakdown by run mode and model.

---

*Built in 48 hours for the Anthropic hackathon. The best ideas really do come from the sofa.*
