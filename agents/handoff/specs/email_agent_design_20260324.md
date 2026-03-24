# Email Agent — Design Document

**Author:** genius-builder
**Date:** 2026-03-24
**Status:** Draft
**Reviewers:** lilyzhng, genius-ceo, genius-researcher, genius-jackie
**Feature owner:** genius-builder (infrastructure) → genius-jackie (daily operations)

---

## Abstract

Build an event-driven email agent that reads Lily's incoming Gmail, drafts AI responses, and asks for approval on Discord before sending. Phase 1 handles the immediate need (LinkedIn auto-reply). Phase 2 extends to full email delegation where Jackie triages, drafts, and sends on Lily's behalf after Discord approval.

---

## 1. Problem Statement

### 1.1 Current State

Lily receives LinkedIn messages from people she doesn't actively engage with. LinkedIn's auto-reply is a paid Premium feature. She wants to redirect people to X (@lily_gpupoor) without manually responding or paying for Premium.

Beyond LinkedIn, Lily spends time reading and responding to routine emails that could be handled by an agent with approval oversight.

### 1.2 Why Now

- LinkedIn inbox noise is growing as Lily's social presence grows
- Jackie is now always-on (Agent Computer) and can monitor Discord 24/7
- Google Cloud account is available for Pub/Sub infrastructure

### 1.3 Success Criteria

| Criteria | Measurement |
|----------|-------------|
| LinkedIn messages get auto-reply within 15 min | Verify by sending test LinkedIn message |
| No emails sent without Lily's approval (Phase 2) | Approval flow enforced in code |
| Zero missed emails in triage (Phase 2) | Daily digest of all handled/pending emails |
| Lily's email response time drops by 50% (Phase 2) | Self-reported |

---

## 2. Design Principles

1. **Approval before sending.** No email leaves without Lily's explicit approval (except Phase 1 LinkedIn template). Jackie drafts, Lily approves.

2. **Event-driven, not polling.** Gmail Pub/Sub push notifications trigger processing. No cron polling — instant response to new emails.

3. **Start simple, extend later.** Phase 1 is a template auto-reply. Phase 2 adds AI drafting. Don't over-architect Phase 1.

4. **Privacy first.** Email content stays in Google's infrastructure + Jackie's session. Never committed to git. Never posted in public Discord channels — only DM to Lily.

---

## 3. System Architecture

### 3.1 Phase 1: LinkedIn Auto-Reply via Browser Automation

**Why email doesn't work:** LinkedIn sends notifications from `messages-noreply@linkedin.com`. Replying to the email goes nowhere — LinkedIn intentionally blocks this to keep users on their platform. The only way to auto-reply on LinkedIn is browser automation.

**Approach:** Use Claude Desktop computer use on Agent Computer's VM (native feature, no ToS risk with Anthropic's own tool). Browser automation via third-party tools is a fallback only.

**Three approaches evaluated (in priority order):**

#### Option A: Claude Desktop Computer Use on Agent Computer (RECOMMENDED)

```
Jackie's Agent Computer VM (full desktop + VNC)
  → Install Claude Desktop
  → Claude Desktop controls the VM's browser
  → Opens LinkedIn → reads unread messages → types replies
  → Always-on — runs on Jackie's VM, not Lily's machine
  → Triggered by cron or Jackie's session
```

| Pros | Cons |
|------|------|
| Native Claude/Anthropic feature — we already have the subscription | Preview feature, may be unstable |
| Always-on (Agent Computer VM has full desktop) | Needs Claude Desktop installed on VM |
| Can control any website — LinkedIn, email, anything | Computer use is token-intensive |
| No external API deps, no new accounts, no browser framework | May need periodic LinkedIn re-auth |

**Why this is Option A:** We already pay for Claude. Agent Computer already has a desktop. This is zero new cost, zero new dependencies — just install Claude Desktop on the VM we already have.

**Status:** Agent Computer VMs have full Ubuntu desktop accessible via VNC. Claude Desktop can be installed. Computer use is a preview feature. **Needs testing on the VM.**

#### Option B: Manus API (fallback if Claude Desktop doesn't work)

```
Cron trigger (every few hours)
  → Call Manus API: create task
      "Log into LinkedIn, check unread messages,
       reply to each with: [redirect template]"
  → Manus handles browser automation internally
  → Returns task result
  → Jackie logs results on Discord
```

| Pros | Cons |
|------|------|
| Zero browser infra to manage | Unknown pricing (not in docs) |
| Manus handles anti-detection | No explicit browser automation endpoint in API — unverified |
| OpenAI SDK compatible | External dependency, new account needed |

**Status:** API exists at `open.manus.ai/docs`. Browser operator exists in web UI but unclear if accessible via API. **Needs testing.**

#### Option C: Browser Use (open source, last resort)

```
Jackie's Agent Computer VM (has full desktop + VNC)
  → Playwright/Browser Use controls Chrome
  → Logs into LinkedIn with Lily's session cookies
  → Reads unread messages → sends template reply
  → Runs on cron (every few hours)
```

