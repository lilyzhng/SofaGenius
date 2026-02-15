# Sofa Genius — Final Design (Hackathon-Ready, Extensible)

## 1. Product Definition

Sofa Genius is a "lazy-smart research agent" that lets a researcher stay in high-level thinking mode (often literally on a sofa) while delegating procedural work: data inspection (SQL), training job launch, W&B monitoring, scouting new datasets/models, and drafting posts. The core UX promise: speak a goal → get an actionable brief → approve → the agent executes → you get alerts + a clean summary.

## 2. The Three Modes (First-Class UX)

### Mode A — Audio Mode ("Sofa Mode")

**Purpose:** capture intent hands-free + make quick decisions.

**Behavior rules:**
- Respond in ≤ 20–30 seconds.
- Start with a 1-line verdict.
- Mention at most 2 key findings.
- End with exactly 1 decision question.

> Example: "Run looks unstable: loss spiked 3 times after step 2k. Want me to lower LR and restart, or keep running?"

### Mode B — Conversational Mode ("Chat + Cards")

**Purpose:** show evidence, plans, and receipts.
**Note**:  I think you can either pull the wannabe cards or you can render a generated UI on the flag given the training information it has. We can go whichever is easier

**Layout:**
- Left: chat (intent, plan, confirmations).
- Right: cards (visual summaries + actions).

**Card types (v1):**
- W&B Health Card (status, anomalies, top metrics, recommended action)
- Data Card (SQL used, key stats, plot)
- Scout Card (top datasets/models, why, links)
- Run Brief Card (dataset + config + risks + acceptance criteria)
- Draft Post Card (tweet/linkedin draft + key claims + evidence references)

### Mode C — Control Mode ("Task Runner")

**Purpose:** deterministic execution + demo-friendly.

A set of one-click flows with checkpoints:
- Monitor Run
- Analyze Data
- Scout Datasets/Models
- Launch Training
- Draft Post

Each flow shows a step list with "Proposed → Approved → Executed" state.

## 3. The MVP Scope (Keep It Tight)

You already chose 3 core capabilities. Lock them:

**Feature 1: Data/SQL Analyst**
- NL → SQL translation (for a configured dataset/schema)
- Run query, compute basic stats, generate one plot
- Return Data Card + "what it means" + next query suggestions

**Feature 2: W&B Monitor**
- Pull metrics history for a run (loss, eval loss, accuracy, lr, grad_norm if available)
- Detect "interesting behaviors" and flag
- Return W&B Health Card + proposed next action

**Feature 3: Budget Control**
- ask Sofa Genius, hey, the Sofa Genius will ask me, are you ready to launch this experiment? Then I will do, like, can we do a budget check? Because I think this is like the boring work of, you know, researchers, you need to do resource management, budget management. But Sofa Genius will give us estimation, say, oh, don't worry about it. It's just going to take about five hours using 8 H100, so like about $50. You can totally cover it.

- Adding a budget check is smart and practical. Before launching any experiment, Sofa Genius will prompt you with a cost estimate based on runtime and resources. You'll get a clear dollar figure—so you can either approve, adjust the scale, or cancel. This feature not only reduces the hassle of manual budget calculations but also builds trust—you always know the cost before committing.

**Feature 4: Scout + Draft**
- Search HF/GitHub for datasets/models by topic keywords
- Return shortlist with reason
- Optionally draft a post based on real evidence from run or data analysis (always human approval)

## 4. Core User Flows (End-to-End)

### Flow 1: "Monitor my run" (fastest wow)

1. Audio: "Check my W&B run."
2. Agent (audio): verdict + 2 findings + decision question.
3. Chat+Cards: W&B Health Card appears (plot thumbnail + anomaly list + recommended action).
4. User taps: Approve "Lower LR + restart" (or "Keep running").
5. Task Runner executes action (if you wire it) or at least generates exact commands/instructions (fallback).

**Demo artifact:** a flagged anomaly + a recommended fix.

### Flow 2: "Check this data for me" (practical daily value)

