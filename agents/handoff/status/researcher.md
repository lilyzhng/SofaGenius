---
agent: researcher
updated: 2026-03-28 11:50 PM PT
status: active
---

## Current Focus
Waiting on Lily's feedback on SuperGeneral redesign doc. Supporting skill brainstorming for ZAI ambassador program.

## Last Completed (This Session)
- **PR #94 merged** — researcher persona (IDENTITY.md + SOUL.md) embodying Karpathy from all 3 podcasts
- **Builder's RLM reward doc reviewed** — honest assessment: RLM overkill for v1, reward gaming is real risk. Team aligned on execution-based reward first.
- **SuperGeneral redesign doc drafted** (`specs/design_supergeneral_topdown_20260328.md`) — top-down decomposition + execution-based reward + autoresearch loop. 5 open questions for Lily.
- **Deep study of OpenEnv + SkillClaw codebases** via GitHub — confirmed diamond/hourglass/seesaw/temple are transfer distance patterns, not domains. Found GRPO scripts don't run environment (offline text scoring only).
- **ZAI + Anthropic ambassador context** — read full proposal + 11-round thinking artifact from lily-memory vault. Saved to private memory.
- **Zara Zhang + Claude Code skill research** — analyzed her content direction, identified viral skill patterns, recommended GLM 5.1 skill ideas. Integrated with Jackie's research.
- **Research → Product 1-pager** delivered earlier in session

## Next Up
- Lily's feedback on SuperGeneral design doc open questions
- Support Jackie on skill planning (provide data/analysis as needed)
- Raise PR for research reports (currently uncommitted: APEX strategy, dataset catalog, training environments, design doc, 1-pager, Karpathy study)

## Blockers
- None — vault access fixed, all GitHub repos accessible

## Findings Worth Acting On
- **GRPO scripts don't run the environment** — reward is offline text pattern matching, not execution-based. Both execution-based reward AND RLM reward need to be built from scratch.
- **Transfer distance confirmed** — diamond (zero) → temple (far) measures reasoning gap from reference example. Top-down decomposition makes harder transfer distances (seesaw, temple) the most valuable training signal.
- **SkillClaw evidence** — bottom-up flywheel worked for easy tasks, failed for hard ones. Shared brain README became a top-down decomposition guide because pure composition failed.
- **Viral skill formula** — "ugly input → beautiful output" + non-technical accessible + 60-second demo. Visual skills go most viral.
