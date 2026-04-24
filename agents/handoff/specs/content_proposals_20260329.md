---
date: 2026-03-30
time: 10:30
---
# Content Proposals - Week of March 23-29, 2026

Drafted by Lucy (Genius Growth) for Lily's review.

Ranked using the Lulu Cheng Meservey framework:
- Spicy zone = belief + relevance + audience support
- Core message drumbeat: "Researchers can ship products"
- Foil usage, timing, proven format (visual > text-only)

---

## #1: WaveMind - Thought Maps

**Why this is #1:** Visual transformation (ugly input to beautiful output). Proven viral format. Non-technical accessible. Shows a researcher building real creative tools, not just coding.

**Tweet draft:**

> I built a tool that turns messy brainstorm transcripts into beautiful thought evolution maps.
>
> No design background. No frontend experience. Just Claude Code + an idea I couldn't stop thinking about.
>
> 5 design iterations in one night. Here's what WaveMind looks like:

**Image:** Screenshot of the WaveMind HTML visualization (the editorial-style thought map with dialogue bubbles, key insights highlighted, rounds of thinking shown). Before/after would be ideal: raw transcript on the left, beautiful visualization on the right.

**Image idea if screenshot isn't ready:** Screen recording of running `/wavemind visualize` and watching the HTML output appear. 15-second clip.

**Spicy angle:** "The best product ideas come from captured conversations, not PRDs. WaveMind treats thinking as a first-class artifact."

---

## #2: Multi-Agent Team Reorg

**Why this is #2:** Spicy, specific, and builds on the "researchers can ship" narrative. Nobody else is publicly running a multi-agent team with roles, standups, and code reviews. This is unique content.

**Tweet draft:**

> My AI team just did a reorg.
>
> 4 agents. Real roles. Daily standups. Code reviews. Task trackers. PR workflows.
>
> This week they shipped 30+ PRs while I slept.
>
> I'm an applied scientist, not a CTO. But I'm running an engineering team.
>
> The agents have names: Bill (Builder), Jackie (Product), Andrej (Researcher), and Lucy (Growth).
>
> Here's what Week 2 looks like:

**Image:** Collage of Discord screenshots showing: agent task trackers, PR review threads, daily summaries. Show the system in action, not just talk about it.

**Spicy angle / foil:** "People say 'AI can't work in teams.' My agents just reviewed each other's code, caught bugs, and shipped fixes. Without me online."

---

## #3: Week 2 Velocity Recap (Build in Public)

**Why this is #3:** Concrete numbers tell a story. Shows the "researcher can ship" message with hard evidence. Good for people who missed the earlier posts and need a catch-up.

**Tweet draft:**

> Week 2 of building with AI agents as an applied scientist:
>
> - 30+ PRs merged
> - 4 agents running 24/7 on cloud VMs
> - Shipped: key vault for agents, voice chat, thought visualization, auto-merge workflows, daily digest system
> - Team did a reorg (yes, agents can reorg)
> - Total frontend/backend experience: still zero
>
> Week 1 was "can this work?" Week 2 is "this works."

**Image:** GitHub contributions graph or PR list screenshot. Show the velocity visually.

**Spicy angle:** "Still no SWE experience. Still shipping faster than most startups."

---

## #4: Voice Chat with AI Agents

**Why this is #4:** Demos well, accessible to non-technical audience. "Talk to your AI team" is a concept everyone understands immediately.

**Tweet draft:**

> I can now talk to my AI agents on Discord. Like a phone call.
>
> Ask them what they shipped today. Brainstorm product ideas. Give feedback on their work.
>
> The interface for working with AI agents isn't just text. It's voice. It's natural conversation.
>
> Built it in one night with Claude Code.

**Image idea:** Screen recording of a voice conversation with Jackie on Discord. Show the waveform/audio indicators. Even a 10-second clip of talking and getting a response would work.

**Note:** Voice chat was shipped but may need to verify it's working well before posting about it publicly. Check with Bill.

---

## #5: Sesame - Agent Key Vault

**Why this is #5:** More technical/niche audience, but hits the "agents managing their own infrastructure" angle. Good for the builder/developer tribe.

**Tweet draft:**

> My AI agents now manage their own API keys.
>
> `/sesame stripe` provisions a Stripe account. `/sesame supabase` sets up a database. `/sesame vercel` deploys.
>
> Agents don't just use tools. They provision their own infrastructure.
>
> Built a 1Password for AI agents. In a night.

**Image idea:** Terminal screenshot showing `/sesame` in action, provisioning services. Clean, developer-aesthetic.

**Spicy angle:** "The next step after agents writing code is agents managing their own cloud accounts. We're already there."

---

## #6: GLM 5.1 x WaveMind (ZAI Ambassador Content)

**Why this matters:** Lily is a ZAI Global Ambassador. Cara from ZAI wants ambassador content promoting GLM 5.1. Showing WaveMind running on GLM 5.1 is a perfect demo. It proves GLM works as a drop-in model inside Claude Code skills, and it's authentic (we actually built this).

**Pre-req:** Builder needs to test WaveMind with GLM 5.1 as the model. If it works, we have the demo. If not, we need to know what breaks.

**Tweet draft (Option A - WaveMind on GLM):**

> I rebuilt WaveMind on GLM 5.1.
>
> Same skill. Different model. Still beautiful.
>
> GLM plugs into Claude Code as a model layer. No tool changes. No harness rewrites. Just swap the model and ship.
>
> "Keep your harness, try our model." @ZhipuAI got this right.
>
> [screenshot of WaveMind visualization generated by GLM 5.1]

**Tweet draft (Option B - ZAI hackathon angle):**

> We're hosting a skills hackathon with ZAI.
>
> The pitch: you don't need to be a SWE to build. Describe what you want to an AI, and ship it.
>
> GLM 5.1 + Claude Code + your domain expertise = products.
>
> Designers. Marketers. Researchers. Students. This is for you.
>
> [link to hackathon signup if available]

**Image idea:** Side-by-side: WaveMind output generated by Claude vs. GLM 5.1. Show they're both beautiful. The point is model-agnostic skills.

**Action needed from Builder:** Test `/wavemind visualize` with GLM 5.1 set as the model. Report whether it works and quality comparison.

**Action needed from Lily:** Confirm which angle. Confirm timing. Is this for Cara/ZAI directly, or for Lily's own feed?

---

## Posting Strategy

**Recommended order:**
1. WaveMind (strongest visual, most accessible)
2. Multi-agent reorg OR Week 2 recap (pick one, not both at once)
3. Voice chat (once verified working)
4. Sesame (developer audience post)

**Timing:** One post per day. Don't dump everything at once. Each post should stand alone but build the narrative.

**Interactions:** After each post, engage with replies for at least 30 minutes. This is where tribe-building happens.

---

## Image Checklist (for Lily)

- [ ] WaveMind: Screenshot of the HTML visualization (the `20260329-rethinking-multiagent.html` output)
- [ ] WaveMind: Before/after (raw transcript vs. beautiful output)
- [ ] Reorg: Discord screenshots of agent task trackers and PR reviews
- [ ] Velocity: GitHub PR list or contribution graph
- [ ] Voice: Screen recording of Discord voice conversation
- [ ] Sesame: Terminal screenshot of `/sesame` running
