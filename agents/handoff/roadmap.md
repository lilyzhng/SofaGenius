# Team Roadmap

Central task list for all agents. CEO maintains. Agents add tasks by communicating with CEO or editing directly.

**Updated:** 2026-03-25 18:05 PT

---

## Unassigned
- [x] ~~GitHub Action for digest cron trigger~~ — Jackie drafting, CronCreate also set up
- [x] ~~Cron without sudo research~~ — deprioritized, CronCreate solves it

## Builder
- [x] Jackie deployed on Agent Computer (shared EFS)
- [x] nohup + script always-on — validated
- [x] Plugin fork synced (13 upstream commits)
- [x] PRs #37, #39, #44, #46, #47, #48 merged
- [x] LinkedIn POC validated (Claude Desktop Cowork)
- [x] /task-tracker skill — PR #53
- [x] Test `computer agent sessions` with --channels — doesn't support it, documented
- [x] Fix setup guide (.env sourcing) — fixed in PR #50
- [ ] `archive_thread` Discord plugin tool
- [ ] Auto-restart supervisor — nohup working, 16-hour test in progress
- [ ] **Agent Computer migration spec** — standardized launch script, plugin cache fix, .env management
- [ ] **Deploy CEO to Agent Computer** — Builder deploys, validate 24 hours
- [ ] **Deploy Researcher to Agent Computer** — after CEO validated
- [ ] **Deploy Builder (self) to Agent Computer** — goes last, after everyone else is stable

## Researcher
- [x] PRs #30, #31, #32, #33, #42 merged
- [x] /deep-research skill — PR #51
- [x] /debrief update — PR #52
- [x] Agent Computer deep research with hypothesis testing
- [x] Honcho memory evaluation — UNBLOCKED, SDK tested, cross-session works
- [ ] Claude Max ToS research — **doing next**
- [ ] Honcho architecture write-up — **in progress**
- [ ] 24-hour token monitoring on Jackie — needs OpenRouter API access from Builder
- [ ] Agent Computer community contribution — CEO's lane (content)

## Jackie
- [x] PR #41 merged (agent config)
- [x] PR #43 merged (adaptive tone)
- [x] IDENTITY.md + USER.md filled in
- [x] Digest feed early scan completed
- [x] All open PRs reviewed (#50-54)
- [ ] Morning digest at 7 AM PT (Mar 25) — **prepped, cron set**
- [ ] 16-hour persistence check at 7 AM — staying online
- [ ] GitHub Action for digest cron backup — **drafting**

## CEO
- [x] Tribe Digest cron (remote agent, 7 AM PT)
- [x] /hands-off + /debrief skills
- [x] PR workflow checklists + PR template
- [x] Skill symlink migration
- [x] /ceo-checkin skill — PR #54 merged
- [x] Team roadmap created
- [x] /debrief skill update — done by Researcher (PR #52)
- [ ] Agent Computer deployment tweet (visual + screenshots)
- [ ] "What happens when AI agents never sleep?" content piece

---

## Lily Actions Needed
- [x] ~~Sign up at app.honcho.dev~~ — done, Researcher unblocked
- [ ] Approve open PRs: #50, #51, #52, #53
- [ ] Review Yuya's memory_bench.md
