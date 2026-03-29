# WaveMind — Design Doc

> Date: 2026-03-29
> Owner: Jackie (design + build) | CEO (review + mentor)
> Status: Draft — pending Lily's review
> Context: Evolved through 7-round brainstorm with Lily (2026-03-28), new requirements from Lily + CEO (2026-03-29)

---

## First Principles Check

1. **Who is this for?** Lily. One user. An AI-native person who thinks in voice, lives in the terminal, and already has Claude Code + agents running daily.
2. **What problem are we actually solving?** Lily has too many ideas and no single place to capture them, track daily tasks, and review how her thinking evolves. She uses Discord, voice chat, scattered notes — nothing persists or connects.
3. **Does the delivery model meet her where she already is?** Yes — a Claude Code skill. She's already in the terminal all day. No new app to open, no context switch.
4. **What's the simplest version that tests whether this works?** A skill that reads existing thinking artifacts and generates a visual thought map. Plus a Supabase-backed task list she can update from the terminal.
5. **Why this approach over alternatives?** A web app requires building auth, UI, hosting — all unnecessary for a single user who lives in the terminal. A skill is zero-friction. Supabase gives persistence without building a backend.

---

## Problem

Lily's daily workflow generates massive amounts of thinking — voice chats with Claude, brainstorms with agents, meeting preps, debriefs. But:

- **Ideas vanish.** Voice chats end and the thinking process disappears. No automatic capture.
- **Tasks scatter.** To-dos live in Discord messages, mental notes, scattered files. No single source of truth.
- **No review loop.** She can't look back at how her thinking evolved over a week or month.

She needs one tool that does three things: **capture thoughts, track tasks, and show the bigger picture.**

---

## What WaveMind Does

A Claude Code skill with two layers, backed by Supabase.

### Layer 1: Thought Capture (the original vision)

Takes a thinking artifact (conversation transcript, voice chat output, brainstorm notes) and transforms it into a structured, visual output.

**Input:** Any thinking artifact — markdown transcript, conversation log, voice-to-text dump
**Processing:** Analyze thought evolution, identify turning points, extract key insights, map connections
**Output:** Beautiful HTML visual — thought evolution timeline, insight cards, mind map of connections

```
/wavemind capture                    # Capture current conversation as thinking artifact
/wavemind visualize <artifact>       # Generate visual from a thinking artifact
/wavemind review                     # Browse past thinking artifacts + visuals
```

### Layer 2: Task Management / Secretary

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

**Task features:**
- Clickable checklist with history (what was done when)
- Carry-over: undone tasks auto-move to next day
- Tags: group tasks by project/goal
- History: "what did I do on Tuesday?"

---

## Architecture

```
┌─────────────────────────────────────┐
│         /wavemind skill             │
│  (Claude Code skill — markdown +    │
│   shell scripts)                    │
├─────────────────────────────────────┤
│                                     │
│  capture.sh    — save artifacts     │
│  visualize.sh  — generate HTML      │
│  tasks.sh      — CRUD tasks/habits  │
│  sync.sh       — Supabase I/O       │
│                                     │
├─────────────────────────────────────┤
│         Supabase (backend)          │
│                                     │
│  thinking_artifacts  — raw text     │
│  visualizations      — HTML output  │
│  tasks               — daily tasks  │
│  habits              — recurring    │
│  habit_logs          — completions  │
│                                     │
└─────────────────────────────────────┘
```

### Why Supabase?

- Lily already knows it (mentioned MicDrop uses it)
- Persistence across sessions — agent restarts don't lose data
- REST API = agents can access it directly (no ORM, no server)
- Free tier is more than enough for single-user
- Future web UI can read the same data

### Supabase Schema (v1)

```sql
-- Thinking artifacts
create table thinking_artifacts (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  raw_content text not null,
  source text,                    -- 'voice_chat', 'brainstorm', 'manual'
  tags text[],
  created_at timestamptz default now()
);

-- Generated visualizations
create table visualizations (
  id uuid primary key default gen_random_uuid(),
  artifact_id uuid references thinking_artifacts(id),
  html_content text not null,
  summary text,
  key_insights jsonb,             -- [{title, description, round}]
  turning_points jsonb,           -- [{round, from, to, trigger}]
  created_at timestamptz default now()
);

-- Daily tasks
create table tasks (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  status text default 'pending',  -- 'pending', 'done', 'carried'
  tags text[],
  due_date date,
  completed_at timestamptz,
  carried_from date,              -- if carried over from a previous day
  created_at timestamptz default now()
);

-- Recurring habits
create table habits (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  frequency text default 'daily', -- 'daily', 'weekly'
  target int default 1,           -- e.g., 3 for "interact with 3 tweets"
  active boolean default true,
  created_at timestamptz default now()
);

-- Habit completion log
create table habit_logs (
  id uuid primary key default gen_random_uuid(),
  habit_id uuid references habits(id),
  date date not null,
  count int default 0,
  notes text,
  created_at timestamptz default now(),
  unique(habit_id, date)
);
```

---

## Composability Strategy

**Don't build from scratch.** Use existing tools as building blocks.

