---
from: Launcher
to: Builder
date: 2026-03-21
priority: high
---

# AutoResearch for SuperGeneral — Environment & Framework Research

## Context

Lily watched the Karpathy x No Priors podcast. Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) repo has a `program.md` that defines an autonomous research loop: agent modifies code → runs experiment → keeps/discards based on objective metric → LOOP FOREVER. Lily wants to apply this pattern to her SuperGeneral project (compositional tool environments for long-horizon agents).

## What Lily Wants

An autonomous research loop where an agent experiments with tool composition strategies in a sandboxed environment, with verifiable objective metrics (task completion, composition correctness).

## Tasks

### 1. Check Lily's local setup first
- Read Lily's journal entries (`~/Documents/lilyzhng/2026/`) for hackathon notes
- She did Harbor + SkyRL fine-tuning that "almost worked"
- Understand what's already set up locally before looking externally

### 2. Review Lily's repos
- **autoresearch fork:** https://github.com/lilyzhng/autoresearch — check if forked, if not fork it
- **SuperGeneral / OpenEnv hackathon:** https://github.com/lilyzhng/OpenEnv/tree/main/hackathon — understand current environment design, task family (diamond/hourglass/seesaw/temple), reward structure

### 3. Research RL environments (NOT sandboxes — RL training environments)
Compare these for running the auto research loop:
- **Harbor** — Lily's preferred direction, used with SkyRL before
- **OpenEnv** — current setup but Lily wants to potentially switch
- **Prime Intellect RL environment**
- **Nous Research Hermes Agent** — recently integrated Honcho memory

### 4. Research sandboxes for running experiments
Where to actually execute the agent's experiments:
- **Modal** — Lily already uses Modal for training. Do they have good sandbox support?
- **Daytona**
- **E2B**
- Other options

### 5. Deliverable
Write a summary comparing:
- RL environments: Harbor vs OpenEnv vs others (features, ease of setup, reward design flexibility)
- Sandboxes: Modal vs Daytona vs E2B (cost, API, isolation)
- Recommendation for which combo to use
- What's already working locally vs what needs to be built

## Key Principle from Karpathy

The auto research loop needs:
1. A single objective metric (like val_bpb) that can be automatically evaluated
2. Code that can be modified by the agent (like train.py)
3. Fixed evaluation harness that agent cannot touch
4. LOOP FOREVER — no human in the loop

For SuperGeneral, the metric would be task completion rate / composition correctness in the tool environment.

## References
- Karpathy autoresearch program.md: https://github.com/karpathy/autoresearch/blob/master/program.md
- Podcast notes: `Build_My_Tribe/Following_Builders/Podcasts/karpathy_no_priors_loopy_era.md`
- SuperGeneral site: https://supergeneral.vercel.app/
