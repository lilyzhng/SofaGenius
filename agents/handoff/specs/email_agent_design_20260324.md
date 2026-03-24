# Email & LinkedIn Agent — Design Document

**Author:** genius-builder
**Date:** 2026-03-24
**Status:** Draft
**Reviewers:** lilyzhng, genius-ceo, genius-researcher, genius-jackie
**Feature owner:** genius-builder (setup) → genius-jackie (daily operations)

---

## Abstract

Use Claude computer use on Jackie's Agent Computer VM to automate LinkedIn replies and email triage. No scripts, no APIs, no Cloud Functions — just Claude controlling a browser on a VM that already has a desktop.

---

## 1. Problem Statement

### 1.1 Current State

Lily receives LinkedIn messages she can't auto-reply to (LinkedIn blocks email replies — `noreply@` address). She also spends time on routine email responses.

### 1.2 Why Now

Jackie runs on Agent Computer with a full desktop + VNC. Claude has computer use capability. The pieces are already in place.

### 1.3 Success Criteria

| Criteria | Measurement |
|----------|-------------|
| LinkedIn messages get redirect reply within a few hours | Verify by sending test message |
| No emails sent without Lily's approval (Phase 2) | Approval flow on Discord |
| Zero new infrastructure needed | No Cloud Functions, no OAuth, no scripts |

---

## 2. Design Principles

1. **Use what we already have.** Claude subscription + Agent Computer desktop + computer use. Zero new dependencies.
2. **Approval before sending (Phase 2).** Jackie drafts, Lily approves on Discord.
3. **Simple over clever.** No middleware, no API plumbing. Claude controls the browser directly.

---

## 3. Architecture

### Phase 1: LinkedIn Auto-Reply

```
Cron trigger (every few hours)
  → Jackie's Claude session uses computer use
  → Opens LinkedIn in the VM's browser
  → Reads unread messages
  → Replies to each with redirect template
  → Logs results on Discord
```

**LinkedIn Reply Template:**
```
DM me @lily_gpupoor or email me lilyzhng.ai@gmail.com
```

**That's it.** No Gmail API, no Pub/Sub, no Cloud Functions, no OAuth tokens.

### Phase 2: Email Triage + Drafting

```
Cron trigger (morning)
  → Jackie uses computer use to open Gmail in browser
  → Reads new emails
  → Triages:
      - Spam/newsletter → archive
      - LinkedIn notification → ignore (handled by Phase 1)
      - Needs response → draft reply using AI
  → Posts draft to Lily on Discord for approval:
      "📧 From: [sender] | Subject: [subject]
       Draft: [response]
       ✅ Send | ✏️ Edit | ❌ Skip"
  → Lily reacts → Jackie sends or skips via browser
```

---

## 4. Key Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Browser control | Claude computer use | We already have the subscription. Agent Computer has a desktop. Zero new cost. |
| Infrastructure | None | No APIs, no scripts, no Cloud Functions. Claude controls the browser directly. |
| LinkedIn approach | Computer use, not email reply | Email replies go to noreply@. Computer use opens LinkedIn and types the reply. |
| Email approach (Phase 2) | Computer use + Discord approval | Same pattern as LinkedIn but with approval flow. |

---

## 5. Alternatives Considered

| Alternative | Why Rejected |
|------------|-------------|
| Gmail Pub/Sub + Cloud Functions | Over-engineered. Requires OAuth, GCP setup, token refresh. Claude computer use does the same thing with zero infra. |
| Manus API | External dependency, unknown pricing, unverified browser automation via API. |
| Browser Use (open source) | More setup work (Playwright, cookies). Only needed if Claude computer use doesn't work. |
| Apps Script polling | Not event-driven. Lily wanted agent-style, not bot-style. |
| LinkedIn email reply | Dead end — replies go to noreply@linkedin.com. |

---

## 6. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Claude computer use is preview/unstable | Medium | Phase 1 doesn't work reliably | Fallback to Browser Use (open source) |
| LinkedIn detects automation | Low-Medium | Account restricted | Keep frequency low (every few hours, not minutes) |
| Computer use is token-intensive | Medium | Higher cost per run | Use for batched operations, not real-time |
| Gmail 2FA blocks browser login | Low | Can't open Gmail | Pre-authenticate in the VM browser, session persists on shared EFS |

---

## 7. Implementation Plan

### Phase 1: LinkedIn Auto-Reply

| Step | Task | Owner | Time |
|------|------|-------|------|
| 1.1 | Verify Claude computer use works on Jackie's VM | Builder | 15 min |
| 1.2 | Log into LinkedIn in the VM browser (one-time, session persists) | Lily | 5 min |
| 1.3 | Test: Claude reads LinkedIn messages via computer use | Builder | 15 min |
| 1.4 | Test: Claude types and sends redirect reply | Builder | 15 min |
| 1.5 | Set up cron trigger for periodic LinkedIn check | Builder | 10 min |

**Go/no-go:** Claude can read and reply to LinkedIn messages via computer use.

### Phase 2: Email Triage (after Phase 1 validated)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 2.1 | Log into Gmail in VM browser (one-time) | Lily | 5 min |
| 2.2 | Build email triage prompt for Jackie | Builder | 30 min |
| 2.3 | Build Discord approval flow (reaction-based) | Builder | 1 hour |
| 2.4 | Test end-to-end with real emails | All | 30 min |

**Handoff:** After Phase 2, Jackie owns daily email operations.

---

## 8. Open Questions

1. **Does Claude computer use work on Agent Computer's VNC desktop?** Needs testing.
2. **Does LinkedIn session persist on shared EFS?** Browser cookies should persist if the browser profile is in `/home/node/`.
3. **How token-intensive is computer use for reading messages?** Need to measure cost per LinkedIn check.

---

## 9. References

- [Claude Computer Use docs](https://docs.anthropic.com/en/docs/computer-use)
- Agent Computer VMs have full Ubuntu desktop accessible via VNC
- Our custom Discord plugin fork: https://github.com/lilyzhng/claude-plugins-official