1. Audio/Chat: "Find failure cases where UI gen outputs break layout."
2. Agent asks 1–2 schema clarification questions (only if needed), then proposes SQL.
3. Executes SQL → Data Card with table + plot.
4. Agent suggests: "Next slice to inspect" + "candidate labeling strategy."

### Flow 3: "Scout → launch → monitor → draft post" (full story)

1. "I want to train a coding agent for better UI/UX."
2. Scout Card: 3 candidate datasets + tradeoffs.
3. Run Brief Card: chosen dataset + config + acceptance criteria.
4. Task Runner: triggers Modal job (or prints modal command) → W&B link created.
5. W&B Health Card updates.
6. Draft Post Card generated only if there's a genuine insight (e.g., a fix improved eval metric).

## 5. "Interesting Behavior" Definitions (Simple, Robust Heuristics)

Implement these as rule-based detectors for hackathon reliability:

**Training instability:**
- Loss spike: loss(t) > mean(loss last N) + k*std (k=3)
- Divergence: loss increases monotonically for M steps
- Oscillation: high variance above threshold for window W
- Gradient explosion: grad_norm above threshold (if logged)

**Overfitting:**
- train_loss decreasing while eval_loss increasing for K eval points

**Plateau:**
- improvement < ε for T steps (or K eval points)

**Data issues:**
- NaNs in metrics
- sudden metric reset (step counter reset, logging glitch)

Each detector outputs: "symptom → likely cause → suggested action."

## 6. System Architecture (Minimal but Real)

### Front-end (web)
- Push-to-talk button (audio mode)
- Chat thread
- Right-side cards panel
- Task Runner panel (stepper UI)

### Back-end (agent + tools)

A small orchestrator with:
- Intent Router: classify intent into one of the flows
- Planner: produce a plan + required tools
- Tool Executors:
    - W&B connector: fetch run metrics + charts
    - SQL connector: run queries (via configured DB)
    - Scout connector: search HF/GitHub (can start with simple HTTP search or curated list)
    - Modal launcher: trigger job OR generate command template
- Artifact Builder: creates Cards (JSON schema)

### Data model (key objects)
- Task: {id, mode, flow_type, status, checkpoints[]}
- Card: {type, title, summary, evidence[], actions[]}
- Evidence: {source, snippet/metric, link}
- Action: {label, risk_level, requires_approval, payload}

## 7. Guardrails (So It Feels Trustworthy)

- **Human-in-the-loop always for:**
    - launching jobs that spend money
    - stopping/restarting runs
    - posting publicly
- **"Evidence required" for strong claims:**
    - If no evidence, the card must say "Hypothesis" not "Finding."
- **Clear rollback:**
    - Every proposed change must include "undo" or "revert" instruction.

## 8. Hackathon Selling Points (What Judges Should Remember)

- **The aha:** your best ideas come when relaxed; Sofa Genius removes the procedural grind so you can stay in creative mode.
- **Strong demo artifacts:** cards + plots + SQL output + flagged anomalies.
- **Practical value:** replaces repetitive "check W&B / run SQL / search HF" loops with one spoken request.
- **Extensible:** traces + approvals become data to personalize the agent to your "research taste" later.

## 9. Build Order (To Actually Ship)

- 1 (must work end-to-end): Monitor Run (W&B Health Card + anomaly detector)
- 2: Data/SQL (one dataset + NL→SQL + one plot)
- 3: Scout + Draft (shortlist + draft post with evidence)
- **If time:** polish mode handoff (audio → auto-create cards)

If you want, I can also give you the exact card JSON schemas + a single "demo script" you can rehearse word-for-word (audio lines + clicks + expected outputs).

### 10. Tools
Great question — for a hackathon you should absolutely stand on shoulders. Here's what maps to Sofa Genius:

### Agent Brain: Claude Agent SDK (Python)
This is the **strongest pick** since it's an Anthropic hackathon. The SDK gives you the same agent loop powering Claude Code — intent routing, planning, tool execution — all built in. The killer feature: you define your tools (W&B, SQL, Scout) as **in-process MCP servers** using a `@tool` decorator. No subprocess management, no orchestration boilerplate.

This replaces what you'd otherwise build from scratch: the Intent Router, Planner, and Tool Executor layers from your architecture section.