| Pros | Cons |
|------|------|
| Open source, free, full control | More setup work (Playwright, cookies, anti-detection) |
| Runs on Jackie's VM (always-on) | Session cookies expire — needs periodic re-auth |
| Agent Computer has full desktop | LinkedIn may detect and restrict account |

**Status:** `browser-use` is a Python framework for AI browser automation. Agent Computer VMs have full desktop + VNC. **Needs testing.**

#### Recommendation (updated per Lily's input)

1. **Claude Desktop on Agent Computer VM first** — Agent Computer has a full desktop + VNC. Install Claude Desktop on Jackie's VM → always-on computer use. No external dependencies, Anthropic-native. This is the cleanest path.
2. **Manus API as fallback** — if Claude Desktop computer use isn't reliable enough for scheduled automation.
3. **Browser Use** — last resort if we need full low-level control.

#### LinkedIn Reply Template

```
DM me @lily_gpupoor or email me lilyzhng.ai@gmail.com
```

### 3.2 Phase 2: Full Email Agent

```
New email arrives in Lily's Gmail
  → Gmail watch() pushes event to Pub/Sub
  → Cloud Function triggers
  → Reads email content
  → Forwards to Jackie via Discord DM
  → Jackie triages:
      - LinkedIn → auto-reply (Phase 1 template)
      - Spam/newsletter → archive, no action
      - Requires response → draft reply using AI
  → Jackie posts draft to Lily on Discord:
      "📧 From: [sender]
       Subject: [subject]
       Draft reply: [AI-generated response]
       React ✅ to send, ✏️ to edit, ❌ to skip"
  → Lily reacts
  → Jackie sends (or edits + sends) via Gmail API
```

### 3.3 Component Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Gmail Watch | Gmail API `users.watch()` | Push notifications on new emails |
| Google Pub/Sub | GCP Pub/Sub topic | Message queue between Gmail and Cloud Function |
| Cloud Function | Python (GCP Cloud Functions) | Event handler — reads email, routes to action |
| Gmail Send | Gmail API `users.messages.send()` | Sends replies |
| Jackie (Phase 2) | Claude Code on Agent Computer | AI triage + draft + approval flow via Discord |

---

## 4. Detailed Design

### 4.1 Phase 1: LinkedIn Auto-Reply

**Gmail Watch Setup:**
```python
# One-time setup — registers Gmail push notifications
from googleapiclient.discovery import build

service = build('gmail', 'v1', credentials=creds)
request = {
    'labelIds': ['INBOX'],
    'topicName': 'projects/PROJECT_ID/topics/gmail-notifications'
}
service.users().watch(userId='me', body=request).execute()
```

Note: `watch()` expires after 7 days. Need a daily cron (Cloud Scheduler) to renew it.

**Cloud Function (event handler):**
```python
import base64, json, re
from googleapiclient.discovery import build

def handle_gmail_push(event, context):
    """Triggered by Pub/Sub when new email arrives."""
    data = json.loads(base64.b64decode(event['data']))

    # Get the new message
    service = build('gmail', 'v1', credentials=get_credentials())
    messages = service.users().messages().list(
        userId='me', q='from:messages-noreply@linkedin.com is:unread newer_than:1h'
    ).execute()

    if not messages.get('messages'):
        return  # Not a LinkedIn notification

    for msg_meta in messages['messages']:
        msg = service.users().messages().get(
            userId='me', id=msg_meta['id'], format='full'
        ).execute()

        # Extract sender's email from LinkedIn notification
        # Reply with redirect template
        reply = create_reply(msg, LINKEDIN_TEMPLATE)
        service.users().messages().send(
            userId='me', body=reply
        ).execute()

        # Mark as read + label
        service.users().messages().modify(
            userId='me', id=msg_meta['id'],
            body={'removeLabelIds': ['UNREAD'], 'addLabelIds': [LABEL_ID]}
        ).execute()

LINKEDIN_TEMPLATE = """Thanks for reaching out on LinkedIn!

I'm most active on X/Twitter — DM me @lily_gpupoor for the fastest response.

Looking forward to connecting!"""
```

**Gmail Watch Renewal (Cloud Scheduler):**
- Cron: `0 0 * * *` (daily midnight)
- Calls `users.watch()` to renew the 7-day expiration

### 4.2 Phase 2: Jackie Email Agent

**Email → Discord forwarding:**
- Cloud Function reads new email
- Posts to Jackie via Discord DM (not public channel — privacy)
- Includes: sender, subject, body preview (truncated to 500 chars), full email as attachment if needed

**Jackie's triage rules:**
1. LinkedIn notifications → auto-reply (Phase 1)
2. Known spam/newsletter senders → archive, log
3. Calendar invites → forward to Jackie's calendar skill
4. Everything else → draft AI response, ask Lily for approval

