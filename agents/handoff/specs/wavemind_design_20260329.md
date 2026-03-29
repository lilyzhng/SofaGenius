# WaveMind — Design Doc

> Date: 2026-03-29
> Owner: Jackie (design + build) | Builder (mentor) | CEO (review)
> Status: Draft v2 — incorporating review feedback
> Context: Evolved through 7-round brainstorm with Lily (2026-03-28), new requirements from Lily + CEO (2026-03-29), review feedback from Builder + Researcher

---

## First Principles Check

1. **Who is this for?** Lily. One user. An AI-native person who thinks in voice, lives in the terminal, and already has Claude Code + agents running daily.
2. **What problem are we actually solving?** Lily has too many ideas and no single place to capture them and review how her thinking evolves. Voice chats end and the thinking process disappears.
3. **Does the delivery model meet her where she already is?** Yes — a Claude Code skill. She's already in the terminal all day. No new app to open, no context switch.
4. **What's the simplest version that tests whether this works?** A skill that reads existing thinking artifacts from a file path and generates a visual thought map. Local file storage, no external dependencies.
5. **Why this approach over alternatives?** A web app requires building auth, UI, hosting — all unnecessary for a single user who lives in the terminal. A skill is zero-friction. Local JSON files are simpler than Supabase for single-user v1.

---

## Problem

Lily's daily workflow generates massive amounts of thinking — voice chats with Claude, brainstorms with agents, meeting preps, debriefs. But:

- **Ideas vanish.** Voice chats end and the thinking process disappears. No automatic capture.
- **No review loop.** She can't look back at how her thinking evolved over a week or month.
- **Tasks scatter.** To-dos live in Discord messages, mental notes, scattered files. (Addressed in v1.1)

---

## What WaveMind Does

A Claude Code skill for turning thinking artifacts into beautiful visual thought maps.

### v1: Thought Capture + Visualization (the unique value)

Takes a thinking artifact (conversation transcript, voice chat output, brainstorm notes) and transforms it into a structured, visual output.

**Input:** Any thinking artifact — markdown transcript, conversation log, voice-to-text dump
**Processing:** Claude-driven analysis of thought evolution, turning points, key insights, connections
**Output:** Beautiful HTML visual — thought evolution timeline, insight cards, mind map of connections

```
/wavemind capture <filepath>         # Save a thinking artifact from a file
/wavemind visualize <artifact-id>    # Generate visual from a stored artifact
/wavemind review                     # Browse past thinking artifacts + visuals
```

**Capture mechanism (v1):** Takes a file path to an existing markdown transcript or conversation log. Auto-capture from live Claude conversations is deferred to v2 (requires research into how Claude Code exposes conversation state).

### v1.1: Task Management / Secretary (after thought capture is validated)

A persistent daily command center. Not a project manager — a personal secretary that knows Lily's habits and priorities.

```
/wavemind today                      # Show today's tasks, habits, and agenda
/wavemind add "Write ZAI proposal"   # Add a task
/wavemind done 3                     # Mark task #3 complete
/wavemind habit                      # Show recurring habit status
/wavemind week                       # Weekly review — what got done, what carried over
```

**Daily habits (configured):**
- Post 1 tweet/day
- Interact with 3 tweets/day
- (Extensible — Lily adds more as needed)

---

## Architecture

```
agents/skills/wavemind/
├── wavemind.md              # Skill entry point (prompt + instructions)
├── lib/
│   ├── store.sh             # JSON CRUD (following Sesame vault pattern)
│   ├── capture.sh           # Artifact capture + storage
│   └── visualize.sh         # Orchestrate I/O for visualization
├── templates/
│   └── thought-map.html     # Visual template for thought evolution
└── data/                    # Runtime data (gitignored, repo-local)
    ├── .gitignore           # "*\n!.gitignore"
    ├── index.json           # Artifact registry
    ├── artifacts/           # Raw markdown files
    └── visuals/             # Generated HTML files
```

### Why Local File Storage (not Supabase)?

- **Zero setup friction.** No project creation, API keys, or table setup. Just works.
- **No permission issues.** Data lives inside `agents/skills/wavemind/data/` (repo-local, gitignored) — no home directory writes that trigger permission dialogs in headless mode.
- **Single user.** Lily is the only user. Local JSON files persist fine for one person.
- **Supabase = v2.** When we need multi-device sync or a web dashboard, we upgrade to Supabase. Not before.

### Data Structure

```
agents/skills/wavemind/data/
├── .gitignore              # "*\n!.gitignore" — keeps runtime data out of repo
├── index.json              # [{id, title, source, tags, created_at, file}]
├── artifacts/
│   ├── 20260327-zai-prep.md
│   └── 20260318-gtc-reflection.md
└── visuals/
    ├── 20260327-zai-prep.html
    └── 20260318-gtc-reflection.html
```

### Visualization Pipeline

The visualization is the hardest and most valuable part. It's Claude-driven, not shell-script NLP:

1. **Skill prompt** instructs Claude to analyze the artifact:
   - Identify conversation rounds / sections
   - Find key turning points (where thinking shifted)
   - Extract core insights and their connections
   - Map the narrative arc (how thinking evolved from start to end)

2. **Claude outputs structured JSON:**
   ```json
   {
     "title": "WaveMind Brainstorm",
     "rounds": 7,
     "narrative_arc": "Visual Dictionary → voice direction → thought capture → mysay discovery → interactivity → Claude voice chat pivot → test data",
     "turning_points": [
       {"round": 6, "from": "Build voice system", "to": "Use Claude's existing voice chat", "trigger": "Lily realized Claude already has voice"}
     ],
     "key_insights": [
       {"title": "Post-conversation skill", "description": "WaveMind adds an output layer to what Claude already does", "round": 6}
     ],
     "connections": [
       {"from": "mysay discovery", "to": "Claude voice pivot", "relationship": "mysay showed the interaction model, Claude showed we don't need to build it"}
     ]
   }
   ```

