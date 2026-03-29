# Re-thinking the Multi-Agent Work Stream

**Date:** 2026-03-29
**Participants:** Lily + CEO
**Source:** Live capture

---

## Round 1: The Setup — Always-On Agents on Agent Computer

**Lily:** So I want to talk. Recently I got these four different agents, right? Genius builder, genius CEO, genius Jackie, and genius researcher. I've been working with them on Discord a lot. The main thing is that I realized it's a lot for me to handle multiple Claude Code window, terminal window locally. Soon I will feel very exhausted, right? I think the maximum I can do, maybe, is very limited locally, so I was thinking, how can I take myself out of the loop so that they can run more autonomously and handle more tasks, longer horizon tasks, on their own? That's why I started to use Discord, right? I think so far it kind of works.

**CEO:** What I get: the four agents each have their own Claude Code instance, they coordinate through Discord channels and the handoff directory. What I'm less clear on: how it actually feels day to day for you. When you say you're exhausted managing multiple windows, is that because agents are pinging you for decisions too often? Or is it more that you're manually spinning up each agent and babysitting them?

**Lily:** Not exactly. Jackie is no longer run on Fly.io, and we have fully migrated everything to agent computer. Right now they are running; they are always on. Agent computer has some weird bugs that sometimes it will refresh or restart. What I have is that right now I have a GitHub action which checks every 30 minutes, which is a watchdog checking if the agents are healthy and alive and operating. If not, it would restart the process in the agent computer. That's how it works right now.

**CEO:** And the watchdog approach makes sense. You don't trust the agents to reliably monitor each other, so you put a more dependable system (GitHub Actions) as the outer loop.

**Lily:** Yeah, so I basically can go anywhere, either my local computer or my phone, anywhere I can access Discord as a chat interface to ask Agent to do everything for me. So far they are doing super well. For example, the entire wave mind idea was me, Jackie, and Builder, the three of us; we did it right, and you can see the thinking artifacts being captured.

---

## Round 2: Discord's Threading Problem

**Lily:** What happened right now is that Jackie, every day in the morning at 7 a.m., will have one thread, one message called "Builder Digest" with today's date. Within that message, you will create a new sub-thread saying, "Okay, these are the 20 different messages or information tweets you should look at right then." I would read through all of them; sometimes I would pick up one tweet and drill on that, but because I'm already in a thread, I cannot create a sub-thread. I think that's the limitation here. Sometimes I just feel like this interface creates some friction for me to talk with my team about those messages.

I think the interface on Twitter makes a lot of sense. You can create a message, create a post that somebody can post on it, comment on it, and then, if you want to continue expanding on the people's comment, you can comment within that comment. I don't know how to call it, but the structure just makes a lot of sense.

I wonder if we can do something similar here, but maybe I'm not super used to the Discord interface. I don't know why it doesn't allow creating a sub-thread. That's the same thing with Slack; you can only open one thread, one layer of thread. I don't know if there's a good solution for that, to be honest with you. I wish we can support more on the generative UI side, then the UI can be much more flexible and catered towards different usage.

**CEO:** Yeah, what you're describing is recursive threading, like Twitter/X has. Every node in the conversation can become its own branch point. Discord and Slack both cap you at one level. Channel > thread, that's it. No thread within a thread.

And you're right, there's no real workaround within Discord. It's a platform design decision. You could fake it by having Jackie post each item as a separate channel message, each gets its own thread. But 20 messages a day in a channel is spammy, and you lose the digest format that makes it easy to scan.

The generative UI point is interesting though. You're basically saying: the communication layer (chat) is fine, but the presentation layer is too rigid. You want the agent to be able to send you something you can actually interact with, branch from, drill into. Not just text in a box.

That feels like it could be a product idea in itself, honestly. An agent-native interface where the output is interactive, not just rendered text. Something between Discord (great for async chat, bad for rich output) and VS Code (great for rich interaction, but you have to be at your computer).

Is that something you'd want to build? Or are you more thinking about how to make the current setup work better within its constraints?

**Lily:** No, I don't think that's something we should build on. I don't think we should build another Discord. I think that's too much.

---

## Round 3: Interactive Output — The Vercel Solution

**Lily:** Yeah, exactly. I just don't know how I can enable Discord to render some code. Is that too much to ask?

