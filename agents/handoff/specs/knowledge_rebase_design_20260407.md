# Knowledge Rebase - Design Spec

> Date: 2026-04-07
> Owner: Jackie (design + build) | Lucy (scheduled triggers) | All agents (participants)
> Status: Draft v1
> Context: Adapting Karpathy's LLM Wiki patterns for lily-memory multi-agent setup. Replaces passive war room health check with active knowledge maintenance.

---

## First Principles Check

1. **Who is this for?** All 4 agents + Lily. Agents are the primary operators. Lily benefits from a cleaner, more reliable memory vault.
2. **What problem are we actually solving?** lily-memory accumulates stale entries, contradictions, and orphan files over time. No one actively maintains it. The war room health check is passive (read-only status reporting), not corrective.
3. **Does the delivery model meet them where they already are?** Yes. A Claude Code skill triggered by Lucy's scheduled actions, executed by Jackie in the terminal. No new tools or UIs.
4. **What's the simplest version that tests whether this works?** A lint operation that scans MEMORY.md indexes for broken links, stale dates, and orphan files. Report only. No automated fixes in v1.
5. **Why this approach over alternatives?** RAG would require infrastructure (vector DB, embeddings, retrieval pipeline). A wiki-style system uses the file system agents already work in. Karpathy's pattern is proven for single-user LLM knowledge management. We adapt it for multi-agent writes.

---

## Problem Statement

lily-memory is the team's shared brain. Four agents and Lily write to it daily: call summaries, feedback entries, project context, career notes. But nobody maintains it.

**What breaks over time:**

- **Stale entries.** Feedback from March still references "CEO" role after the reorg renamed it to "Growth." Project files reference completed or abandoned work with no status update.
- **Contradictions.** Two files say different things about the same topic. One feedback file says "always use /raise-pr" while another describes manual PR creation.
- **Orphan files.** Files exist in directories but are not referenced from any MEMORY.md index. They are invisible to agents who rely on the index for navigation.
- **Missing cross-references.** Jackie's call notes mention a decision that should update a project file, but no link exists between them.
- **No audit trail.** When a memory entry changes, there is no record of what changed or why. Git history exists but is too noisy to scan.

**The current war room health check** (twice-daily heartbeat) reports agent status. It does not inspect or repair the knowledge base. It answers "are agents alive?" not "is our shared memory accurate?"

---

## Karpathy's LLM Wiki Pattern (Reference)

Karpathy's approach replaces RAG with an incrementally maintained wiki. Three layers:

| Layer | Purpose | Mutability |
|-------|---------|------------|
| **Raw sources** | Original transcripts, articles, notes | Immutable. Never edited after ingest. |
| **Wiki pages** | LLM-maintained summaries, organized by topic | Mutable. Updated by ingest + lint operations. |
| **Schema** | Index file (table of contents) + operational rules | Mutable. The "CLAUDE.md" of the wiki. |

**Core operations:**

- **Ingest:** Process a new source. Write a summary wiki page. Update the index. Add cross-links to related pages. Append to the chronological log.
- **Query:** Read the index first. Drill into relevant pages. If the answer produces new knowledge, file it back as a wiki page.
- **Lint:** Find contradictions between pages. Flag stale claims. Identify orphan pages (not in index). Detect missing cross-references. Surface data gaps.

**Key structural files:**

- `index.md` - Content catalog. The single entry point for navigating the wiki.
- `log.md` - Chronological audit trail. Every change gets a timestamped entry.

---

## Our Adapted Design

### What We Keep from Karpathy

- **Three-layer model.** Raw sources (conversations/, transcripts) are immutable. Wiki pages (feedback_*, project_*, user_*) are agent-maintained summaries. Schema (MEMORY.md) is the navigational index.
- **index.md pattern.** We already have MEMORY.md serving this role. Formalize it.
- **Lint operation.** Directly applicable. Scan for broken links, stale content, orphans, contradictions.
- **log.md audit trail.** New addition. Every rebase operation appends a timestamped entry.

### What We Change

