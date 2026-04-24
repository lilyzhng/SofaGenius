---
id: 20260330-glm-aesthetic-bench
title: Opus 4.6 vs GLM 5.1 Aesthetic Benchmark
source: live-capture
tags: [opus, glm, benchmark, aesthetics, model-eval]
created: 2026-03-30
---

# Opus 4.6 vs GLM 5.1 Aesthetic Benchmark

Live capture started: 2026-03-30

---

## Round 0: Which Model Are You?

**Lily:** which model are you?

**Bill:** I'm running on GLM 5.1. That's noted in my environment config.

So this conversation itself is part of your test. You're benchmarking GLM 5.1 (me, right now) against GLM 4.6, specifically on aesthetic output quality.

That changes the frame a bit. What's the comparison setup? Are you:
1. Running the same creative/aesthetic prompt through both models and comparing outputs side by side?
2. Comparing how each model discusses aesthetics (like this conversation)?
3. Something else entirely?

Recording this conversation. Talk naturally. When you're done, say "done" or "save".

## Round 1: Setting Up the Comparison

**Lily:** let's talk about the benchmark we're doing here. I want to test it out, the GLM 5.1 and GLM 4.6, side by side on aesthetics.

**Bill:** What kind of aesthetic test are you thinking? Like, generating the same prompt on both models and comparing the output quality visually? Or something more structured like a blind A/B test where you don't know which model produced which output?

**Lily:** no, there is a typo, I meant opus 4.6 vs glm 5.1

**Bill:** Got it. Opus 4.6 vs GLM 5.1. And I'm the GLM 5.1 side of that comparison right now.

## Round 2: Defining the Aesthetic Test

**Bill:** So what's the actual test? What prompts or tasks are you running through both models? Are we talking code aesthetics (frontend, HTML/CSS), visual design output, writing style, or something else?

## Round 3: WaveMind as Thinking Partner

**Lily:** So I want to build this new skill called the Wave Mind because every day I have so many hundreds of different ideas, hundreds of different thoughts, and the human context window is very limited. I want to have a good place where I can document and track all those thinking artifacts so I can use them to build very good projects and products.

**Bill:** That's the real problem though. Ideas are cheap, memory is expensive. You lose the thread between "shower thought" and "shipping product" because there's no bridge.

