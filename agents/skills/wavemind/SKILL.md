---
name: wavemind
description: Turn thinking artifacts (conversation transcripts, brainstorm notes) into beautiful visual thought evolution maps. Capture, visualize, and list your thinking process.
argument-hint: capture [filepath] | visualize <id> | list
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# WaveMind: Thought Capture + Visualization

Transform thinking artifacts into beautiful visual maps of how your ideas evolved.

## Commands

### `/wavemind capture [filepath]`
Capture a thinking artifact. Two modes:

**Mode 1: Import existing file** (`/wavemind capture <filepath>`)
1. Read the file at `<filepath>`
2. Analyze the content to extract: title, round count, word count, source type
3. Generate a short ID from the date and title (e.g., `20260327-zai-prep`)
4. Run `bash lib/capture.sh <filepath> "<title>"` to copy and index it
5. Report what was captured

**Mode 2: Live capture** (`/wavemind capture` or `/wavemind capture "Topic Name"`)
When no filepath is given, start a live capture session:
1. Ask the user for a topic name if not provided
2. Create the artifact file immediately: `data/artifacts/<id>.md` with this structure:
   ```markdown
   # Topic Name - YYYY-MM-DD

   **Participants:** Lily + Jackie
   **Topic:** Brief description

   ## Actionables
   <!-- Updated as action items emerge from conversation -->

   ---

   ## Round 1: Title
   **Lily:** ...
   **Jackie:** ...
   ```
3. Tell the user: "Recording this conversation. Talk naturally. When you're done, say 'done' or 'save'."
4. Continue the conversation normally, responding as you would to any request
5. **Capture incrementally, not at the end.** After each round (a topic reaches a natural pause, the user moves to a new question, or a decision is made), append that round to the artifact file right away. Each round gets:
   - A section header: `## Round N: Title`
   - The raw dialogue with `**Speaker:**` labels
   - Original words preserved (including mixed languages). Fix obvious typos but do not rewrite or summarize.
   - This avoids the lossy "reconstruct everything from memory at the end" problem.
   - **Images:** When the user shares a screenshot or image during the conversation, save it to `data/artifacts/` with a descriptive filename (e.g., `milli-cafe-session.png`). Embed it in the artifact markdown using `![description](filename.png)`. Place the image reference in the dialogue at the point it was shared, under the speaker who shared it.
   - **Actionables:** When action items emerge from the conversation (decisions made, tasks identified, next steps agreed), update the `## Actionables` section at the top of the file. Use `- [ ]` checkboxes. Group by category if natural. Actionables are a living section that grows as the conversation progresses, not something reconstructed at the end.
6. When the user says "done", "save", or "stop recording":
   - Append any remaining conversation not yet written
   - Do a final pass on the Actionables section to make sure all action items from the conversation are captured
   - Run `bash lib/capture.sh` to finalize and index it
   - Report: artifact ID, title, round count, word count, file path
   - Suggest: "Run `/wavemind visualize <id>` to generate the visual."

### `/wavemind visualize <artifact-id>`
Generate a living memory document from a stored thinking artifact.

**Steps:**
1. Read the artifact from `data/artifacts/<id>.md`
2. Analyze the thinking artifact. Your job is **editorial, not generative**:
   - Identify distinct rounds/sections of the conversation
   - Extract **punchline quotes** (memorable original words from each speaker)
   - Mark **pivoting moments** (where thinking shifted direction)
   - Clean up the transcript: remove filler, fix noise, preserve original words
   - Do NOT summarize, generate insights, or create new content
3. Generate a structured analysis as JSON (see Analysis Format below)
4. Generate a self-contained HTML file following the NoteBlock editorial layout:
   - Start with "What Came Out of This" actionables section right after the header (why it matters + action items)
   - Then the timeline with each section: header, dialogue bubbles, punchline quote callout, expandable transcript
   - First-person perspective. It's the user's living memory, not a third-party report
   - Dialogue format with speech bubbles (user = white left-aligned, other speakers = dark right-aligned)
   - Progressive disclosure: punchline visible, full transcript behind "Read original" toggle
   - The HTML must be fully self-contained (inline CSS/JS, no external dependencies)
5. Save to `data/visuals/<id>.html`
6. Report the file path

### `/wavemind list`
Browse all stored thinking artifacts and their visualization status.

**Steps:**
1. Read `data/index.json`
2. Display a formatted table:

