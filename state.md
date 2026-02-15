# Sofa Genius — Project State

## Phase 1: W&B Monitor (Complete)
- Full-stack app: FastAPI backend + Vite/React/TypeScript frontend
- Anthropic tool_use agent loop with SSE streaming
- 4 W&B tools: get_wandb_info, list_wandb_runs, get_run_metrics, analyze_run_health
- 7 anomaly detectors: spike, divergence, oscillation, grad explosion, overfitting, plateau, NaN
- Auto-discovery of W&B entity (username) and metric keys from run history
- Two-panel UI: chat (left) + Health Card with Recharts plots (right)
- Markdown rendering in chat, conversation history for multi-turn
- New Chat button, custom user avatar, design system (cream/gold/stone palette)

## Phase 2: Data/SQL Analyst (Complete)

### Design

**Goal:** Let researchers inspect HuggingFace datasets via natural language. User says "analyze dataset X" → agent discovers schema → writes SQL → executes via DuckDB → DataCard renders with table, stats, plot, and suggested next queries.

**Demo flow:**
1. "Find me datasets for fine-tuning Qwen2.5-Coder-14B" → agent searches HF Hub → numbered list
2. "Check out the first one" → agent discovers schema → shows columns/types/row count
3. "Show me a sample of 10 rows" → agent runs SQL → DataCard appears with table + stats + plot

**Architecture (extends Phase 1):**
```
backend/tools/                    frontend/src/components/
├── wandb_monitor.py (Phase 1)   ├── WandBHealthCard.tsx (Phase 1)
└── sql_analyst.py (Phase 2)     ├── DataCard.tsx (Phase 2)
                                 ├── DataTable.tsx (Phase 2)
                                 └── DataPlot.tsx (Phase 2)
```
Same pattern as Phase 1: tool functions return Pydantic JSON → agent emits SSE card events → frontend renders by `card_type` discriminator.

**Backend tools (6 functions in `sql_analyst.py`):**
1. `search_hf_datasets(query)` — Search HF Hub API, return ranked list with name/downloads/tags
2. `discover_dataset_schema(dataset_path)` — `DESCRIBE SELECT *` + sample values + row count. Auto-normalizes paths: `"user/dataset"` → `"hf://datasets/user/dataset/train.parquet"`
3. `run_sql_query(dataset_path, sql_query)` — Execute SQL via DuckDB. Auto-inject `LIMIT 1000` if missing. SELECT-only.
4. `compute_stats(query_result_json)` — mean/std/min/max for numeric cols, unique_count/top_values for categorical
5. `generate_plot_data(query_result_json, plot_type="auto")` — Auto-detect: 1 numeric → histogram, categorical+numeric → bar (sorted by leading number), 2 numeric → scatter
6. `create_data_card(...)` — Assemble into DataCard, emit via SSE

**Backend models (`models.py`):**
- `ColumnInfo` — name, type, sample_values
- `QueryResult` — columns, rows, row_count, execution_time_ms, truncated
- `StatsSummary` — per-column stats (numeric or categorical)
- `PlotData` — plot_type, title, x/y labels, x/y values
- `DataCard` — card_type="data_card", title, dataset_path, sql_query, summary, query_result, stats, plot, next_suggestions

**Frontend components:**
- `DataCard.tsx` — Header with "Data Analysis" label + blue row count badge, gold divider, summary, collapsible SQL block, expandable details (plot → stats grid → table → suggested queries)
- `DataTable.tsx` — Stone header, hover rows, 4-decimal numbers, italic nulls, 100-row cap
- `DataPlot.tsx` — Recharts wrapper for bar/line/scatter/histogram with gold palette

**Agent integration (`agent.py`):**
- 10 tool schemas + dispatch (4 W&B + 6 data)
- System prompt with enforced workflow: schema → SQL → stats → plot → create_data_card (MUST always finish with card)
- `tool_result` SSE events with brief summaries for stepper UI
- Text emitted before tool calls (not after) for correct interleaving

**UX improvements made during Phase 2:**
- Interleaved message segments: text and tool steps render in order (not concatenated)
- Tool stepper: each tool call shows as a step with spinner/checkmark/error + result summary
- Bar chart smart sorting: numeric range labels (0-5k, 5k-10k, ...) sorted by leading number