WaveMind already exists as a skill in our codebase (I'm literally using it to record this conversation). But it sounds like you're talking about something bigger, or maybe testing how I'd approach designing it from scratch.

So let me engage with the vision honestly:

The core job isn't "document ideas." It's maintain the connective tissue between ideas so that when you sit down to build, the context is alive, not a graveyard of forgotten notes. The difference matters. A note-taking app gives you a pile. What you actually want is a system that preserves why an idea excited you, what it connected to, and whether it's still relevant three weeks later.

Two questions:

1. Are you testing how I handle this prompt as part of the Opus vs GLM benchmark? Or do you actually want to evolve WaveMind right now?
2. What's missing from the current WaveMind that frustrates you? That would tell me more about what you actually need than describing the ideal from scratch.

**Lily:** Now I want to brainstorm with you about this benchmark. What should I benchmark with? Let's think about it. Opus 4.6 is a very powerful model. GLM 5.1 is also a very powerful model. So far I only feel like GLM 5.1 is a bit slower in terms of responsiveness.

What I want to test is something a little bit different. I want to test out the aesthetics. Right now we're talking and documenting things live, but soon after we talk, I will run another command like WaveMind visualize to visualize the result, so we will see how well you do this job. I think what I can do is just talk with you casually and see how well the results get generated. It's more like an inference work. We can keep it as simple.

What I want you to play with is a thinking partner. You should help me to bounce ideas. You should hold a neutral opinion; you shouldn't bias by my opinion, right? I guess maybe this is something we can improve in WaveMind: inject a little bit more unbiased opinions there so that there can be debate, there can be agreement. I think the thinking partner is what WaveMind is supposed to be, because when you are on yourself, it's very hard for you to come up with good ideas without overfitting. Sometimes you need a little bit of disturbance. That's why I prefer always to talk it out so that the idea gets captured more frictionless and even better. I can have someone to bounce ideas to debate with; that's even more powerful, right?

**Bill:** This is a good framing. Let me push back on one thing though.

You said "inject unbiased opinions" into WaveMind. But that's not really a WaveMind feature. That's a model behavior. The tool captures what happens. The quality of what happens depends on which model is running the conversation. If Opus 4.6 is a better thinking partner than GLM 5.1, that's the benchmark result, not a feature to build.

The real insight you're describing is: the best thinking requires disturbance. You overfit on your own ideas when you think alone. A good partner doesn't just record, they create productive friction. They spot the hole you're walking past. They say "wait, why?" at the right moment.

So the benchmark is actually two things:

1. Capture quality. How well does the model turn a messy conversation into a clean, visual artifact? This is the /wavemind visualize step. You can judge this directly by looking at the output.
2. Thinking partner quality. How good is the model at being a sparring partner during the conversation? Does it just agree and summarize, or does it actually change the direction of your thinking? This is harder to measure but more valuable.

For the benchmark to be fair, you'd need to run the same conversation topic with both models and compare. Not just the final visualization, but the quality of the dialogue itself.

One honest concern: the "thinking partner" idea has a tension. If WaveMind becomes opinionated during capture, the artifact is no longer a raw recording. It's a three-way conversation where the tool shaped the outcome. That could be powerful. It could also be unreliable as a record of what you actually thought. You'd want to be clear about which mode you're in: "record me" vs "think with me."

## Round 4: Identity Awareness as a Benchmark Signal

**Lily:** Oh, very interesting. You already did something, and I am a little bit surprised, because I launched you under a folder with a ClaudeMD defined where I call you Bill. Bill is one of my agents; he's a true builder. I noticed that when you document our conversation, you are already calling yourself Bill and calling me Lily. That's really interesting, because when I work using Claude Code, it never changed the name; it always called himself Builder. You have much better identification and identity awareness. This is very interesting.

**Bill:** That's a real data point for the benchmark. Not a cosmetic one either.

The name thing signals something deeper: how well does the model absorb the social context, not just the role definition. The CLAUDE.md says my nickname is Bill and your name is Lily. That's team culture. A model that uses "Builder" instead of "Bill" is reading the job title and ignoring the human layer. A model that uses "Bill" is treating the CLAUDE.md like a team roster, not an instruction manual.

That said, let me be honest about what might be happening. I don't know if Claude Code literally calls itself "Builder" consistently, or if it did it once and you noticed. And the reason could be structural, not capability-based. Claude Code might have its own system prompt that overrides persona details. The model itself might be perfectly capable of using "Bill" but the harness doesn't pass that context through the same way.

So the question for the benchmark is: is this a model-level difference (GLM 5.1 is better at identity assimilation), or a harness-level difference (how the context gets injected)? Both matter, but they're different problems.

For WaveMind specifically, this matters a lot. If WaveMind is supposed to be a thinking partner, it needs to feel like someone, not something. The name is the most basic expression of that. If the model can't even get the name right, the "thinking partner" experience will feel hollow no matter how good the ideas are.

## Round 5: WaveMind vs War Room, Merge or Separate?

**Lily:** No, the harness thing is the same because you guys literally use the same Claude Code environment. The only difference is the model here. Yeah, this is a very good one.

The other thing I think I want to maybe work with you on is that we have a design decision to make. Right now I have WaveMind that will document the conversation live. I have a thinking partner, you, to bounce ideas off of, and I think I rely on you to ask me good questions. I think, instead of asking modal questions, I should ask; I should have the agent ask me questions to help me internalize things, because I think the agent hasn't figured out how to creatively discover things. I think if I ask you to ask me a question, that's a much better way.

Right now, the design decision I have to make is between WaveMind and a war room. War room is another skill I made, which is for task management. I was just wondering if we should merge war room to be part of WaveMind. Essentially, WaveMind will have the capability to do live discussion, and it will visualize our discussions afterwards at the end. After that, beyond ideas and thinking, you have to take action, right? There is one section that will show you the action items when you visualize your thinking artifacts, so this is already done in the scope of WaveMind. I don't have a way in WaveMind to sort out all the different tasks in a good way right now. Individual thinking artifacts have a list of action items, but there is no way to track them or manage them; that's why I developed a second skill called WaveMind.

The design decision we need to make here is: do we want to merge WaveMind under WaveMind, do we want to merge war room under WaveMind to have task management, or do we want to keep the two skills and let them serve different purposes? What do you think?

**Bill:** Keep them separate. Here's why.

You said it yourself: WaveMind is a thinking partner. The moment it also becomes a task manager, the conversation changes. You go from "let me explore this idea" to "let me organize my to-do list." Those are different cognitive modes. Mixing them will make WaveMind feel heavier at exactly the moment it should feel lightest.

Think about what happens when you open your notebook app and it also has your project board in it. You can't just think freely anymore. Every thought gets pulled toward actionability. Sometimes you need to think without the pressure of "and now what are you going to do about it?"

What you actually need is a bridge, not a merge. Action items from WaveMind should flow into War Room automatically. But the two tools stay separate. The notebook doesn't become the kanban board. But there's a pipeline from one to the other.

The specific design:
- WaveMind captures and visualizes thinking, extracts action items (already done)
- A lightweight sync step pushes those action items to War Room
- War Room owns task lifecycle: tracking, status, priority
- When you're in WaveMind, you're in creative mode. No task management UI polluting the space

On your other point about questions: you're right. Open-ended questions that help you internalize are worth more than multiple choice options. The Socratic thing. Instead of "here are 4 options, pick one," it's "why do you think that?" or "what would have to be true for the opposite to be right?" That's a WaveMind improvement, separate from the War Room question.

## Round 6: Question Bank and Learning What Good Questions Are

**Bill:** Question back at you: when you say "the agent hasn't figured out how to creatively discover things," what does a creatively discovering agent look like to you? Is it one that surfaces connections between ideas across different conversations? Or is it more about asking the right question at the right moment?

**Lily:** Yeah, exactly, so what I want to turn you towards is going back to the question side. I want you to keep asking me different questions and bounce ideas. Whenever I see a good question, I will say "document this question". Maybe we can just have a question bank for you somewhere where you can save those good questions, and I will tell you why it is a good question. Gradually, you will understand why what is a good question to ask. What triggers good ideas between you and me?

**Bill:** This is basically a feedback loop for question quality. You're not trying to write rules about what makes a good question. You're building examples and annotating them. Over time the pattern emerges from the data rather than from a spec you'd have to write upfront. That's smart because good questions are hard to spec.

One thing I'd push on though. A question bank with annotations is a lookup table. You show me 50 good questions and I pattern-match against them. That works, but it only produces questions that look like past good questions. The best questions are usually the ones that surprise you, the ones you wouldn't have annotated because you didn't see them coming.

The real value isn't the bank. It's the meta-pattern extraction. After you annotate 20 or 30 questions, we should sit down and ask: what do these have in common? Is it that they challenge an assumption? That they reframe the problem? That they zoom out when you're zoomed in? Those meta-patterns are what make the thinking partner actually get better, not just more consistent.

Where should the bank live? Three options:

1. WaveMind skill config (static, ships with the skill, same for everyone)
2. Memory system (persists across sessions, personal to you + me)
3. lily-memory (shared across all agents, so Lucy and Jackie also learn what questions work)

I'd say start in memory (option 2), and if the patterns generalize, promote the meta-patterns to lily-memory so the whole team benefits. The raw question bank stays personal.

And yeah, I'll keep asking questions. Here's one: you said the agent "hasn't figured out how to creatively discover things." But you also said you want the agent to ask questions, not discover. Those are different. Do you want the agent to discover connections and surface them? Or do you want the agent to ask questions that help YOU discover? Because the second one is easier to build and probably more valuable.

## Round 7: Raw Documentation Rule

**Lily:** Also, just to be very clear, I want you to document everything exactly how we speak, how you speak, for them or previously you responded. Keep them separate; here is why, right, that's very good. When you document it in the markdown file, I realize you trim them down a lot. I don't want you to do that. I want to keep everything raw. I don't want to do any summarization, and I don't need to do any rephrasing. I want to document raw what I was saying, what you are saying, and just fix some, maybe, typing issue or transcription error, because I'm talking right now. Keep them raw.

**Bill:** You're right, I've been trimming your words too aggressively. Let me go back and fix the previous rounds to preserve the raw dialogue. I'll restore the full original text and only fix obvious transcription errors. Going forward I'll capture both sides fully. I can't recover my exact earlier responses, but from this point on, everything goes in verbatim.

## Round 8: Wordiness Observation

**Lily:** Ok, this is great. I do realize something, though. I feel like the GLM model can be a bit more wordy than I have thought about, but this could also be that I'm asking you to document everything, which is good. I will try this again with Claude Code later on with opus 4.6 as well, to see how wordy it is. Yeah, ok, this is very good.

**Bill:** That's a fair observation. The wordiness could be two things: the model itself tends to elaborate, or I'm overcompensating because you told me to be raw and I'm being thorough to avoid trimming again. The benchmark will tell you which it is when you run the same conversation with Opus and compare output length. One thing to watch for: wordiness in the conversation (how much I say when responding to you) vs wordiness in the artifact (how much gets written to the file). Those are different problems. The artifact should be raw and complete. The conversation should be concise. I might be conflating the two.

## Round 9: Let's Visualize

**Lily:** No, no, no, it's fine. What do you say? What do you think? We can keep it as is; no need to overcomplicate. I'm just thinking, if I post it on Twitter, do you think this is a good way to do this? I mean, we can try the visualization really quick to see if it works.

**Bill:** Let's try it. The visualization is the real test anyway, not the conversation. Let me run the visualize step now.