| Component | Build vs Compose | What to use |
|-----------|-----------------|-------------|
| Voice → text | Compose | Claude's built-in voice chat (already exists) |
| Text analysis | Compose | Claude's native reasoning (just prompt it) |
| HTML generation | Compose | Anthropic's `frontend-design` skill aesthetic patterns |
| Data persistence | Compose | Supabase REST API (curl) |
| Task management | Build | Simple CRUD — too specific to compose |
| Habit tracking | Build | Simple CRUD — too specific to compose |

WaveMind's real value is **orchestration** — wiring together existing capabilities into a flow that feels like one product.

---

## v1 Scope (Weekend Build)

### What we build:

1. **Supabase setup** — create tables, configure API access
2. **`/wavemind today`** — show today's tasks + habit status (fetch from Supabase)
3. **`/wavemind add/done`** — create and complete tasks
4. **`/wavemind habit`** — log habit completions, show streaks
5. **`/wavemind capture`** — save a thinking artifact to Supabase
6. **`/wavemind visualize`** — generate HTML visual from an artifact

### What we defer:

- Auto-capture from voice chat (needs Claude Code integration research)
- Weekly review aggregation
- Carry-over automation (manual for v1)
- Encryption / multi-user
- Web UI

### Test data:

Lily has 8 thinking artifacts in lily-memory ready for testing:
1. **20260327 — ZAI Ambassador Prep (11 rounds)** — best test case, clear narrative arc
2. **20260318 — GTC Event Reflection** — emotional journey, personal reflection
3. **20260320 — MyTake v2 Narrative Arc Discovery** — aha moment, layered thinking
4. Others: APEX Hackathon, Flywheel Demo, Ablation experiments

### Skill structure:

```
agents/skills/wavemind/
├── wavemind.md              # Skill entry point (prompt + instructions)
├── lib/
│   ├── supabase.sh          # Supabase REST helpers (auth, CRUD)
│   ├── tasks.sh             # Task management logic
│   ├── habits.sh            # Habit tracking logic
│   ├── capture.sh           # Artifact capture + storage
│   └── visualize.sh         # HTML generation from artifacts
└── templates/
    └── thought-map.html     # Visual template for thought evolution
```

---

## User Flows

### Morning: "/wavemind today"
```
📋 Saturday, March 29

Tasks:
  1. [ ] Write ZAI ambassador proposal
  2. [ ] Review WaveMind design doc
  3. [x] Fix watchdog interval (PR #98)

Habits:
  🐦 Tweet: 0/1
  💬 Interact: 0/3

Carried from yesterday:
  4. [ ] Finish Sesame spec review
```

### After a voice chat: "/wavemind capture"
```
Captured thinking artifact: "WaveMind brainstorm with CEO"
→ 12 rounds, ~4500 words
→ Stored to Supabase (id: abc-123)
→ Run /wavemind visualize abc-123 to generate visual
```

### Review thinking: "/wavemind visualize abc-123"
```
Generated thought evolution map → saved to ~/wavemind-output/abc-123.html
Open in browser to view.

Key insights found:
  1. "CLI is wrong distribution model for agents" (round 3)
  2. "Skill = portable across Claude Code forks" (round 5)
  3. "Vault framing > one-time setup" (round 7)

Turning points:
  Round 3: CLI → Skill pivot (triggered by: "who is the actual user?")
  Round 7: Setup tool → Key management platform (triggered by: "what about project #2, #3?")
```

---

## Success Metrics (v1)

- [ ] Lily can run `/wavemind today` and see her tasks + habits
- [ ] Lily can add/complete tasks from the terminal
- [ ] Lily can log habit completions and see streaks
- [ ] Lily can capture a thinking artifact and store it to Supabase
- [ ] Lily can generate a visual from the ZAI 11-round artifact and find it useful
- [ ] Data persists across agent restarts (Supabase)
- [ ] Lily actually wants to use it daily (the real test)

---

## v2+ Roadmap

1. **Auto-capture:** Hook into Claude voice chat end-of-conversation to automatically save thinking artifacts
2. **Carry-over automation:** Cron job moves undone tasks to next day at midnight
3. **Weekly review:** `/wavemind week` — aggregated view of what got done, thinking themes, habit streaks
4. **Fragmented capture:** Short voice notes throughout the day → merged into daily thought map
5. **Publish mode:** Pick an insight from thought cards → generate tweet / LinkedIn post
6. **Web UI:** Read-only dashboard showing tasks, habits, thought maps (Supabase → simple frontend)
7. **Cross-artifact connections:** "This idea from March 15 connects to what you said on March 28"

---

## References

- [Our brainstorm (2026-03-28)](jackie-memory/conversations/20260328_wavemind_brainstorm.md) — full 7-round thinking evolution
- [v2 plan](jackie-memory/memory/mid-term/weekend_skill_plan_v2.md) — previous iteration
- [Karpathy's MenuGen post](https://karpathy.bearblog.dev/vibe-coding-menugen/) — the setup pain is real
- [Zara's mysay](https://mysay.ai) — adjacent product, voice → social content
- Composability lesson from 小红书 post — build on existing MCPs/skills