### Summary
- 6 SQL/search tools + DuckDB `hf://` protocol — reads HF Parquet files directly, no downloads
- DataCard with collapsible plot, stats grid, results table, suggested next queries
- HF Hub search for dataset discovery
- SQL safety: SELECT-only, auto-LIMIT injection, fresh DuckDB connections per call
- Total: 10 tools across 2 domains (W&B + Data)

## Scope & Focus
- **Primary focus:** Coding agents — datasets for fine-tuning code models (e.g. Qwen2.5-Coder-14B)
- Phase 2 handles **tabular/Parquet data** via DuckDB SQL. Image datasets are out of scope for now.
- Image dataset support (if needed later): use HF dataset viewer API (`datasets-server.huggingface.co/rows`) for thumbnails. Would need a new tool + image preview card component. Not prioritized since coding datasets are text/code.

## Remaining (Non-Urgent)
- Action buttons on Health Card are visual-only (no onClick handlers)
- No persistent chat history (refreshing the page clears everything)
- No loading skeleton for cards while tools execute
- Example queries in empty state are hardcoded, could adapt to user's projects

## Known Bugs
- Claude occasionally still leaks partial JSON into chat text despite regex stripping
- If W&B API key is invalid/missing, error message is generic ("something went wrong")
- Conversation history grows unbounded — no truncation for long sessions, may hit token limits

## Architecture Decision: Subagents (Phase 4)

**Decision: Refactor to subagents when adding the Launch Agent in Phase 4.** That's the inflection point where tool count crosses ~15 and three distinct domains exist.

A subagent is a separate Claude conversation spawned by a parent "orchestrator" agent. Each gets its own system prompt, tool set, and context window.

```
User
  └─> Orchestrator Agent (routes intent)
        ├─> Data Agent (DuckDB, HF datasets — 5 tools)
        ├─> Training Agent (W&B monitoring — 4 tools)
        └─> Launch Agent (Modal jobs — TBD tools)
```

### Tradeoffs

| | Single agent (current) | Subagents |
|---|---|---|
| **Simplicity** | Simpler, one agent loop | More code to manage |
| **Latency** | One conversation | Extra LLM call for routing |
| **Tool reliability** | Degrades as tools grow (15-20+) | Each agent stays focused with fewer tools |
| **Context window** | All tool results compete for space | Each agent has its own context |
| **Cross-domain queries** | Easy ("compare dataset X with run Y") | Orchestrator must coordinate between agents |
| **System prompt** | Gets long/conflicting with mixed domain rules | Each agent gets a focused, clean prompt |
| **Error isolation** | One bad tool call can derail the conversation | Subagent failures are contained |

### Analysis
- At 9 tools (Phase 2), the flat approach works fine.
- At 15-20+ tools (Phase 4), tool confusion and prompt bloat become real problems.
- Tools are already cleanly separated by file (`wandb_monitor.py`, `sql_analyst.py`), making each file a natural subagent toolset.
- The hardest part is **cross-domain queries** (e.g., "my run is overfitting, find me a bigger dataset"). The orchestrator needs to chain subagents: Training Agent diagnoses → Data Agent scouts.

### Implementation sketch for Phase 4
1. Create `backend/orchestrator.py` — lightweight router with tools like `delegate_to_data`, `delegate_to_training`, `delegate_to_launch`
2. Each subagent gets its own system prompt and tool list (already separated by file)
3. Orchestrator calls Claude once to classify intent, spawns the right subagent
4. Subagent does its multi-step tool loop, returns final card JSON
5. Orchestrator relays card + summary to user via SSE
6. For cross-domain queries, orchestrator chains subagents sequentially

## Next Up
- **Phase 3:** Scout + Draft — HF dataset shortlist + draft post with evidence
- **Phase 4:** Launch Agent (Modal) — this is when subagent refactor happens
- Stream token-by-token instead of waiting for full text block (true SSE streaming with Anthropic SDK)
- Voice mode (Pipecat / Web Speech API)
- Task Runner stepper UI (Proposed → Approved → Executed)
- Rate limiting / caching for API calls
- Evaluate Hashbrown or similar for dynamic AI-generated UI components