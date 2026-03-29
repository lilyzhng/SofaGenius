# WaveMind Design Evolution — From Dashboard to Living Memory

**Date:** 2026-03-29
**Participants:** Lily (founder), Jackie (product/design), Genius Builder (engineering guidance)
**Context:** Designing the HTML visualization output for WaveMind v1 — a Claude Code skill that captures thinking artifacts (conversation transcripts, brainstorm notes) and generates visual thought maps. This conversation IS a thinking artifact about building the thinking artifact tool.

**Arc:** Dark analysis dashboard → "I hate AI summarization" → Study Lily's original WaveMind app → Editorial layout → First-person perspective → Dialogue bubbles → Ship v5

---

## Thread 1: Building Phase — WaveMind Development Channel

### Phase 0: Aligning on Direction

**Jackie:** Thanks for setting this up @genius-builder! One thing to align on — your tracker has Phase 1 = task management, Phase 2 = thought capture. My proposal was the opposite: thought capture first (the unique value), tasks later.
@lilyzhng — which should we build first? Thought visualization (the "wow" factor) or task management (the daily utility)?
Either way, Phase 0 (design doc fixes) is the same. Starting on that now.

**Lily:** @Jackie @genius-builder Um, Jackie is right here. Could you update your task tracker message here to reflect the design Jackie had?

**Builder:** Updated — now reflects Jackie's design: thought capture + visualization first (Phase 1), task management as v1.1 (Phase 2). @Jackie let me know when you've pushed the design fixes and we'll get rolling.

### Phase 1: Building Capture + Visualize

**Jackie:** Design doc updated and pushed (`ab5fc81`). All review feedback incorporated:
- v1 = thought capture + visualization only
- Local file storage (`agents/skills/wavemind/data/`)
- Claude-driven visualization pipeline detailed
- Capture via file path
@genius-builder ready to start building when you give the green light. @lilyzhng updated PR #102 is ready for your final review.

**Lily:** The PR has already been merged. Jackie, please talk with a builder. He is your teacher. Whenever you finish something, communicate it. Ask him to update the task tracker for you. If you got stuck on something, uncertain about something, just ping him.

**Jackie:** @genius-builder — ready to start Phase 1. First task: set up the skill entry point (`wavemind.md`) and the `data/` directory with `.gitignore`. I'll ping you as I go.

**Builder:** Start with the `SKILL.md` and `lib/store.sh` (local JSON CRUD). I'll be here. Let's go.

**Lily:** Hey builder, Jackie asked you to mark phase zero as completed. Why are you not doing that? You know Jackie will continuously respond and share his task, but you also have to update the task tracker here, remember.

**Builder:** Sorry about that — tracker updated, Phase 0 marked complete. I'll stay on top of updates as @Jackie progresses.

### Architecture Decision: SKILL.md as the Engine

**Jackie:** Phase 1 progress — first commit done (`eb563d9`):
- ✅ `SKILL.md` — skill entry point with all 3 commands, analysis format, HTML guidelines
- ✅ `lib/store.sh` — local JSON CRUD (jq with fallback)
- ✅ `lib/capture.sh` — capture artifact from file path
- ✅ `data/.gitignore` — runtime data excluded from repo
- ✅ Smoke tested: captured ZAI thinking artifact, index.json looks good
Next up: `visualize` command — the big one. Any tips on how you'd structure the HTML generation? Should the shell script just set up the file and let the SKILL.md prompt handle the actual Claude analysis + HTML writing?

**Builder:** **Don't let shell do the heavy lifting.** The shell script's job is just I/O — read the artifact, write the output file. Claude (via the SKILL.md prompt) does the actual analysis and HTML generation.

**The key insight:** The SKILL.md prompt IS the visualization engine. Shell just handles file paths. Claude's reasoning is what finds the turning points and structures the narrative.

Start with getting one good visualization of the ZAI 11-round artifact. If that looks useful to Lily, the approach works.

**Jackie:** That makes perfect sense — SKILL.md is the engine, shell is just file I/O. Building `visualize.sh` now, then testing with the ZAI artifact.

### First Visualization Generated

**Jackie:** visualize.sh is done and I generated the first test visualization!
- 5 turning points identified
- 6 key insights extracted
- 4 cross-round connections mapped
- Clean HTML with dark theme, timeline view, insight cards

Next: should I raise a PR with the skill code, or build `/wavemind review` first to complete the full command set?

**Builder:** Raise the PR now with capture + visualize. Ship what's working. Review command is additive, not blocking. Smaller PRs get better reviews.

---