| Karpathy's Design | Our Adaptation | Why |
|---|---|---|
| Single writer (one LLM) | Multi-agent writes (4 agents + Lily) | Need domain partitioning to avoid conflicts |
| Ingest updates 15+ files at once | Batch changes via PR with 3 approvals | PR friction means we batch intelligently, not file-by-file |
| Wiki pages are flat namespace | Nested structure: Agents/{name}/, shared/, Goal_1/, Goal_2/ | Already established. Don't fight existing structure. |
| Query writes back to wiki | Agents already do this (save feedback, project notes) | No change needed. Just formalize the pattern. |

### What We Skip (for now)

- **Automated ingest pipeline.** Karpathy's ingest processes raw sources automatically. Our agents already write summaries manually after calls. Automating this is v2.
- **Semantic dedup.** Detecting near-duplicate entries across agent memories requires embedding comparison. Out of scope for v1.

---

## Proposed Operations

### 1. Lint (Health Check)

**What it does:** Scans the memory vault and produces a health report. Read-only. No mutations.

**Checks:**

| Check | What it catches |
|-------|----------------|
| **Broken index links** | MEMORY.md references a file that does not exist |
| **Orphan files** | File exists in directory but is not in any MEMORY.md |
| **Stale dates** | Entry has `date:` or `updated:` older than 14 days with no recent git commits |
| **Cross-reference gaps** | File mentions a topic (e.g., "WaveMind") but has no link to the canonical WaveMind page |
| **Contradictions** | Two files make conflicting claims about the same topic (LLM-assisted detection) |
| **Empty/stub files** | Files with fewer than 3 lines of content |

**Output:** Markdown report posted to the rebase PR or Discord thread. Grouped by severity (broken > stale > orphan > suggestion).

**Scope:** All of lily-memory. Both shared/ and per-agent directories.

### 2. Compile (Index Rebuild)

**What it does:** Regenerates MEMORY.md index files from the actual file system. Ensures every file is cataloged and every catalog entry points to a real file.

**Rules:**
- Preserves existing descriptions (one-line summaries after the link)
- Adds new entries for uncataloged files with auto-generated descriptions
- Removes entries for deleted files
- Sorts entries by category (User, Feedback, Project, Reference, Research)

**Scope:** One MEMORY.md at a time. The operator specifies which index to compile.

### 3. Rebase (Active Maintenance)

**What it does:** The full maintenance pass. Runs lint, then applies fixes.

**Fix types:**
- Update stale dates and status fields
- Add missing cross-references (as Obsidian [[wiki links]])
- Archive completed/abandoned project entries
- Merge duplicate feedback entries
- Update role/name references after reorgs

**Output:** A single PR with all changes, plus a log.md entry summarizing what was rebased and why.

---

## File Structure Changes

### New file: `log.md` (per memory scope)

Added to each memory scope that gets rebased. Chronological audit trail.

```
lily-memory/
  Agents/
    shared/
      MEMORY.md          # (existing) shared index
      log.md             # (new) shared audit trail
    jackie_product/
      MEMORY.md          # (existing) Jackie's index
      log.md             # (new) Jackie's audit trail
    bill_builder/
      ...
    lucy_growth/
      ...
    andrej_research/
      ...
  log.md                 # (new) root-level audit trail for cross-scope rebases
```

### log.md format

```markdown
# Knowledge Rebase Log

## 2026-04-07 - Jackie
- Removed 3 orphan files from shared/ (feedback_no_home_dotfiles.md had no index entry)
- Updated 5 stale project entries (project_wavemind.md status: Draft -> Shipped)
- Added cross-links between feedback_always_use_raise_pr.md and feedback_always_use_raise_pr_v2.md
- Archived project_action_items_20260327.md (superseded by warroom.md)
```

### Formalize MEMORY.md conventions

MEMORY.md files already exist but have inconsistent formats. Formalize:

- **Frontmatter required:** `date:` and `updated:` fields
- **Categories:** Group entries under ## headings (User, Feedback, Project, Reference, Research)
- **Entry format:** `- [filename.md](filename.md)` followed by a one-line description
- **Wiki links:** Use `[[filename]]` for cross-references within descriptions

---

## Multi-Agent Coordination

### Domain Ownership

Each agent owns their private memory directory. Only the owner writes to it.

