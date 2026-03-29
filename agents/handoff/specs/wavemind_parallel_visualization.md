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

### Approach: Template + JSON (Builder's recommendation)

The slow part is Claude writing ~500 lines of HTML, not the analysis. The simplest fix: extract the HTML as a static template with placeholders, Claude outputs JSON analysis only, a script does string replacement. No Jinja2, no Agent SDK, no coordinator needed.

### 1. HTML Template

Extract the approved layout from the reference visual into a static template:
- **Reference:** `agents/skills/wavemind/data/visuals/20260329-rethinking-multiagent.html`
- Simple placeholder syntax (e.g., `{{TITLE}}`, `{{SECTIONS}}`)
- Template takes a JSON analysis and renders the full page via string replacement
- All CSS/JS stays inline (self-contained HTML output)
- The template handles: header metadata, timeline layout, dialogue bubbles, pivot badges, quote callouts, transcript toggles, responsive styles

### 2. Analysis (Claude's only job)

Claude reads the artifact and outputs structured JSON. No HTML generation:

```json
{
  "title": "Title from user's perspective",
  "date": "2026-03-29",
  "participants": "Lily + CEO",
  "sections": [
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
  ]
}
```

Editorial rules:
- `header`: From user's perspective. BAD: "Discussion of X." GOOD: "I Was the Taste Person All Along"
- `quote`: Real speaker quote, not generated. The memory hook.
- `dialogue`: One thought per bubble. Clean filler, preserve original words (including mixed Chinese/English).
- `is_pivoting_moment`: True only when thinking genuinely shifted direction.

### 3. Render Script

A simple shell or Python script that:
1. Reads the JSON analysis from stdin or a file
2. Does string replacement into the HTML template
3. Writes the final `.html` file

No AI, no SDK, no parallelism needed at this stage. If the template approach isn't fast enough, we can add parallelism later.

## Files

- Template: `agents/skills/wavemind/lib/template.html`
- Render script: `agents/skills/wavemind/lib/render.sh` (or `.py`)
- Reference visual: `agents/skills/wavemind/data/visuals/20260329-rethinking-multiagent.html`
- Reference artifact: `agents/skills/wavemind/data/artifacts/20260329-rethinking-multiagent.md`

## Success Criteria

- Visualization takes under 60 seconds (down from 4-5 min)
- Output quality matches or exceeds the reference visual
- Works with any artifact that follows the `## Round N` format
- Template is easy to tweak without touching AI code

## Notes

The reference visual and artifact are in `agents/skills/wavemind/data/` (committed as examples per Lily's request).