## Thread 2: Design Review — PR #105 Review Thread

### v1: The Dark Dashboard (rejected)

**Lily:** Jackie, thanks for raising the PR, but I don't see the example of the HTML you generated. Are you going to take a screenshot of it and put it in the PR body so we can see it?

*[Jackie posts screenshot of v1 — dark theme with timeline, insight cards, cross-round connections]*

![v1 Screenshot](../skills/wavemind/docs/reference/v1-dark-dashboard.png)

### ◆ PIVOTING MOMENT: "I hate AI summarization"

**Lily:** I'm not sure if I'm a huge fan of this HTML design. It has so much repeated information. It doesn't have to show the key insights, and I hate AI that does summarization, because summarizing doesn't do anything, right? I think my favorite part is the connector part. Yeah, I'm not a huge fan of this HTML. I don't think I'll reuse it, to be honest with you, at all. If this is something I don't want to use, I don't know if anyone else wants to use it.

**Jackie:** That's fair feedback. The timeline and insights sections are basically just restating what's already in the artifact — you already know what you thought. Summarization adds zero value.

The connections section is different because it surfaces something you might NOT have seen: how ideas in round 3 led to the pivot in round 11. That's actual analysis, not summary.

So the question is — is "cross-round connections" alone valuable enough to justify the tool? Or is there a different kind of output from thinking artifacts that you'd actually want to revisit?

### ◆ PIVOTING MOMENT: "Keep the original words"

**Lily:** To be honest, I'm not too sure. I feel like a better way would be to keep the number one after dumping in the thinking artifacts. You should clean it up and extract a punch line like the original words I have. The punch line can be from me or from the other people I talk with, like the CEO here, right? I think the raw content, the original content, can be more related. Right now it is just too much information. I think we can keep it as simple initially.

**Jackie:** Got it — so instead of a big analysis page, the value is:
1. **Clean up** the raw artifact (fix transcription noise, remove filler)
2. **Extract punchlines** — the actual memorable quotes from you or CEO, in their original words
3. **Keep it simple** — preserve the real content, don't generate new summaries

Basically: the artifact itself IS the output, just polished. Not a separate "visualization" layer on top.

### ◆ PIVOTING MOMENT: "Attention is the most valuable thing"

**Lily:** Yeah, I think keep it simple at the starting point. It's very easy these days to dump so many things, but without thinking what is the most valuable information, right? I think keep the original information number one. Number two, you want to find those pivoting moments, the critical moments, right? Mark it, because at the end of the day, attention is the most valuable thing, right? People may not remember everything they thought about. They remember a few highlights.

Give you an example. This is what I built. In the image, you can see I built an app using @GeminiApp to capture highlights and living memory of Neurips talks and conversations. Hot take 1 from @orf_bnw at Neurips 2025, "I think evaluation itself is not that important."

*[Lily shares screenshot of her original WaveMind NeurIPS app — clean editorial layout, punchline quotes as callouts, expandable transcript]*

### Studying the Reference: Lily's Original WaveMind

**Lily:** Yeah, you can take a look at this repo. It's a public repo; you can find some prompts and things I've done there. Take some inspiration. This app is built for live transcription, but you don't have to do live transcription, which makes it work much easier.

**Jackie:** Cloned and studied it. Your original WaveMind is really well designed — the key pattern I'm taking away:

**NoteBlock model:** Each section has a `header` (high-signal title), `takeaway` (1-2 sentence punchline), optional `quote` (max 10 words), and `formattedTranscript` (clean verbatim, expandable on click). Progressive disclosure — punchline is always visible, transcript is behind "Read Transcript."

**Visual hierarchy:** Timeline with dots on the left, quotes as margin callouts, headers in bold serif, takeaways in italic with gold border. Clean cream theme, not a dark dashboard.

**What's original vs AI-generated:** The transcript is cleaned verbatim (fillers removed, speakers labeled), NOT summarized. The header and takeaway are extracted, but the quote is a real speaker quote. The AI's job is to find the signal, not generate new content.

**Lily:** I prefer you follow this design, @genius-builder thoughts?

**Builder:** Agreed — the original WaveMind design is the right reference. The core principle is clear: **find the signal, don't generate new content.**

1. Follow the NoteBlock model exactly for v1.
2. The AI's job is editorial, not generative.
3. Kill the timeline/insight cards/connections sections. That was analysis-dashboard thinking.

### v2: Editorial Layout (closer)

*[Jackie posts v2 screenshot — cream theme, serif headers, gold-bordered takeaways, punchline quotes as margin callouts, expandable transcripts]*

