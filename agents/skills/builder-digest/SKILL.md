# Builder Digest Skill

**Trigger:** Run this every morning at 7:00 AM PT

**Purpose:** Fetch builder feeds, compile digest, post to Discord #daily-digest with threads

## Workflow

### Step 1: Fetch feed data

```bash
curl -s https://raw.githubusercontent.com/lilyzhng/follow-builders/main/feed-x.json -o /tmp/feed-x.json
curl -s https://raw.githubusercontent.com/lilyzhng/follow-builders/main/feed-podcasts.json -o /tmp/feed-podcasts.json
```

**Time window:** Yesterday 7 AM PT → Today 7 AM PT

### Step 1b: Fetch AI Valley newsletter

```bash
# Fetch the archive page to find the latest post URL
curl -s https://www.theaivalley.com/archive -o /tmp/aivalley-archive.html

# Parse the latest post slug from the archive page (first /p/ link)
LATEST_POST=$(grep -o '/p/[^"]*' /tmp/aivalley-archive.html | head -1)

# Fetch the full post to get trending tools
curl -s "https://www.theaivalley.com${LATEST_POST}" -o /tmp/aivalley-latest.html
```

From the latest post HTML, extract:
- **Post title and date**
- **Trending tools:** Each tool has a name, one-line description, and an external link to the tool's website. Extract ALL of these — the direct link to each tool is critical so Lily can try them immediately (not just the newsletter link).
- **Full newsletter link:** `https://www.theaivalley.com{LATEST_POST}`

Example output format for a tool:
`**Stitch 2.0** — Turn ideas into production-ready UI in seconds → <https://stitch.google.com>`

### Step 2: Compose the digest

Read the feed JSON files. For each builder with tweets in the time window:

- Include their name, @handle, and a 1-2 sentence summary of what they posted
- Include the tweet URL for every entry — wrap in `<>` to suppress previews
- Group by category: Agent Infra & Product, Research & Dev Tools, Community & Growth, Research Labs & Infra, Podcasts, AI Valley Highlights

**Taste filter (prioritize these, put them first):**
- Builders sharing real work and shipping (e.g. Garry Tan, Steipete, Cat Wu)
- Novel research/technical content with new information
- Specific opinions from community voices

**Deprioritize or put last:**
- Insights Lily already knows (obvious takes)
- Drama / platform disputes
- Self-promotional content
- Frameworks outside Lily's stack (e.g. Next.js)

**AI Valley Highlights section format:**
- Header: "🗞️ AI Valley Highlights — {post title} ({date})"
- List trending tools with name, description, and **direct link** to try each tool
- End with: "📰 Full newsletter: {link to full post}"
- Every tool link must be included so Lily can try them directly

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

**Step 3c: Post digest entries in the thread — ONE MESSAGE PER BUILDER**

Use `reply` with `thread_id` set to the thread ID from step 3b.

- Post **one message per builder** (not per section). This lets Lily reply to individual builders to discuss.
- For the **first builder in each category**, edit the message after sending to prepend a section header using `edit_message`. Example headers:
  - `## Agent Infra & Product`
  - `## Research & Dev Tools`
  - `## Community & Growth`
  - `## Research Labs & Infra`
  - `## AI Valley Highlights`
- Each message format: `**Name** (@handle) -- 1-2 sentence summary in mixed Chinese/English\n<tweet_url>`
- Keep each message under 2000 chars.

**Do NOT post polls.** Lily's engagement (replies to specific builders) is tracked instead.

### Step 4: Confirm completion

Reply in the thread: "Digest posted! Reply to any builder above to discuss."

## Discord Channel

- Target: `1485075381613760603` (#daily-digest)

## Important Rules

- Every tweet MUST have its URL — no URL = don't include
- Do NOT fabricate content — only use what's in the feed JSON
- Wrap all URLs in `<>` to suppress embed previews
- If feed is empty (no new tweets), post: "No new updates from builders today. Check back tomorrow!"
- If AI Valley fetch fails, skip the section — don't block the rest of the digest
- AI Valley only publishes Mon–Fri, so weekends may have no new issue