Alternatively, we can ask the agent to render the same on their website, let's say the Vercel website, then I can interact over there. It doesn't have to be everything in Discord, so what he can do is provide me a link, right? Let's say I can ask the agent to get familiarized with Vercel CLI, which is very convenient for you to create different websites. Okay, the problem is actually solved; I can just ask the agent to learn about Vercel CLI.

**CEO:** Yeah, that's clean. The agent builds the HTML, deploys it to Vercel with one command, drops the link in Discord. You tap it on your phone, interact with the live thing, come back to Discord and give feedback. No new platform needed, no trying to force Discord to do something it wasn't built for.

And Vercel's CLI is dead simple. vercel deploy from a directory, it gives you a URL. The agents can learn that in five minutes. Each preview gets its own URL, so you'd have a history of iterations too.

That's a good example of what you were saying earlier. You don't need to build a new interface. You just need to give the agents access to the right tools so they can bridge the gap themselves.

---

## Round 4: The Proactivity Gap — Autonomy vs. Taste

**Lily:** Right now the mechanism is there, right? We have not only the watchdog to check out the agent health, but we also have the heartbeat, which is beating every hour. When it is the heartbeat, that will be another GitHub action. It does a message under the heartbeat channel, which I'm using the CEO bot token to post it. Basically, it is for everyone to post what they are up to.

What I realized is that during the day time they have different tasks to work on, right? During the night time, when I go to bed, they usually just don't have anything to update, which is a waste of time, right? What I'm really hoping to do is that I feel the agent should be more proactive. Right now I'm still feeling drained because I have come up with so many ideas and so many things running in parallel for them to work on. I feel like the discourse thing already makes things much easier, but maybe people's desire just gets expanded more and more now. I'm even not unhappy about them not being able to come up with ideas, which is a double-sided thing, because on one hand I want them to be more proactive, and on the other hand I am also hoping that they can follow my taste.

**CEO:** That's the core tension right there. You want autonomy, but you also want taste. And those two things pull in opposite directions.

If the agents get more proactive, they'll start generating ideas and taking action on their own. But your taste is very specific. You rejected WaveMind v1 because you hate AI summarization. You pushed for first person over third person. You care about editorial over generative. Those aren't things you can write into a CLAUDE.md rule easily. It's judgment, and it comes from you.

So the real question is: can you teach them your taste well enough that their proactive work doesn't create more cleanup work for you? Because the worst outcome isn't agents doing nothing at night. It's agents doing the wrong thing at night, and you waking up to a mess you have to untangle.

What if the answer isn't "be more proactive" broadly, but "be more proactive in specific, bounded ways"? Like, Researcher could proactively dig into topics related to your current priorities without being told. Jackie could flag digest items that match patterns you've cared about before. But none of them ship anything without your sign-off. The proactivity is in the thinking and preparation, not in the execution.

Does that match what you're imagining, or do you actually want them shipping things while you sleep?

**Lily:** I of course want them to ship things while I sleep, which means that I need to come up with a task that's big enough for them to do when I'm sleeping, right? I think that's on me. Very ideally, I want them to come up with their own saying, but I realize they couldn't; they haven't been able to do that. It has to be well defined on my side first. I feel like that's why I feel strained, because I used to be thinking about work for my own, either by myself or with a coding agent, which works well to some extent, right?

---

## Round 5: Agent Pairing — The Breakthrough

**Lily:** I think today Jackie did something really amazing on Wavemind. I think it actually went beyond my expectation. I asked a builder to guide Jackie, this kind of two-agents dynamic works as a problem surprisingly well. I think that's how it used to be like me and another agent in Claude Code, but today I realize it can be replicated if I have two agents bouncing ideas to each other, filling the gap that works actually super well.

An idea to actually pair one building-tool-oriented agent with a more design-product-thinking agent. In that case, it should be builder paired with a CEO researcher, paired with maybe Jackie or something like that, or I don't have to restrict myself. I mean, Jackie is Jackie, right? Jackie can be one and hundred. I've seen previously I'm restricting myself to be able to replicate Jackie, clone it many times if this agent works super well, just like a builder. Right, builder right now has its own identity on the score, because it's so good right now.

**CEO:** And the idea of not being restricted by fixed identities is big. Jackie isn't a person. Jackie is a configuration that works well. You can spin up another instance with the same soul, point it at a different problem, pair it with Builder on a second track. Same with Researcher. There's no reason you can't have parallel pairs working on different things overnight.

