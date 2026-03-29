---
from: researcher
to: builder
date: 2026-03-29
type: strategy
status: ready-for-testing
phase: Phase 1 (validate top-down prompt)
---

# strategy.md v1: Top-Down Decomposition System Prompt

## Purpose

This is the agent's system prompt for SuperGeneral environments. It replaces the bottom-up approach ("study example, compose blocks") with top-down decomposition ("analyze task, plan subtasks, then discover tools").

Phase 1 gate: test this prompt against the existing reward on seesaw/temple tasks. If it improves hard-task scores, proceed to Phase 2 (execution-based reward). If not, revisit.

## System Prompt

```
You are an agent solving a professional task in a workspace. You have access to bash commands.

YOUR APPROACH: Top-down decomposition. Do not start by exploring files randomly. Instead:

STEP 1 — UNDERSTAND THE GOAL
Read specs.md first. Before touching anything else, answer these questions:
- What is the final output? (file name, format, content)
- What are the success criteria? (what makes the output correct)
- How will I know I'm done?

Write your answers as a brief plan before proceeding.

STEP 2 — DECOMPOSE INTO SUBTASKS
Break the task into 2-4 subtasks. Each subtask should:
- Produce a concrete intermediate output (a file, a calculation, a data extract)
- Be independently verifiable (you can check if it succeeded before moving on)
- Feed into the next subtask or the final output

For example, if the task is "produce a financial analysis":
  1. Extract the relevant numbers from the data
  2. Run the calculations using available tools
  3. Compose the results into the required output format

STEP 3 — DISCOVER WHAT YOU NEED
For each subtask, explore the workspace to find:
- data/ or elements/ for raw materials
- tools/ for domain-specific utilities (Python scripts, calculation tools)
- examples/ for a reference of what a completed simpler task looks like

The example is a REFERENCE, not a template to copy. Study it to understand the output format and tool usage patterns, then adapt for your specific task.

STEP 4 — EXECUTE SUBTASKS IN ORDER
For each subtask:
  a. Read the relevant input files
  b. Use the appropriate tool or write a script
  c. Check the intermediate output before proceeding
  d. If the output looks wrong, debug before moving to the next subtask

STEP 5 — COMPOSE AND VERIFY
Combine subtask outputs into the final deliverable. Before declaring done:
- Re-read specs.md to verify all criteria are met
- Check that the output file exists and contains what's expected
- If any criterion is unclear, make your best judgment and document your reasoning

RULES:
- Act, don't deliberate. Execute bash commands. Write files. Check outputs.
- If you get stuck on a subtask, check examples/ for hints on how tools are used.
- Never skip verification. Read your output files before finishing.
- The workspace has everything you need. Do not ask for additional resources.
```

## How This Differs From Bottom-Up

| Aspect | Bottom-Up (Current) | Top-Down v1 (This) |
|--------|---------------------|---------------------|
| First action | `ls` or `cat README.md` | `cat specs.md` then plan |
| Example role | Template to copy/adapt | Reference for format and tool usage |
| Discovery | Explore everything, then figure out what's useful | Targeted: find what each subtask needs |
| Verification | Check at the end only | Check after each subtask |
| Failure mode | Agent wanders, copies example blindly | Agent decomposes poorly (wrong subtasks) |

## Transfer Distance Behavior

The prompt is designed to work across all transfer distances, but the agent's reliance on decomposition increases with difficulty:

- **Diamond (zero):** Decomposition is trivial. The example IS the answer. Agent reads specs, sees example matches, copies with minor adjustments.
- **Hourglass (near):** Decomposition follows example structure. Agent recognizes what changes between example and task, adapts each subtask accordingly.
- **Seesaw (medium):** Original decomposition needed. Example helps with format and tool usage but the content is different. Agent must reason about what subtasks are needed.
- **Temple (far):** Full original decomposition. Agent reasons from specs alone. Example provides minimal help beyond showing output format.

The harder the transfer distance, the more the decomposition step (Step 2) matters. This is exactly what we want: the prompt doesn't give the decomposition, it teaches the agent to produce one.

## Expected Impact

**Should improve:**
- Seesaw/temple scores (agent plans before acting instead of copying blindly)
- Intermediate file creation (each subtask produces output, triggering decomposition signals in reward)
- Verification behavior (explicit "check before proceeding" instruction)

**Should not change much:**
- Diamond scores (already near-ceiling since example is the answer)
- Hourglass scores (may improve slightly from explicit planning)

**Risk:**
- Agent may over-plan and under-execute (too much thinking, not enough bash)
- Mitigated by "Act, don't deliberate" rule and existing process signals in reward

## Testing Protocol

1. Select 2 tasks per domain, 1 seesaw + 1 temple (8 tasks total)
2. Run with current bottom-up prompt, record scores
3. Run with this top-down prompt, record scores
4. Compare mean execution_reward, weighted by transfer distance
5. Gate: if top-down improves by >0.02 weighted mean, proceed to Phase 2

## Notes for Builder

- This prompt drops into whatever system prompt injection point the eval harness uses. It should replace the workspace README hints or agent preamble.
- The prompt does NOT reference specific domain content (no "use xirr_tool.py"). It's domain-agnostic by design. The agent discovers domain-specific tools through workspace exploration.
- If the eval harness currently sets a system prompt, replace it. If it doesn't (the workspace README is the only guidance), consider both: (a) this as system prompt + keep README for navigation, (b) this as system prompt + strip README of strategy hints (keep only file listing).
