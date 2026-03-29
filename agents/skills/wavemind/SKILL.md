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
Generate a beautiful HTML thought evolution map from a stored artifact.

**Steps:**
1. Read the artifact from `agents/skills/wavemind/data/artifacts/<id>.md`
2. Analyze the thinking artifact deeply:
   - Identify distinct rounds/sections of the conversation
   - Find **turning points** — moments where thinking shifted direction
   - Extract **key insights** — the most important realizations
   - Map **connections** between ideas across rounds
   - Identify the **narrative arc** — how thinking evolved from start to end
3. Generate a structured analysis as JSON (see Analysis Format below)
4. Generate a beautiful, self-contained HTML file that visualizes the thought evolution
   - Use modern CSS with a clean, editorial aesthetic
   - Include: timeline of rounds, turning point highlights, insight cards, connection lines
   - Make it visually impressive — this is the "wow factor"
   - The HTML must be fully self-contained (inline CSS/JS, no external dependencies)
5. Save to `agents/skills/wavemind/data/visuals/<id>.html`
6. Report the key findings and file path

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
  "title": "Descriptive title of the thinking session",
  "rounds": 7,
  "word_count": 3200,
  "narrative_arc": "Brief description of how thinking evolved from start to end",
  "turning_points": [
    {
      "round": 3,
      "from": "Previous direction",
      "to": "New direction",
      "trigger": "What caused the shift"
    }
  ],
  "key_insights": [
    {
      "title": "Short insight name",
      "description": "What was realized",
      "round": 5,
      "significance": "Why this matters"
    }
  ],
  "connections": [
    {
      "from": "Idea or round",
      "to": "Connected idea or round",
      "relationship": "How they connect"
    }
  ]
}
```

## HTML Visual Guidelines

When generating the HTML visualization:

- **Style:** Clean, modern, editorial. Think high-end blog or research publication.
- **Color palette:** Dark background (#1a1a2e) with accent colors for turning points (#e94560) and insights (#0f3460). Use gradients sparingly.
- **Typography:** System fonts, generous whitespace, clear hierarchy.
- **Layout:**
  - Header: title, date, round count, one-line narrative arc
  - Timeline: vertical timeline showing each round with brief summary
  - Turning points: highlighted cards breaking out of the timeline
  - Insights: cards with connections drawn between related ones
  - Footer: full narrative arc summary
- **Self-contained:** All CSS and JS must be inline. No external dependencies.
- **Responsive:** Should look good on both desktop and mobile.

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