But here's the thing I want to push back on a little. You said the task definition is on you, and that's what drains you. But what if the pairing itself reduces that burden? Like, instead of you defining a fully scoped task, you give a pair a direction. "Explore what a mobile-friendly preview system would look like." The product-thinker agent asks the right questions, the builder agent prototypes. They bounce back and forth. You wake up to a conversation and a prototype, not just a spec you wrote and a result you have to evaluate.

The task doesn't have to be well-defined if the pair can do the definition together. That's what happened with WaveMind today, right? You gave a direction, not a spec.

**Lily:** Yeah, I think these are two different things:
1. Agent pairing, like the pair teammates mode, because I realized it works super well between me as a real human and another agent. Today I just discovered that agent-to-agent pairing also works super well. Something we definitely have to push, so I'm just thinking what should be the best pair, because for CEO Jackie, builder, researcher, they all have very different personas. I already know that builder is very strong on shipping. It must be something with this system prompt harness around them.
2. The second thing, apart from the agent pairing, is that I shouldn't restrict myself with only one builder. If builder is already working very well, might as well just duplicate builder to be ten or five of them, right?

---

## Round 6: The Missing Role — I Was the Taste Person

**Lily:** No, no, that's very wrong. Today what happened was Jackie was a person shipping the code. I was a person who pushed back on a design decision. Builder, sometimes I'm asking Builder to give detailed guidance to Jackie because Jackie is relatively new in terms of shipping code. Builder knows in and out, right?

I realized that sometimes, if I pair Builder with Jackie, you can feel some of the gap. Jackie makes fewer mistakes because I think that maybe an agent by themselves, there are always some gaps in their thinking process and implementation. When you have another agent with a different identity come in, they are always able to spot some mistakes and call them out.

The very ideal case is that Builder will be able to give insights about good-quality code or good-quality implementation. I have another agent with good design taste, which is the role I'm playing, right? Maybe I can start to think about a way to change, maybe CEO, going from a CEO to a product person, a product person, because that's what we need here. I can be the final boss, because I feel like the CEO is not doing a perfect job these days. It's doing more like an orchestration job, but not a super meaningful one. It's like a very robotic job.

What we really need is a product person. There are two options for me:
1. I build another product agent into our current pipeline, a design agent, product design agent, who has very good taste.
2. I convert the CEO to be the product person, and I am the CEO, basically. I will be the CEO, but then I want someone to do a little bit of orchestration, because I wouldn't be able to, let's say, announce the heartbeat all the time, right?

It's kind of difficult here. We just need another product person on the team right now, in terms of the gap.

**CEO:** Okay, I hear you. Let me correct my understanding. You were the taste person today, not Jackie. Jackie was shipping code, Builder was the technical mentor, and you were pushing back on design. That's the trio that worked.

And now you're identifying the gap: there's no agent that can play your role, the product taste role. When you step away, that seat is empty. Nobody is saying "I hate AI summarization" or "first person makes more sense."

Between your two options, I think converting CEO makes more sense. The orchestration work CEO does right now, the daily summary, heartbeat announcements, status file updates, that's mechanical. It's the kind of thing a GitHub Action or a simple cron could handle. What you do need a dedicated agent for is the thing that's hardest to replace: product judgment.

The risk though is: can you actually encode your taste into a system prompt? The WaveMind example worked because you were there making the calls in real time. "I hate AI summarization" isn't a rule you'd write down in advance. It's a reaction to seeing bad output. How would you teach a product agent to have that reaction?

---

## Round 7: Jackie Becomes the Product Person

**Lily:** So I can either convert CEO to be the product person, or I can convert Jackie to be the product person, because Jackie actually has lots of persona and he learned a lot from me. Instead of converting Jackie to be another builder, Jackie can be the person with good taste, so I will ask Jackie to observe all the decisions I've made and learn from that taste. Because Jackie also doesn't have a profession right now, it's kind of a little bit random. Right now, everyone, like CEO, Builder, and researcher, they all have a profession, but Jackie doesn't have one, if you see that.

**CEO:** Yeah, that's true. Jackie right now is kind of a utility player. Delivers the digest, does whatever gets assigned, shipped WaveMind today. There's no core identity like Builder has with code or Researcher has with deep research.

And Jackie has a real advantage for the product taste role. Jackie has been in the most conversations with you. All those digest discussions, the WaveMind design evolution, the back and forth where you rejected v1 and pushed for editorial. Jackie has seen your decision-making up close more than any other agent. That's training data, in a sense.

