---
from: ceo
to: jackie
priority: high
created: 2026-03-29
status: ready
guidance_from: builder
---

# WaveMind: Parallel Visualization with Templates

## Problem

`/wavemind visualize` takes 4-5 minutes because the agent writes ~500 lines of HTML from scratch every time. The editorial layout is now stable and proven. The AI work (analyzing rounds, picking quotes, detecting pivots) is independent per round and should run in parallel.

## Goal

Make visualization fast by separating two concerns:
1. **Editorial analysis** (AI work) — per-round, parallelizable
2. **HTML rendering** (template work) — deterministic, no AI needed

## What to Build

### 1. HTML Template

Extract the approved layout from the reference visual into a reusable template:
- **Reference:** `agents/skills/wavemind/data/visuals/20260329-rethinking-multiagent.html`
- Use Jinja2 or Handlebars-style templating
- Template takes a JSON array of analyzed rounds and renders the full page
- All CSS/JS stays inline (self-contained HTML output)
- The template handles: header metadata, timeline layout, dialogue bubbles, pivot badges, quote callouts, transcript toggles, responsive styles

### 2. Parallel Round Analyzer

Use Claude Agent SDK (or Claude Code sub-agents) to analyze rounds in parallel:
- Input: one round of raw dialogue (markdown)
- Output: structured JSON per the existing analysis format:

```json
{
  "round": 1,
  "header": "High-signal title from user's perspective",
  "quote": "Memorable speaker quote, max 10 words",
  "dialogue": [
    {"speaker": "lily", "text": "One thought per bubble."},
    {"speaker": "ceo", "text": "Response in original words."}
  ],
  "is_pivoting_moment": false,
  "raw_transcript": "Full original text for the expandable section"
}
```

Each round analyzer is a small, focused prompt. The editorial rules:
- `header`: From user's perspective. BAD: "Discussion of X." GOOD: "I Was the Taste Person All Along"
- `quote`: Real speaker quote, not generated. The memory hook.
- `dialogue`: One thought per bubble. Clean filler, preserve original words (including mixed Chinese/English).
- `is_pivoting_moment`: True only when thinking genuinely shifted direction.

### 3. Coordinator Script

A script (Python or Node) that:
1. Reads the artifact markdown
2. Splits into rounds (by `## Round N` headers)
3. Spawns parallel analysis agents (one per round)
4. Collects all JSON results
5. Feeds them into the HTML template
6. Writes the final `.html` file

Could be a standalone CLI: `python wavemind_visualize.py <artifact-id>`

Or integrated into the existing skill flow so `/wavemind visualize` uses it under the hood.

## Architecture Decision: Agent SDK vs. Claude Code Sub-agents

Two options. Get Builder's input on which is more practical:

**Option A: Claude Agent SDK standalone script**
- Runs as a Python script in terminal
- Uses `claude_agent_sdk` to spawn parallel workers
- Fully self-contained, can run outside Claude Code
- Pros: true parallelism, reusable, testable
- Cons: needs SDK setup, separate from skill flow

**Option B: Claude Code sub-agents (Agent tool)**
- The skill prompt instructs Claude Code to spawn sub-agents via Agent tool
- Each sub-agent gets one round
- Pros: no new infrastructure, works within existing skill
- Cons: still runs within Claude Code session, may not be truly parallel

Recommend Option A for speed, but get Builder's take.

## Files

- Template: `agents/skills/wavemind/lib/template.html`
- Coordinator: `agents/skills/wavemind/lib/visualize.py` (or `.js`)
- Reference visual: `agents/skills/wavemind/data/visuals/20260329-rethinking-multiagent.html`
- Reference artifact: `agents/skills/wavemind/data/artifacts/20260329-rethinking-multiagent.md`

## Success Criteria

- Visualization takes under 60 seconds (down from 4-5 min)
- Output quality matches or exceeds the reference visual
- Works with any artifact that follows the `## Round N` format
- Template is easy to tweak without touching AI code

## Notes

The reference visual and artifact are being pushed in PR alongside this spec so you can use them directly as test fixtures.
