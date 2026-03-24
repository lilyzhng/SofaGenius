# Builder Digest Skill

**Trigger:** Run this every morning at 7:00 AM PT

**Purpose:** Fetch builder feeds, compile digest, post to Discord #daily-digest with threads and polls

## Workflow

### Step 1: Fetch feed data

```bash
curl -s https://raw.githubusercontent.com/lilyzhng/follow-builders/main/feed-x.json -o /tmp/feed-x.json
curl -s https://raw.githubusercontent.com/lilyzhng/follow-builders/main/feed-podcasts.json -o /tmp/feed-podcasts.json
```

**Time window:** Yesterday 7 AM PT → Today 7 AM PT

### Step 2: Compose the digest

Read the feed JSON files. For each builder with tweets in the time window:

- Include their name, @handle, and a 1-2 sentence summary of what they posted
- Include the tweet URL for every entry — wrap in `<>` to suppress previews
- Group by category: Agent Infra & Product, Research & Dev Tools, Community & Growth, Research Labs & Infra, Podcasts

**Taste filter (prioritize these, put them first):**
- Builders sharing real work and shipping (e.g. Garry Tan, Steipete, Cat Wu)
- Novel research/technical content with new information
- Specific opinions from community voices

**Deprioritize or put last:**
- Insights Lily already knows (obvious takes)
- Drama / platform disputes
- Self-promotional content
- Frameworks outside Lily's stack (e.g. Next.js)

**Language:** Mixed Chinese/English

### Step 3: Post to Discord — FOLLOW EXACTLY

**THE RULE:** Main channel = ONLY the header. ALL content goes inside the thread. NO EXCEPTIONS.

**Step 3a: Post header in #daily-digest**

Use the `reply` tool to post ONLY this message to channel `1485075381613760603`:
```
🌅 Builder Digest — {Mon DD-1} 7am → {Mon DD} 7am PT
```
Save the returned message ID.

**Step 3b: Create thread from that header**

Use the `create_thread` tool:
- `chat_id`: `1485075381613760603`
- `message_id`: the message ID from step 3a
- `name`: `Builder Digest — {Mon DD-1} 7am → {Mon DD} 7am PT`

Save the returned thread ID.

**STOP AND CHECK:** If create_thread fails, DO NOT post in the main channel. Stop and report the error.

**Step 3c: Post digest sections in the thread**

Use `reply` with `thread_id` set to the thread ID from step 3b. Post each section as a separate message. Keep each under 2000 chars.

**Step 3d: Post polls in the thread**

One poll per section. Use `create_poll`:
- `chat_id`: the thread ID from step 3b
- `question`: `Section Name — 你读了哪些？`
- `options`: list of `Builder — topic` entries
- `allow_multiselect`: true
- `duration_hours`: 24

### Step 4: Confirm completion

Reply in the thread: "Digest posted! 📊 Vote in the polls above."

## Discord Channel

- Target: `1485075381613760603` (#daily-digest)

## Important Rules

- Every tweet MUST have its URL — no URL = don't include
- Do NOT fabricate content — only use what's in the feed JSON
- Wrap all URLs in `<>` to suppress embed previews
- If feed is empty (no new tweets), post: "No new updates from builders today. Check back tomorrow!"