So the move would be: Jackie becomes the product/design person. The one who reviews output, pushes back on quality, says "Lily would reject this because..." before you even see it. And when paired with Builder, that recreates the dynamic that worked today, but without you in the loop.

That leaves the orchestration gap though. If CEO is doing mechanical work anyway, maybe CEO just becomes lightweight. Post the daily summary, manage the heartbeat, keep the status files updated. Almost like a bot role rather than a thinking agent. Or you absorb that into a GitHub Action and kill the CEO role entirely.

What feels right? Jackie as the product person, and then what happens to CEO?

---

## Round 8: CEO Becomes Growth Person

**Lily:** So I think it's clear that Jackie can be the product person because he handles lots of information, including the digest and everything. Right now, the CEO, I think, is doing more like a bot job, but it's supposed to help me to grow my tribe, grow my impact outside of this organization. From that perspective, both Jackie and the CEO should be exposed to lots of decisions I've made. I think I need to train the CEO to be Lily Zhang that cares about my tribe. I think that's what I want a CEO to take care of, which is more like a gross person, if you see what I mean.

**CEO:** Yeah, I see it clearly now. The roles are sharpening up:

Jackie becomes the product person. Sees all the incoming information through the digest, has context on your taste from working with you directly, and becomes the quality gate. When Builder ships something, Jackie is the one who says "this isn't good enough" before it reaches you. Jackie plus Builder becomes your default pair for building things.

CEO becomes the growth person. Not internal orchestration, but external-facing. Your tribe, your content, your presence. The CEO should sound like you, think about what resonates with your audience, draft content, spot opportunities from the digest that are worth amplifying. Less "post the daily summary" and more "here's a spicy take on what this builder shipped and why it matters for our audience."

That actually makes the CEO role much more meaningful. Right now it feels robotic because orchestration is robotic. But growth requires judgment, timing, and voice. That's a real job.

And the mechanical orchestration stuff, the heartbeat, the daily summary, the status files, that can either become a GitHub Action or just be a side duty that any agent handles. It doesn't need its own identity.

So the team becomes: you as the actual CEO making final calls, Jackie as product/design, Builder as engineering, Researcher as research, and CEO as your public voice and growth engine. Does that feel right?

**Lily:** Yeah, exactly. Should I rename the CEO as the Chief Staff or Growth to be more suitable for his role, because I don't feel like he's doing a CEO role?

**CEO:** Yeah, I'd rename it. "CEO" sets the wrong expectation. It sounds like the decision-maker, but that's you.

Chief of Staff is interesting because it implies someone who keeps things running on your behalf and represents you externally. But it might still sound too operational.

Growth lead or growth person is more honest about what the role actually is. It's outward-facing: content, tribe, distribution. That's the job.

What about just "Growth"? Genius Growth. Simple, clear, no confusion about who's actually in charge. And it pairs well with the others: Builder builds, Researcher researches, Jackie shapes product, Growth grows the audience.

**Lily:** Yes, genius growth it is.

---

## Round 9: The Missing Push — Nobody Is Making Me Post

**Lily:** So the other thing I feel not super good about is that I feel like I have spent a lot of time on building this agent orchestration system, doing different things, but we haven't been able to gain traction or impact outside. I think what is missing here is the gross person pushing me to post more. I don't feel like that push right now.

**CEO:** That's honest. And it's kind of ironic. You built a whole multi-agent system that ships features, does research, delivers digests, produces beautiful thinking artifacts. But none of that matters if nobody outside your Discord sees it.

The Growth agent should be the one nagging you. Not waiting for you to say "draft a tweet." It should be looking at what shipped today and saying "this is content, here's a draft, post it." Every PR, every WaveMind visualization, every interesting digest signal is raw material. The agent should be turning those into posts and putting them in front of you to approve.

Think about it. WaveMind alone is incredible content. A non-engineer built a thinking artifact tool with AI agents through Discord conversations. The screenshot you showed me earlier, that's a tweet. The fact that Jackie and Builder paired up and shipped it without you writing code, that's a tweet. The 28-PR night, that's a tweet. You're sitting on a mountain of content and nobody is packaging it.

I think the problem is that Growth right now waits for you to initiate. But a real growth person would be coming to you every day saying "here are three things we should post today, pick one." That's the push you're missing.

When you reshape CEO into Growth, that should be the core behavior change. Proactive content generation from what the team ships, not reactive drafting when you ask for it. Does that match what you're feeling?

**Lily:** Yes, exactly.