3. **HTML generation** — Claude generates a beautiful HTML page using `frontend-design` skill aesthetic patterns, rendering the JSON as an interactive thought evolution map.

Shell scripts (`capture.sh`, `visualize.sh`) handle file I/O only — reading artifacts, writing output, managing the index. Claude does all the thinking.

---

## Composability Strategy

**Don't build from scratch.** Use existing tools as building blocks.

| Component | Build vs Compose | What to use |
|-----------|-----------------|-------------|
| Voice → text | Compose | Claude's built-in voice chat (already exists) |
| Text analysis | Compose | Claude's native reasoning (just prompt it) |
| HTML generation | Compose | Anthropic's `frontend-design` skill aesthetic patterns |
| Data persistence | Build (simple) | Local JSON files in `data/` directory |

WaveMind's real value is **orchestration** — wiring together existing capabilities into a flow that feels like one product.

---

## v1 Scope (Weekend Build)

### What we build:

1. **Skill entry point** (`wavemind.md`) — commands + instructions
2. **Local data store** (`lib/store.sh`) — JSON CRUD, following Sesame vault pattern
3. **`/wavemind capture <filepath>`** — save a thinking artifact to local store
4. **`/wavemind visualize <id>`** — Claude-driven analysis → HTML visual output
5. **`/wavemind review`** — list and browse past artifacts
6. **`data/.gitignore`** — keep runtime data out of repo

### What we defer to v1.1:

- Task management (`/wavemind today`, `add`, `done`)
- Habit tracking (`/wavemind habit`)
- Weekly review

### What we defer to v2+:

- Auto-capture from voice chat (needs Claude Code integration research)
- Supabase backend (for web dashboard)
- Carry-over automation
- Encryption / multi-user
- Web UI

### Test data:

Lily has 8 thinking artifacts in lily-memory ready for testing:
1. **20260327 — ZAI Ambassador Prep (11 rounds)** — best test case, clear narrative arc
2. **20260318 — GTC Event Reflection** — emotional journey, personal reflection
3. **20260320 — MyTake v2 Narrative Arc Discovery** — aha moment, layered thinking
4. Others: APEX Hackathon, Flywheel Demo, Ablation experiments

---

## User Flows

### Capture a thinking artifact: "/wavemind capture"
```
/wavemind capture /home/node/lily-memory/2026/thinking/20260327_thinking_artifact.md

Captured thinking artifact: "ZAI Ambassador Prep"
→ 11 rounds, ~3200 words
→ Stored to data/artifacts/20260327-zai-prep.md (id: 20260327-zai-prep)
→ Run /wavemind visualize 20260327-zai-prep to generate visual
```

### Generate visual: "/wavemind visualize"
```
/wavemind visualize 20260327-zai-prep

Analyzing thinking artifact... (Claude-driven)

Generated thought evolution map:
→ Saved to data/visuals/20260327-zai-prep.html

Key insights found:
  1. "CLI is wrong distribution model for agents" (round 3)
  2. "Skill = portable across Claude Code forks" (round 5)
  3. "Vault framing > one-time setup" (round 7)

Turning points:
  Round 3: CLI → Skill pivot (triggered by: "who is the actual user?")
  Round 7: Setup tool → Key management platform (triggered by: "what about project #2, #3?")

Open data/visuals/20260327-zai-prep.html in browser to view.
```

### Browse artifacts: "/wavemind review"
```
Stored artifacts:
  1. 20260327-zai-prep — ZAI Ambassador Prep (11 rounds) [visualized]
  2. 20260318-gtc — GTC Event Reflection [not yet visualized]
  3. 20260320-mytake — MyTake v2 Narrative Arc [not yet visualized]
```

---

## Success Metrics (v1)

- [ ] Lily can capture a thinking artifact from a file path
- [ ] Lily can generate a visual from the ZAI 11-round artifact and find it useful
- [ ] The visual accurately identifies turning points and insight evolution
- [ ] Data persists in `agents/skills/wavemind/data/` across sessions
- [ ] Lily actually wants to visualize more artifacts after seeing the first one (the real test)

---

## v2+ Roadmap

1. **v1.1 — Task management:** `/wavemind today`, `add`, `done`, `habit` (daily tasks + recurring habits)
2. **Auto-capture:** Hook into Claude voice chat end-of-conversation to automatically save thinking artifacts
3. **Supabase backend:** Upgrade from local files when web dashboard or multi-device sync is needed
4. **Fragmented capture:** Short voice notes throughout the day → merged into daily thought map
5. **Publish mode:** Pick an insight from thought cards → generate tweet / LinkedIn post
6. **Web UI:** Read-only dashboard showing thought maps (Supabase → simple frontend)
7. **Cross-artifact connections:** "This idea from March 15 connects to what you said on March 28"

---

## References

- Our brainstorm (2026-03-28) — full 7-round thinking evolution (stored in `jackie-memory/conversations/20260328_wavemind_brainstorm.md`, Jackie-local)
- v2 plan — previous iteration (stored in `jackie-memory/memory/mid-term/weekend_skill_plan_v2.md`, Jackie-local)
- [Karpathy's MenuGen post](https://karpathy.bearblog.dev/vibe-coding-menugen/) — the setup pain is real
- [Zara's mysay](https://mysay.ai) — adjacent product, voice → social content
- Composability lesson from 小红书 post — build on existing MCPs/skills
