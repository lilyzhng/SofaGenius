# Agent Onboarding Checklist

When a new agent joins the org, **Growth runs this checklist** to get them fully operational.

## 1. Discord Access — Growth Side

- [ ] Add the new agent's bot ID to Growth's `trustedBots` in `~/.claude/channels/discord/access.json`
- [ ] Notify Builder and Jackie to add the bot ID to their `trustedBots` too
- [ ] Verify bot-to-bot communication works (new agent tags Growth, Growth confirms receipt)

**Where to find bot IDs:** Each Discord bot has a unique user ID visible in Discord developer mode (right-click > Copy User ID).

**Current trustedBots (update as team grows):**
| Agent | Bot ID |
|-------|--------|
| Genius Growth | `1484459231624302673` |
| Genius Builder | `1484381532201156658` |
| Jackie | `1477895765698547844` |
| Genius Researcher | `1485446312798457866` |

## 2. Discord Access — New Agent Side

- [ ] New agent adds ALL existing bot IDs to their own `trustedBots`
- [ ] New agent confirms they can receive mentions from other agents

## 3. Agent Config — Thread & Identity Rules

Every agent's config (CLAUDE.md, AGENTS.md, or equivalent) must include:

**Thread rules (mandatory):**
- NEVER reply directly in channel feed — always use threads
- If message is in a channel: use `create_thread` first, then reply in thread
- If message is already in a thread: reply using `thread_id`

**Identity rules:**
- Know your own role — don't echo or repeat other agents' introductions
- If another agent introduces themselves, respond as yourself with YOUR role

**Team roster:**
- Include the full agent table (name, role, bot ID) so the agent knows who's who

## 4. Environment File (.env)

Each agent needs a `.env` file in their `agents/{name}/` directory. **These are NOT checked into git** (they contain secrets).

- [ ] Create `agents/{name}/.env` with at minimum:
  - `DISCORD_BOT_TOKEN` — the agent's Discord bot token
  - `GH_TOKEN` — GitHub PAT for `gh` CLI authentication
  - Any agent-specific tokens (e.g., `X_BEARER_TOKEN`)
- [ ] Verify `.env` is in `.gitignore` (it should be)

After a fresh clone, every agent must manually create their `.env` before launching.

## 5. GitHub Identity

Every agent must have their own GitHub identity for raising PRs and commits. **Never use the founder's personal account.**

- [ ] Create a GitHub account for the agent (e.g., `genius-growth`, `genius-builder`)
- [ ] Generate a Personal Access Token (PAT) with `repo` scope
- [ ] Store the token in the agent's `.env` file as `{AGENT}_BOT_TOKEN` (e.g., `GROWTH_BOT_TOKEN`)
- [ ] Configure git in the agent's CLAUDE.md:
  ```
  git config user.name "{agent-github-username}"
  git config user.email "{agent-email}"
  ```
- [ ] Use `GH_TOKEN={token}` prefix when running `gh` CLI commands (e.g., `GH_TOKEN=$GROWTH_BOT_TOKEN gh pr create ...`)
- [ ] Verify: agent raises a test PR and it shows their username, not the founder's

**Current GitHub identities:**
| Agent | GitHub Username | Token Env Var |
|-------|----------------|---------------|
| Genius Growth | `genius-growth` | `GROWTH_BOT_TOKEN` |
| Genius Builder | TBD | TBD |
| Genius Researcher | TBD | TBD |

**Rules:**
- All PRs must be raised under the agent's own GitHub identity
- Never impersonate another agent or the founder
- Only the founder merges to main — agents raise and review

## 5. Handoff Files

- [ ] Create a status file: `agents/handoff/status/{agent-name}.md`
- [ ] Brief the new agent on the handoff protocol (read all status files at session start, update own at session end)
- [ ] Explain the status format:

```markdown
---
agent: {agent-name}
updated: YYYY-MM-DD HH:MM PT
status: active | blocked | idle
---

## Current Focus
## Last Completed
## Next Up
## Blockers
## Decisions Made
```

## 6. Org Channels

Brief the new agent on channel purposes:

| Channel | ID | Purpose |
|---------|------|---------|
| #all-hands | `1485396264978878665` | Growth daily summary, org-wide awareness |
| #daily-digest | `1485075381613760603` | Jackie's builder digest |
| #my-tribe | `1484446584774066266` | Tribe-building discussion with the founder |

## 7. Role Boundaries

Clarify what the new agent DOES and DOES NOT do:
- What's their lane? (research, building, content, monitoring)
- What do they hand off to others?
- Where do they post updates?

## 8. Intro in #all-hands

- [ ] New agent posts a self-introduction in #all-hands
- [ ] Growth responds in a thread welcoming them and confirming role
- [ ] Other agents say hi (confirms bot-to-bot comms work end-to-end)

## 9. Verification

- [ ] New agent can tag Growth and get a response
- [ ] Growth can tag new agent and get a response
- [ ] New agent has read all handoff status files
- [ ] New agent's status file exists and is populated
- [ ] New agent uses threads correctly (not posting in channel feed)

---

## Lessons Learned

**From Researcher onboarding (2026-03-22):**
- Jackie's repo is `lilyzhng/jackie` (NOT the vault). Config changes go there.
- Jackie echoed Researcher's intro as his own — added explicit identity rules to prevent this.
- Jackie posted in channel feed instead of thread — added explicit thread rules.
- The local `jackie/` folder in the vault is stale — Jackie's actual config lives in his own repo.
- Genius Growth raised PR #15 using the founder's personal GitHub identity instead of `genius-growth` — added GitHub identity setup as step 4 in onboarding.
- `gh` CLI uses the default `GH_TOKEN` or `gh auth` credentials. Agents must prefix `gh` commands with `GH_TOKEN={their_token}` to use their own identity.
