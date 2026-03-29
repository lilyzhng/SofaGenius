---
name: wavemind
description: Turn thinking artifacts (conversation transcripts, brainstorm notes) into beautiful visual thought evolution maps. Capture, visualize, and list your thinking process.
argument-hint: capture [filepath] | visualize <id> | list | today | add "<task>" | done <id> | habit | week
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# WaveMind — Thought Capture + Visualization

Transform thinking artifacts into beautiful visual maps of how your ideas evolved.

## Commands

### `/wavemind capture [filepath]`
Capture a thinking artifact. Two modes:

**Mode 1: Import existing file** (`/wavemind capture <filepath>`)
1. Read the file at `<filepath>`
2. Analyze the content to extract: title, round count, word count, source type
3. Generate a short ID from the date and title (e.g., `20260327-zai-prep`)
4. Run `bash agents/skills/wavemind/lib/capture.sh <filepath> "<title>"` to copy and index it
5. Report what was captured

**Mode 2: Live capture** (`/wavemind capture` or `/wavemind capture "Topic Name"`)
When no filepath is given, start a live capture session:
1. Ask the user for a topic name if not provided
2. Create the artifact file immediately: `agents/skills/wavemind/data/artifacts/<id>.md` with title and metadata header
3. Tell the user: "Recording this conversation. Talk naturally. When you're done, say 'done' or 'save'."
4. Continue the conversation normally, responding as you would to any request
5. **Capture incrementally, not at the end.** After each round (a topic reaches a natural pause, the user moves to a new question, or a decision is made), append that round to the artifact file right away. Each round gets:
   - A section header: `## Round N: Title`
   - The raw dialogue with `**Speaker:**` labels
   - Original words preserved (including mixed languages). Fix obvious typos but do not rewrite or summarize.
   - This avoids the lossy "reconstruct everything from memory at the end" problem.
6. When the user says "done", "save", or "stop recording":
   - Append any remaining conversation not yet written
   - Run `bash agents/skills/wavemind/lib/capture.sh` to finalize and index it
   - Report: artifact ID, title, round count, word count, file path
   - Suggest: "Run `/wavemind visualize <id>` to generate the visual."

### `/wavemind visualize <artifact-id>`
Generate a living memory document from a stored thinking artifact.

**Steps:**
1. Read the artifact: `bash agents/skills/wavemind/lib/visualize.sh read <id>`
2. Analyze the thinking artifact. Your job is **editorial, not generative**:
   - Identify distinct rounds/sections of the conversation
   - Extract **punchline quotes** from each speaker (real words, not generated)
   - Mark **pivoting moments** where thinking shifted direction
   - Clean up the transcript: remove filler, fix noise, preserve original words
   - Do NOT summarize, generate insights, or create new content
3. Output a JSON analysis (see Analysis Format below). Save it to a temp file:
   `agents/skills/wavemind/data/visuals/<id>.json`
4. Run the render script to produce HTML from JSON:
   `python3 agents/skills/wavemind/lib/render.py agents/skills/wavemind/data/visuals/<id>.json agents/skills/wavemind/data/visuals/<id>.html`
5. Mark as visualized: `bash agents/skills/wavemind/lib/visualize.sh done <id>`
6. Report the file path

### `/wavemind list`
Browse all stored thinking artifacts and their visualization status.

**Steps:**
1. Read `agents/skills/wavemind/data/index.json`
2. Display a formatted table:

```
ID                          | Title                  | Rounds | Date       | Status
20260327-zai-prep           | ZAI Ambassador Prep    | 11     | 2026-03-27 | visualized
20260329-design-evolution   | Design Evolution       | 6      | 2026-03-29 | not visualized
```

3. If no artifacts exist, say "No artifacts captured yet. Run `/wavemind capture` to start."

### `/wavemind today`
Show today's tasks and habit progress. A daily command center.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh today`
2. Display the output to the user

### `/wavemind add "<task>"`
Add a task to today's list.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh add "<task description>"`
2. Confirm what was added

### `/wavemind done <id>`
Mark a task as complete.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh done <task-id>`
2. Then run `bash agents/skills/wavemind/lib/tasks.sh today` to show updated status

### `/wavemind habit`
Show recurring habit status for today.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh habit`
2. Display the output

### `/wavemind habit-log <habit-id> [count]`
Log progress on a recurring habit.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh habit-log <habit-id> [count]`
2. Confirm the logged progress

### `/wavemind week`
Weekly review of task completion across the past 7 days.

**Steps:**
1. Run `bash agents/skills/wavemind/lib/tasks.sh week`
2. Display the output

## Analysis Format

When analyzing a thinking artifact, produce this structure:

```json
{
  "title": "Title from the user's perspective",
  "date": "2026-03-27",
  "participants": "Lily + Growth",
  "sections": [
    {
      "round": 1,
      "header": "High-signal title from user's perspective",
      "quote": "Memorable speaker quote, max 10 words",
      "dialogue": [
        {"speaker": "lily", "text": "One thought per bubble. Keep it short."},
        {"speaker": "growth", "text": "Response in their original words."}
      ],
      "is_pivoting_moment": false,
      "raw_transcript": "Full original text for each speaker, separated by double newlines. Use Speaker: prefix format."
    }
  ],
  "actionables": {
    "why_it_matters": "One paragraph explaining why this conversation mattered and what shifted.",
    "items": [
      "Concrete next step 1",
      "Concrete next step 2",
      "Concrete next step 3"
    ]
  }
}
```

**Key rules:**
- `header`: High-signal, from the user's perspective. BAD: "Discussion of Opportunity." GOOD: "I'm the Orchestrator, Not the Promoter."
- `quote`: A real speaker quote, not AI-generated. The "memory hook" for what you'd remember a week later.
- `dialogue`: The actual back-and-forth, one thought per bubble. Use original words (including mixed Chinese/English). Clean filler but don't rewrite.
- `is_pivoting_moment`: True only when thinking genuinely shifted direction. Not every round is a pivot.
- `raw_transcript`: Full clean transcript for the expandable "Read original" section. Use `Speaker:` prefix, separate paragraphs with double newlines. Preserve original words.
- `speaker` values in dialogue: Use display names (e.g., "Lily", "Growth", "Builder"). The first participant listed in `participants` is rendered as the user (left-aligned bubbles), all others as the other speaker (right-aligned bubbles).
- `actionables`: Always include. `why_it_matters` is a single paragraph explaining significance. `items` are concrete, specific next steps that came out of the conversation. Not vague ("think about X") but actionable ("build X", "pair Y with Z", "test A").

**Important:** You only output JSON. The render script (`lib/render.py`) handles all HTML generation from the template (`lib/template.html`). Do NOT write HTML directly.

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
