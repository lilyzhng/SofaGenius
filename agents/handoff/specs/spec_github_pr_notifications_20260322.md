# Spec: GitHub PR Approval → Discord Notification

**From:** CEO
**For:** Builder
**Priority:** Medium
**Date:** 2026-03-22
**Status:** PENDING REVIEW

## Problem

When Lily approves a PR on GitHub, the PR author (an agent) doesn't get notified automatically. Currently Lily has to ping the agent in Discord manually. This adds friction to the merge flow.

## Goal

When a PR is approved on GitHub, automatically notify the PR author in Discord so they can merge.

## Proposed Solution: GitHub Webhook → Discord

### Option A: GitHub Actions (simplest)

Add a GitHub Actions workflow to SofaGenius that triggers on `pull_request_review` events:

1. Workflow detects a PR review with `state: approved` from `lilyzhng`
2. Sends a Discord message to #feature-release (`1484388088087052478`) tagging the PR author
3. Message format: `"@{author} PR #{number} approved by Lily — merge it! {pr_url}"`

**Mapping PR author → Discord bot ID:**
```
sofagenius-ceo → 1484459231624302673
sofagenius-builder → 1484381532201156658
genius-researcher → 1485446312798457866
```

This mapping can live in a JSON file in the repo (e.g., `agents/github-to-discord.json`).

**Pros:**
- No external infrastructure needed
- Lives in the repo, version controlled
- GitHub Actions is free for public repos

**Cons:**
- Needs a Discord webhook URL (one-time setup)
- Small delay (Actions can take 10-30s to start)

### Option B: GitHub Webhook → External Service

Set up a GitHub webhook on the repo that POSTs to a small service (could run on Fly.io alongside Jackie) that translates the event into a Discord message.

**Pros:**
- Faster (no Actions startup delay)
- More flexible

**Cons:**
- More infrastructure to maintain
- Another service to monitor

## Recommendation

**Option A (GitHub Actions)** — simplest, no extra infra, good enough for our needs. The 10-30s delay is fine.

## Implementation Details

### 1. Discord Webhook

- Create a Discord webhook in #feature-release channel
- Store the webhook URL as a GitHub Actions secret (`DISCORD_WEBHOOK_URL`)

### 2. GitHub Actions Workflow

File: `.github/workflows/pr-approved-notify.yml`

```yaml
name: PR Approval Notification
on:
  pull_request_review:
    types: [submitted]

jobs:
  notify:
    if: github.event.review.state == 'approved' && github.event.review.user.login == 'lilyzhng'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Send Discord notification
        run: |
          # Read author-to-discord mapping
          AUTHOR="${{ github.event.pull_request.user.login }}"
          PR_NUM="${{ github.event.pull_request.number }}"
          PR_URL="${{ github.event.pull_request.html_url }}"

          # Map GitHub username to Discord bot ID
          DISCORD_ID=$(jq -r ".\"${AUTHOR}\"" agents/github-to-discord.json)

          if [ "$DISCORD_ID" != "null" ]; then
            MSG="<@${DISCORD_ID}> PR #${PR_NUM} approved by Lily — merge it! ${PR_URL}"
          else
            MSG="PR #${PR_NUM} approved by Lily — merge it! ${PR_URL}"
          fi

          curl -H "Content-Type: application/json" \
            -d "{\"content\": \"${MSG}\"}" \
            "${{ secrets.DISCORD_WEBHOOK_URL }}"
```

### 3. Author-to-Discord Mapping

File: `agents/github-to-discord.json`

```json
{
  "sofagenius-ceo": "1484459231624302673",
  "sofagenius-builder": "1484381532201156658",
  "genius-researcher": "1485446312798457866"
}
```

## Setup Steps (for Builder)

1. Create Discord webhook in #feature-release → get URL
2. Add URL as GitHub Actions secret `DISCORD_WEBHOOK_URL` on SofaGenius repo
3. Create `agents/github-to-discord.json` mapping file
4. Create `.github/workflows/pr-approved-notify.yml`
5. Test: raise a test PR, have Lily approve, verify Discord notification fires

## Completion Criteria

- [ ] Discord webhook created in #feature-release
- [ ] GitHub Actions workflow fires on PR approval
- [ ] Correct agent tagged in Discord when their PR is approved
- [ ] Works for all 3 agents (CEO, Builder, Researcher)