```
ID                          | Title                  | Rounds | Date       | Status
20260327-zai-prep           | ZAI Ambassador Prep    | 11     | 2026-03-27 | visualized
20260329-design-evolution   | Design Evolution       | 6      | 2026-03-29 | not visualized
```

3. If no artifacts exist, say "No artifacts captured yet. Run `/wavemind capture` to start."

### `/wavemind action items`
Show actionables from today's artifacts, or the most recent artifact if none exist for today.

**Steps:**
1. Check today's date (YYYYMMDD format)
2. Look for today's artifacts in `data/artifacts/` matching `YYYYMMDD-*.md`
3. If found, read the `## Actionables` section from each artifact. If multiple artifacts exist for today, combine their actionables
4. If no artifacts for today, find the most recent artifact that has actionables
5. Display the action items with checkboxes
6. If the user wants to:
   - **Check off items:** Update the `## Actionables` section in the source artifact file, changing `- [ ]` to `- [x]`
   - **Add new items:** Append to the `## Actionables` section in the most recent artifact
7. After any changes, save the file immediately

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
        {"speaker": "lily", "text": "", "image": "screenshot.png", "image_alt": "Terminal color comparison"},
        {"speaker": "lily", "text": "Here's what it looked like after the fix:", "image": "after-fix.png", "image_alt": "Terminal after color fix"},
        {"speaker": "growth", "text": "Response in their original words."}
      ],
      "is_pivoting_moment": false
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
- `quote`: A real speaker quote, not AI-generated. The "memory hook," what you'd remember a week later.
- `dialogue`: The actual back-and-forth, one thought per bubble. Use original words (including mixed Chinese/English). Clean filler but don't rewrite. Entries with an `image` field render as an `<img>` tag inside the bubble instead of (or alongside) text.
- `is_pivoting_moment`: True only when thinking genuinely shifted direction. Not every round is a pivot.
- `actionables`: Always include. `why_it_matters` is a single paragraph explaining significance. `items` are concrete, specific next steps. Not vague ("think about X") but actionable ("build X", "pair Y with Z", "test A").

## HTML Visual Guidelines

When generating the HTML visualization:

- **Style:** Clean, editorial. Think newspaper or literary journal, not dashboard.
- **Color palette:** Cream background (#F9F8F6), charcoal text (#1A1918), gold accents (#CBA16E).
- **Typography:** Serif for headers and quotes (Playfair Display or Georgia), sans-serif for UI (Inter or system). Generous whitespace.
- **Layout (NoteBlock model):**
  - **Header:** Title (large serif), date, participants, "Living Memory" label with gold dot
  - **Actionables (right after header):** "What Came Out of This" with two-column grid: "Why It Matters" + "Actionables" list with gold bullet dots. This goes at the top so readers get the takeaway first.
  - **Timeline:** Vertical gold line at ~28% width. Each section is a grid row.
  - **Left column (28%):** Round label, punchline quote callout (large gold open-quote mark, bold italic serif)
  - **Right column:** Section header (bold serif), dialogue bubbles, "Read original" toggle
  - **Dialogue bubbles:** User = white with light border, left-aligned. Other speakers = dark (#2C2C2C), right-aligned. One thought per bubble.
  - **Images in bubbles:** When a dialogue entry has an image, render it as `<img src="../artifacts/filename.png">` inside the bubble. Style with `max-width: 100%; border-radius: 8px; margin-top: 8px; cursor: pointer`. Add a lightbox overlay so clicking the image shows it fullscreen with an Escape-to-close handler. Use direct file paths (same approach as frontend-slides), not base64 embedding.
  - **Pivoting moments:** Gold-filled timeline dot + "Pivoting Moment" badge
  - **Progressive disclosure:** "Read original" expands to full clean transcript
  - **Footer:** "WaveMind · Captured [date] · Visualized [date]"
- **Self-contained:** All CSS and JS must be inline. No external dependencies (except images, which are referenced by relative path).
- **Responsive:** Hide quote callouts on mobile, switch to single-column layout.

**Reference:** See `data/visuals/glm-benchmark.html` for an approved example (GLM Aesthetic Benchmark).

## Data Directory

Runtime data lives in `data/`. New artifacts and visuals are gitignored, but seeded examples are checked in for reference.

```
data/
├── .gitignore       # Ignores runtime data, keeps seeded examples
├── index.json       # Artifact registry (created at runtime)
├── artifacts/       # Raw markdown files (glm-benchmark.md seeded)
└── visuals/         # Generated HTML files (glm-benchmark.html seeded)
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