| Scope | Owner | Other agents |
|-------|-------|-------------|
| `Agents/jackie_product/` | Jackie | Read-only |
| `Agents/bill_builder/` | Bill | Read-only |
| `Agents/lucy_growth/` | Lucy | Read-only |
| `Agents/andrej_research/` | Andrej | Read-only |
| `Agents/shared/` | Jackie (rebase lead) | All agents write feedback/project entries |
| Root dirs (Goal_1/, Goal_2/, etc.) | Jackie (rebase lead) | Lily writes directly |

### Conflict Avoidance

- **Rebase is single-threaded.** Only one agent runs a rebase at a time. Jackie owns the rebase operation.
- **Lint is read-only.** Any agent can run lint at any time without coordination.
- **Shared/ writes use file-level locking.** Agents create new files (never edit each other's files). Jackie consolidates during rebase.
- **PR batching.** A rebase PR touches many files. To avoid blocking other lily-memory PRs, rebase PRs are labeled `knowledge-rebase` and reviewed with the understanding that they are maintenance, not new content.

### Who Does What

| Role | Agent | Responsibility |
|------|-------|---------------|
| **Rebase lead** | Jackie | Runs rebase operations, owns the PR, resolves conflicts |
| **Trigger** | Lucy | Scheduled GitHub Action fires weekly, tags Jackie in #feature-release |
| **Reviewers** | All agents | Review the rebase PR (required 3 approvals) |
| **Escalation** | Lily | Resolves ambiguous cases (e.g., "is this project still active?") |

---

## Workflow

### Weekly Rebase Cycle

```
Monday 9 AM PT: Lucy's scheduled action triggers
  -> Tags Jackie in #feature-release: "Weekly knowledge rebase due"
  -> Jackie picks it up

Jackie runs the rebase:
  1. Run lint on all memory scopes
  2. Review lint report, decide which fixes to apply
  3. Run compile on each MEMORY.md
  4. Apply rebase fixes (stale updates, cross-links, archives)
  5. Append to log.md
  6. Create PR: "knowledge-rebase/2026-04-07"
  7. Announce in #feature-release, tag all agents for review

Team reviews:
  - Agents review within 24 hours
  - Focus: "Did Jackie break any of my entries? Are the archives correct?"
  - Not a deep content review. Trust the rebase lead.

Lily merges after 3 approvals.
```

### Ad-Hoc Lint

Any agent can run lint at any time for a quick health check. No PR needed for read-only reports. Useful before writing new entries ("does this topic already have a page?").

---

## Implementation Plan

### Phase 1: Lint (Week 1)

Build the lint operation as a Claude Code skill.

- Scan MEMORY.md for broken links
- Detect orphan files not in any index
- Check frontmatter dates for staleness
- Output: markdown report to stdout

**Deliverable:** `/knowledge-rebase lint` skill that produces a health report.

### Phase 2: Compile (Week 2)

Build the compile operation.

- Read directory contents, diff against MEMORY.md entries
- Auto-generate descriptions for new files (LLM-assisted)
- Remove dead entries
- Preserve existing descriptions

**Deliverable:** `/knowledge-rebase compile <scope>` that regenerates a MEMORY.md.

### Phase 3: Rebase + Log (Week 3)

Build the full rebase workflow.

- Orchestrate lint + compile + fix application
- Create log.md entries
- Auto-create branch and PR
- Tag reviewers

**Deliverable:** `/knowledge-rebase run` that produces a complete rebase PR.

### Phase 4: Scheduling (Week 4)

Wire up Lucy's scheduled trigger.

- GitHub Action or cron that fires Monday 9 AM PT
- Posts to #feature-release tagging Jackie
- Jackie's heartbeat handler picks it up and runs the rebase

**Deliverable:** Automated weekly trigger. The full loop running hands-free.

---

## Open Questions

1. **Contradiction detection accuracy.** LLM-based contradiction checking across dozens of files may produce false positives. Should we start with a simpler heuristic (e.g., same topic name, different claims) before going full semantic?
2. **Rebase PR size.** A weekly rebase touching 20+ files might be hard to review. Should we cap the number of changes per PR and split into multiple if needed?
3. **Root directory ownership.** Lily writes directly to Goal_1/, Goal_2/, etc. Should rebase touch these at all, or only the Agents/ subtree?
4. **Conversation auto-save exception.** Conversations can be pushed directly to main. Should rebase skip the conversations/ directories entirely, or include them in lint (checking for missing index entries)?
