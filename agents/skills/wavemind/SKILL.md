---
name: wavemind
description: Turn thinking artifacts (conversation transcripts, brainstorm notes) into beautiful visual thought evolution maps. Capture, visualize, and review your thinking process.
argument-hint: capture <filepath> | visualize <id> | review
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# WaveMind — Thought Capture + Visualization

Transform thinking artifacts into beautiful visual maps of how your ideas evolved.

## Commands

### `/wavemind capture <filepath>`
Save a thinking artifact (markdown transcript, conversation log, brainstorm notes) to the local store.

**Steps:**
1. Read the file at `<filepath>`
2. Analyze the content to extract: title, round count, word count, source type
3. Generate a short ID from the date and title (e.g., `20260327-zai-prep`)
4. Copy the file to `agents/skills/wavemind/data/artifacts/<id>.md`
5. Update `agents/skills/wavemind/data/index.json` with metadata
6. Report what was captured

### `/wavemind visualize <artifact-id>`
Generate a living memory document from a stored thinking artifact.

**Steps:**
1. Read the artifact from `agents/skills/wavemind/data/artifacts/<id>.md`
2. Analyze the thinking artifact — the AI's job is **editorial, not generative**:
   - Identify distinct rounds/sections of the conversation
   - Extract **punchline quotes** — memorable original words from each speaker
   - Mark **pivoting moments** — where thinking shifted direction
   - Clean up the transcript — remove filler, fix noise, preserve original words
   - Do NOT summarize, generate insights, or create new content
3. Generate a structured analysis as JSON (see Analysis Format below)
4. Generate a self-contained HTML file following the NoteBlock editorial layout:
   - Each section has: header, dialogue bubbles, punchline quote callout, expandable transcript
   - First-person perspective — it's the user's living memory, not a third-party report
   - Dialogue format with speech bubbles (user = white left-aligned, other speakers = dark right-aligned)
   - Progressive disclosure — punchline visible, full transcript behind "Read original" toggle
   - The HTML must be fully self-contained (inline CSS/JS, no external dependencies)
5. Save to `agents/skills/wavemind/data/visuals/<id>.html`
6. Report the file path

### `/wavemind review`
Browse all stored thinking artifacts and their visualization status.

**Steps:**
1. Read `agents/skills/wavemind/data/index.json`
2. For each artifact, check if a corresponding visual exists in `data/visuals/`
3. Display a formatted list with: ID, title, round count, date, visualization status

## Analysis Format

When analyzing a thinking artifact, produce this structure:

```json
{
  "title": "Title from the user's perspective",
  "date": "2026-03-27",
  "participants": "Lily + CEO",
  "sections": [
    {
      "round": 1,
      "header": "High-signal title from user's perspective",
      "quote": "Memorable speaker quote, max 10 words",
      "dialogue": [
        {"speaker": "lily", "text": "One thought per bubble. Keep it short."},
        {"speaker": "ceo", "text": "Response in their original words."}
      ],
      "is_pivoting_moment": false
    }
  ]
}
```

**Key rules:**
- `header`: High-signal, from the user's perspective. BAD: "Discussion of Opportunity." GOOD: "I'm the Orchestrator, Not the Promoter."
- `quote`: A real speaker quote, not AI-generated. The "memory hook" — what you'd remember a week later.
- `dialogue`: The actual back-and-forth, one thought per bubble. Use original words (including mixed Chinese/English). Clean filler but don't rewrite.
- `is_pivoting_moment`: True only when thinking genuinely shifted direction — not every round is a pivot.

## HTML Visual Guidelines

When generating the HTML visualization:

- **Style:** Clean, editorial. Think newspaper or literary journal, not dashboard.
- **Color palette:** Cream background (#F9F8F6), charcoal text (#1A1918), gold accents (#CBA16E).
- **Typography:** Serif for headers and quotes (Playfair Display or Georgia), sans-serif for UI (Inter or system). Generous whitespace.
- **Layout — NoteBlock model:**
  - **Header:** Title (large serif), date, participants, "Living Memory" label with gold dot
  - **Timeline:** Vertical gold line at ~28% width. Each section is a grid row.
  - **Left column (28%):** Round label, punchline quote callout (large gold open-quote mark, bold italic serif)
  - **Right column:** Section header (bold serif), dialogue bubbles, "Read original" toggle
  - **Dialogue bubbles:** User = white with light border, left-aligned. Other speakers = dark (#2C2C2C), right-aligned. One thought per bubble.
  - **Pivoting moments:** Gold-filled timeline dot + "Pivoting Moment" badge
  - **Progressive disclosure:** "Read original" expands to full clean transcript
  - **Footer:** Minimal — "WaveMind · Captured [date] · Visualized [date]"
- **Self-contained:** All CSS and JS must be inline. No external dependencies.
- **Responsive:** Hide quote callouts on mobile, switch to single-column layout.

**Reference:** See `agents/skills/wavemind/data/visuals/` for an approved example (ZAI Ambassador Prep).

## Data Directory

All runtime data lives in `agents/skills/wavemind/data/` (gitignored):

```
data/
├── .gitignore       # Keeps runtime data out of repo
├── index.json       # Artifact registry
├── artifacts/       # Raw markdown files
└── visuals/         # Generated HTML files
```

## Index Format

`index.json` is an array of artifact entries:

```json
[
  {
    "id": "20260327-zai-prep",
    "title": "ZAI Ambassador Prep",
    "source": "brainstorm",
    "tags": ["zai", "ambassador", "strategy"],
    "rounds": 11,
    "word_count": 3200,
    "created_at": "2026-03-27T00:00:00Z",
    "file": "artifacts/20260327-zai-prep.md",
    "visualized": true
  }
]
```