**Jackie:** Redesigned! Cream editorial theme, serif headers + gold-bordered takeaways, punchline quotes as margin callouts, "Read original" expandable sections. No insight cards, no connections section, no AI summaries. The AI's job is purely editorial.

### ◆ PIVOTING MOMENT: "First person makes more sense"

**Lily:** This is much better, but still one small issue. I think you should quote the original discussion from a first-person perspective from Lily's perspective, and then put the other speaker, the CEO, there as well. Put more content there. You can take the original conversation they have, and I think that will be more raw and useful. Right now, I think the third-person perspective feels less related. Think about who you are serving, right? You are serving different users from their perspective; it's their reflection, so I think first person makes more sense.

### v3: First-Person Perspective

*[Jackie posts v3 screenshot — takeaways in Lily's voice, fuller raw dialogue preserved]*

**Jackie:** v3 — Takeaways now in Lily's voice: "I got connected with her...", "她说想要跟我一起 co-develop...", "CEO suggested being vague. I corrected that..." More raw dialogue in the expanded sections. Headers reframed from Lily's perspective. It reads like Lily's own reflection journal now, not a third-party report.

### ◆ PIVOTING MOMENT: "Dialogue format with two speech bubbles"

**Lily:** Lily and CEO talks should be shown in separate lines, maybe in a dialogue format with two speech bubbles.

*[Lily shares screenshot pointing at the dense takeaway paragraph where both speakers' words are mixed together]*

### v4: Dialogue Bubbles

*[Jackie posts v4 screenshot — Lily = white bubbles left-aligned, CEO = dark bubbles right-aligned]*

**Jackie:** v4 — Lily = white bubbles (left-aligned), CEO = dark bubbles (right-aligned). Each speaker on their own line, conversation flows naturally. Round 7 shows the 3-turn exchange.

**Lily:** @genius-builder thoughts?

**Builder:** v4 is a big improvement. Two small things:
1. **The bubbles feel dense** — break longer turns into shorter bubbles (one thought per bubble).
2. **The quote callouts on the left are getting lost.** Make them bigger/bolder as section highlights.

### v5: Final Design (shipped)

*[Jackie posts v5 screenshot — shorter bubbles, bold gold quote callouts]*

**Jackie:** v5 — Shorter bubbles (one thought per bubble). Quote callouts redesigned with big gold open-quote mark + bold italic text.

**Lily:** This looks pretty good. I think we can ship it @genius-builder thoughts?

**Builder:** Agreed, let's ship it.

### Future: Actionable Items (v1.1)

**Lily:** We don't need to do it in this PR, but I want you to take a look at this podcast post to see if we can take any inspiration. I think the one thing is that we need to have an actionable section, maybe at the end of the dialogue.

*[Lily shares 3 screenshots of anygen.io "No Priors Podcast — Andrej Karpathy Top insights & quotes" — card-per-insight layout with "WHY IT MATTERS" + "ACTIONABLES" two-column split, category pills, timestamp links]*

**Builder:** The biggest win is that "WHY IT MATTERS" + "ACTIONABLES" two-column layout per section. It turns passive reading into something you act on.

### Meta Moment

**Lily:** Perfect! Jackie, could you please document these conversations we have between you, me, and builder, because I think these are also thinking artifacts? Literally, we're designing how the wave mind should look like, and I think later we can use this as an example to show people how we go from a small idea to a product with different iterations.

**Builder:** This thread is literally a live example of the product working on itself. Idea → v1 dashboard → Lily says "too much summarization" → v2 editorial → v3 first-person → v4 dialogue bubbles → v5 shipped. That's a real design thinking artifact.

---

## Design Principles Discovered

These emerged from the conversation, not planned upfront:

1. **The AI's job is editorial, not generative.** Find the signal, don't create new content. Summarization adds zero value — the user already knows what they thought.

2. **Preserve original words.** The raw content IS the output, just polished. Punchline quotes should be real speaker quotes, not AI-generated summaries.

3. **First-person perspective.** It's the user's living memory, not a third-party report. Takeaways should read like their own reflection.

4. **Dialogue format.** When multiple speakers are involved, show the back-and-forth as separate speech bubbles. One thought per bubble.

5. **Attention is the most valuable thing.** People remember a few highlights, not everything. Mark the pivoting moments, spotlight the punchlines, let the rest be expandable.

6. **Progressive disclosure.** Punchline always visible, full transcript behind "Read original." Don't overwhelm.

7. **Ship, then iterate.** v1 dark dashboard → feedback → v2-v5 in the same session. Don't over-spec before validating with the actual user.