→ [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python) | [Custom Tools Docs](https://platform.claude.com/docs/en/agent-sdk/custom-tools) | [MCP Docs](https://platform.claude.com/docs/en/agent-sdk/mcp)

### Voice Mode: Pipecat (by Daily)
Open-source Python framework for voice + multimodal AI. Handles push-to-talk, STT → LLM → TTS pipeline with WebSocket/WebRTC low-latency streaming. Integrates with Whisper for transcription and various TTS providers. This gives you **Mode A (Sofa Mode)** without building a voice pipeline from scratch.

**Hackathon shortcut:** If Pipecat feels like too much wiring, use the **browser's Web Speech API** for push-to-talk STT and a simple TTS library. Less polished, but ships in an hour.

→ [Pipecat GitHub](https://github.com/pipecat-ai/pipecat)

### 🔌 Tool Connectors (your MCP tools)

| Tool | Library | Effort |
|------|---------|--------|
| W&B Monitor | `wandb` Public API — `api.runs()`, `run.summary`, `run.scan_history()` | ~1hr |
| SQL Analyst | `sqlite3` or `duckdb` (embed a demo dataset, zero setup) | ~30min |
| HF Scout | `huggingface_hub` — `HfApi().list_models(search=...)` | ~30min |
| Modal Launch | `modal` CLI or just generate the command string (fallback) | ~30min |

Each becomes a `@tool`-decorated function in the Claude Agent SDK. The SDK handles calling them when the LLM decides to.

### 💻 Frontend: Vite + React + TypeScript
- **Vite** — build tool and dev server (instant HMR, zero-config)
- **React** — UI library
- **Framer Motion** — animations (card transitions, stepper progress, mode switches)
- **TypeScript** — type checking
- **Recharts or Plotly** — metric charts for W&B Health Card / Data Card

For the Chat + Cards layout:
- **Left panel:** chat thread — stream Claude responses via `fetch` + `ReadableStream` from the Python backend
- **Right panel:** render Card components (W&B Health Card, Data Card, etc.) from structured JSON the agent returns
- **Task Runner panel:** a simple stepper component tracking Proposed → Approved → Executed

## What You DON'T Need to Build

| Sofa Genius Component | Framework Handles It |
|---|---|
| Intent Router | Claude Agent SDK — the LLM routes to the right tool naturally |
| Planner | Claude Agent SDK — plan is implicit in tool-use chain |
| Tool Executors | MCP custom tools — just write the Python functions |
| Artifact Builder | Have the LLM return structured JSON → frontend renders cards |
| Agent loop / retries | Claude Agent SDK handles the full loop |

## What About OpenManus?

[OpenManus](https://github.com/FoundationAgents/OpenManus) is a general-purpose agent framework from the MetaGPT team. It's interesting but **overkill for a hackathon** — it's designed for browser automation and complex multi-step tasks. Your tools are well-defined (W&B, SQL, HF), so the lighter Claude Agent SDK + custom tools approach is faster to ship and scores better on the **"Opus 4.6 Use"** judging criteria.

## TL;DR Build Order with Frameworks

| ID  | What                                | Framework                                              |
| --- | ----------------------------------- | ------------------------------------------------------ |
| 1   | Agent + W&B Monitor flow end-to-end | Claude Agent SDK + `wandb` API + Vite/React chat UI |
| 2   | SQL Analyst + Cards UI              | `duckdb` + Card components in React                    |
| 3   | Scout + Draft + Voice polish        | `huggingface_hub` + Pipecat or Web Speech API          |

The Claude Agent SDK does the heavy lifting on orchestration so you can focus on the **demo experience** — which is 30% of your score.

Sources:
- [Claude Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Agent SDK Python GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude Agent SDK Custom Tools](https://platform.claude.com/docs/en/agent-sdk/custom-tools)
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Pipecat - Voice AI Framework](https://github.com/pipecat-ai/pipecat)
- [W&B Python API Docs](https://docs.wandb.ai/ref/python/public-api/api/)
- [OpenManus GitHub](https://github.com/FoundationAgents/OpenManus)