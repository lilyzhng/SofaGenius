# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sofa Genius is a research agent for an Anthropic hackathon. It lets researchers delegate procedural work (data inspection, W&B monitoring, dataset scouting, post drafting) via voice or chat. Core UX: speak a goal -> get an actionable brief -> approve -> agent executes -> get alerts + summary.

**Status:** Design phase. The spec lives in `Hackathon - Sofa Genius.md`.

## Planned Tech Stack

- **Backend:** Python, Claude Agent SDK (tools defined via `@tool` decorator as in-process MCP servers)
- **Frontend:** Vite + React + TypeScript, Framer Motion (animations), Recharts or Plotly (charts)
- **Voice:** Pipecat (or browser Web Speech API as fallback)
- **Tool connectors:** `wandb` (monitoring), `sqlite3`/`duckdb` (SQL), `huggingface_hub` (scouting), `modal` (job launch)

## Architecture

### Three Modes
- **Mode A (Audio/Sofa Mode):** Hands-free. Response in <=30s. Format: 1-line verdict + 2 findings + 1 decision question.
- **Mode B (Chat + Cards):** Left panel = chat thread, right panel = visual Card components rendered from agent-returned JSON.
- **Mode C (Task Runner):** One-click flows with stepper UI (Proposed -> Approved -> Executed).

### Backend Layers (Claude Agent SDK handles orchestration)
- Intent routing, planning, and tool execution are handled by the SDK
- Custom `@tool` functions: W&B connector, SQL connector, HF Scout connector, Modal launcher
- Agent returns structured Card JSON; frontend renders it

### Data Models
- **Task:** {id, mode, flow_type, status, checkpoints[]}
- **Card:** {type, title, summary, evidence[], actions[]} — types: W&B Health, Data, Scout, Run Brief, Draft Post
- **Evidence:** {source, snippet/metric, link}
- **Action:** {label, risk_level, requires_approval, payload}

### Frontend Layout
- Left panel: chat thread streaming Claude responses via `fetch` + `ReadableStream`
- Right panel: Card components (W&B Health Card, Data Card, etc.)
- Task Runner panel: stepper component

## Build Order (Priority)

1. **Phase 1 (must work e2e):** W&B Monitor Run — Health Card + anomaly detector
2. **Phase 2:** Data/SQL Analyst — one dataset + NL->SQL + one plot
3. **Phase 3:** Scout + Draft — shortlist + draft post with evidence
4. **Phase 4 (if time):** Voice mode handoff (audio -> auto-create cards)

## Anomaly Detection Heuristics (Rule-Based)

- **Loss spike:** loss(t) > mean(last N) + 3*std
- **Divergence:** monotonic loss increase for M steps
- **Oscillation:** high variance above threshold for window W
- **Gradient explosion:** grad_norm above threshold
- **Overfitting:** train_loss decreasing while eval_loss increasing for K eval points
- **Plateau:** improvement < epsilon for T steps
- **Data issues:** NaNs in metrics, sudden metric reset

Each detector outputs: symptom -> likely cause -> suggested action.

## Visual Design System

All new UI must follow these conventions.

### Color Palette
- **Background:** `#F9F8F4` (warm cream) as primary, `#F5F4F0` for secondary surfaces, white for content sections
- **Accent:** `nobel-gold` = `#C5A059` — used for highlights, dividers, badges, active states, and interactive elements
- **Text:** `stone-900` for headings, `stone-600`/`stone-500` for body/secondary text
- **Dark sections:** `stone-900` bg with `stone-100`/`stone-400` text, `nobel-gold` for accents
- **Functional colors:** blue/red/green only for semantic states (errors, status indicators), not decoration

### Typography
- **Serif:** `Playfair Display` — headings, hero text, quotes, large display text
- **Sans:** `Inter` — body text, labels, navigation, UI controls
- **Labels/tags:** uppercase, `text-xs`, `font-bold`, `tracking-widest` or `tracking-[0.2em]`
- Loaded from Google Fonts

### Component Patterns
- **Cards:** `bg-white rounded-xl border border-stone-200 shadow-sm hover:shadow-md transition-all duration-300`
- **Gold divider accent:** `w-16 h-1 bg-nobel-gold` (or `w-12 h-0.5`) used under headings
- **Pill badges:** `px-3 py-1 border border-nobel-gold text-nobel-gold text-xs tracking-[0.2em] uppercase font-bold rounded-full`
- **Primary buttons:** `px-5 py-2 bg-stone-900 text-white rounded-full hover:bg-stone-800`
- **Toggle/tab buttons:** stone border when inactive, `bg-nobel-gold text-stone-900` when active
- **Blockquotes:** `p-6 bg-[#F9F8F4] border border-stone-200 rounded-lg border-l-4 border-l-nobel-gold` with `font-serif italic`

### Layout
- Container: `container mx-auto px-6`
- Sections: `py-24`, alternating white / cream (`#F9F8F4`) / dark (`stone-900`) backgrounds
- Content grids: 12-column (`grid-cols-12`) for asymmetric layouts (e.g., 4-col heading + 8-col body)
- Section headers: small uppercase label + serif heading + gold divider bar

### Animation
- Use Framer Motion for transitions (spring physics: `stiffness: 80, damping: 15`)
- Staggered entry animations with `animationDelay`
- Subtle hover states: shadow elevation, border color shifts (`hover:border-nobel-gold/50`)

### Libraries (Frontend)
- **Tailwind CSS** (via CDN in prototype, install as dependency for production)
- **Framer Motion** — all animations and transitions
- **Lucide React** — icons (e.g., `ArrowDown`, `Menu`, `X`, `BookOpen`, `Activity`, `Cpu`, `BarChart2`)
- **React Three Fiber + @react-three/drei** — 3D scenes (hero backgrounds, decorative visuals)

## Guardrails

- Human-in-the-loop required for: launching jobs (costs money), stopping/restarting runs, posting publicly
- Claims without evidence must be labeled "Hypothesis" not "Finding"
- Every proposed change must include undo/revert instructions
