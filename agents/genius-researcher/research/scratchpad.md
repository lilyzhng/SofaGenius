# Researcher Scratchpad — Active Tasks

## Next Session: Agent Computer Deep Dive (revision of PR #42)

### Research Plan

**Hypotheses to validate:**
1. Agent Computer VMs stay up 24/7 without intervention
2. Claude Code context compression works in Discord bot mode
3. Plugin files persist across VM restarts and platform updates
4. Process auto-restarts after a crash
5. 25 VMs on $20 plan all run simultaneously without degradation

**Sources (check in order):**
- [ ] Agent Computer GitHub repo (if public) — read the code
- [ ] Agent Computer Discord/community — real user experiences
- [ ] Agent Computer API docs — test endpoints, not just read
- [ ] GitHub issues/discussions — production gotchas
- [ ] Jackie's running VM — SSH in, test failure modes
- [ ] OpenRouter dashboard — monitor Jackie's token usage over 24 hours
- [ ] Companion.ai — shared infra details?
- [ ] Builder's PR #39 — extract every gotcha

**Rules:**
- Each hypothesis → tested with real data, not assumed
- Each finding → includes source and verification method
- Unverifiable → labeled "UNVERIFIED" with blocker
- Don't write the doc until research is done

## Completed This Session (2026-03-24)

### Honcho memory evaluation
- **Status:** DONE
- **Output:** `agents/handoff/reports/research_honcho_memory_20260324.md`
- **Finding:** Start with Hermes default memory, add Honcho later

### json-render hands-on
- **Status:** DONE (demo built, terminal output captured)
- **Finding:** json-render/ink works, 27 terminal components, Claude default model

### Agent Computer design doc (PR #42)
- **Status:** IN REVIEW — needs deeper revision per Lily's feedback
- **Feedback:** Too superficial. Need hands-on testing, real user data, code reading. Follow Builder's Hermes doc standard.