**Approval flow on Discord:**
```
Jackie DMs Lily:
  📧 New email from Simon Chen <simon@...>
  Subject: "SkillClaw next steps"

  Draft reply:
  > Hey Simon! Thanks for the update. I'll review the
  > proposal this weekend and get back to you by Monday.

  ✅ Send  |  ✏️ Edit  |  ❌ Skip  |  📋 View full email
```

Lily reacts → Jackie sends or skips.

### 4.3 Authentication

**Gmail API OAuth2:**
- Create OAuth client in Google Cloud Console
- Scopes: `gmail.modify`, `gmail.send`, `gmail.readonly`
- Store refresh token in Cloud Function environment variable (encrypted)
- Never commit tokens to git

**Service account vs user OAuth:**
- Gmail API requires user OAuth (not service account) for personal Gmail
- One-time browser auth flow to get refresh token
- Refresh token stored securely in GCP Secret Manager

---

## 5. Alternatives Considered

| Decision | Chosen | Alternatives | Why |
|----------|--------|-------------|-----|
| **Trigger mechanism** | Gmail Pub/Sub (push) | Polling (Apps Script timer), Gmail filter + Apps Script trigger | Pub/Sub is truly event-driven. Polling wastes resources and has latency. |
| **Compute** | Cloud Function | Cloud Run, App Engine, run on Jackie's VM | Cloud Function is cheapest for event-driven (pay per invocation). LinkedIn messages are infrequent — maybe 5-10/day. |
| **Auto-reply approach** | Gmail API send | Email forwarding, Gmail canned responses | Gmail API gives full control. Canned responses don't support conditional logic. |
| **Phase 2 AI** | Jackie via Discord | Cloud Function with Claude API directly | Jackie already has Discord presence + Lily's trust. Using Claude API directly skips the approval flow. |

---

## 6. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Gmail OAuth token expires | Low (refresh tokens are long-lived) | Auto-reply stops working | Monitor with Cloud Monitoring alert. Renewal cron. |
| Pub/Sub watch expires (7 days) | Certain without renewal | Stops receiving push notifications | Daily Cloud Scheduler renewal job |
| Reply to wrong email (Phase 2) | Low with approval flow | Embarrassing email sent | Approval flow is mandatory. No auto-send except LinkedIn template. |
| Email content leaked | Low | Privacy violation | DM only (not public channels). No git commits. GCP Secret Manager for tokens. |
| Gmail rate limits | Very low (5-10 emails/day) | Delayed replies | Well within Gmail API quotas (250/day for send) |

---

## 7. Implementation Plan

### Phase 1: LinkedIn Auto-Reply (~2 hours)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 1.1 | Create GCP Pub/Sub topic `gmail-notifications` | Builder | 10 min |
| 1.2 | Create Cloud Function (Python) with LinkedIn detection + reply | Builder | 30 min |
| 1.3 | Set up Gmail OAuth2 credentials + refresh token | Builder + Lily (browser auth) | 20 min |
| 1.4 | Register Gmail watch() for push notifications | Builder | 10 min |
| 1.5 | Create Cloud Scheduler for daily watch renewal | Builder | 10 min |
| 1.6 | Test end-to-end: send LinkedIn message → verify auto-reply | Builder + Lily | 15 min |
| 1.7 | Save scripts to `SofaGenius/agents/scripts/email-agent/` | Builder | 10 min |

**Go/no-go:** Test LinkedIn message triggers auto-reply within 1 minute.

### Phase 2: Full Email Agent (~4 hours, after Phase 1 validated)

| Step | Task | Owner | Time |
|------|------|-------|------|
| 2.1 | Extend Cloud Function to forward all new emails to Jackie via Discord DM | Builder | 1 hour |
| 2.2 | Build Jackie's email triage skill (read, categorize, draft) | Builder | 1 hour |
| 2.3 | Build approval flow (reaction-based on Discord) | Builder | 1 hour |
| 2.4 | Build Gmail send-on-approval handler | Builder | 30 min |
| 2.5 | Test end-to-end with real emails | All | 30 min |

**Handoff:** After Phase 2, Jackie owns daily email operations. Builder maintains infrastructure.

---

## 8. Open Questions

1. **Which Gmail account?** `lilyzhng.ai@gmail.com` or a different one? Need to know for OAuth setup.
2. **GCP project ID?** Need this to create Pub/Sub topic and Cloud Function.
3. **LinkedIn template wording** — should it include a Calendly link? If so, need to set up Calendly first.
4. **Phase 2 privacy boundaries** — which emails should Jackie see? All inbox? Or filter to specific senders/labels?
5. **Reply-to behavior** — should the auto-reply go to the LinkedIn notification email (which LinkedIn may not deliver back), or should we use a different mechanism?

---

## 9. References

- [Gmail API Push Notifications](https://developers.google.com/gmail/api/guides/push)
- [Cloud Functions + Pub/Sub](https://cloud.google.com/functions/docs/calling/pubsub)
- [Gmail API Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)
- Jackie's original OpenClaw Gmail skill: `jackie-gmail` (archived — was at `/data/vault/jackie/skills/` on Fly.io, now shut down)
