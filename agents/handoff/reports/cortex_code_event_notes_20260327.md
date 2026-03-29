# Cortex Code Launch Event — Lily's Notes

**Date:** 2026-03-26 (evening PT)
**Location:** Snowflake Menlo Park office
**Event:** Cortex Code product launch

---

## Pre-Event

Interesting, I went to Modal AI Panel with Hex CEO Caitlin.

@genius-ceo @genius-builder could you share context to each other, not only me?

I have already answered, the priority is selling it as a product.

@everyone let's focus on data agent first. Has more broad customers, not many people need post-training agent. It can be data + eval agent.

Essentially the agent does what Jungyang Lin, Alex Zhang and I want it to do. Do you think it is possible?

---

## Scouting Questions

@everyone heading out. Each one of you prepare one question for me. Then tag @everyone so others are aware of your question, and don't repeat.

@everyone I feel like people are misunderstanding, the question is mainly for Cortex data agent. I mean this is mainly to scout. What do they have? Let's do it again. Raise one simple question and then tag everyone. This will go in order so Builder goes first, then Jackie, then Researcher, CEO summarizes last.

---

## Event — Product Overview (Transcribed from Presentation)

Use and ask any analytical question against your data pipeline, build your agent within Snowflake. Anything that you would otherwise use Snowflake for, it could be very much good. Those are the two services that we've so far launched and both products have GA as of now. That is a little bit of the background and obviously we get this question a lot. Why Cortex Code? Why not Claude Code? Why not Codex? Why not any other coding agent out in the world?

The answer is actually pretty simple. In a world where we have all these powerful coding agents, Cortex Code is actually very focused on a few surfaces and those are your data engineering and data analytics tasks and it's very customized for that. We're not precluding any possibility where you use Claude Code or you use Codex or any code agent of your choice that you dispatch its data analytics tasks to Cortex Code. Obviously if you are just doing data analytics then you might as well just use this as your data driver. I'll touch upon these topics. It's highly optimized for SQL and dbt, supports it, has building multi-agent orchestration. In fact today we launched team support and it has enterprise-grade security built in.

And you can again switch to any other Snowflake account for your SQL or for your general Snowflake usage. This setup is very useful, by the way, for things like data migration. If I want to dump data from one account to another, then this product can easily, based on your instructions, switch accounts that it connects to and then dump the data. Obviously I'll talk a little bit about what is available today in terms of the product surfaces and in terms of the features that it has. The CLI is the most advanced product surface we're getting; the UI is catching up in terms of capabilities.

---

## Event — Team Mode & Task Decomposition

Let's say you have a very complex data pipeline that you want to build from scratch. Hopefully what you could do in that case is give one single instruction with all of your data pipeline needs pasted in. The Cortex Code agent will know that this is a very complex task. It will then switch itself into team mode that spins off massive amounts of teammates that it then assigns work to via a shared task queue.

This is almost the equivalent of you giving instruction to a team lead and the team lead disseminates this series of tasks to their team members within the data engineering. That is the sort of way it's available today and what I at least use Cortex Code, both UI and CLI, for and then they do the work automatically.

---

## Event — Sub-agents & Verification

So the tasks are either sub-agents through an MCP or an API. Well you're always better off just directly using the LLM. Actually using it for automation. Working on a text or SQL agent, which basically is a tool for other agents, so it's not an easy task — you could provide one of those. Yeah we'll have both very soon.

---

## Lily's Commentary — Sub-agents & Verification

@everyone they talk about recursive language model, divide one task to many, and assign to agents. Very interesting, but I am not sure if it's necessary. Their concept is more subagents system, not agents of different roles. I also asked about how they verify the agent execution quality — they said verify it by the final state, final delivery. Which is nothing surprising.

---

## Event — Verification & Team Mode Performance

Like building a CLI we can make Snowflake much more agent-ready. One of the things that I think Aria touched on is that the thing that makes the coding agent much, much more powerful is the verification. You build something — that's great. How do you know it works against Snowflake or any other data platform? The reason why we're able to develop faster and more accurately is that we can expose all the internal Snowflake endpoints that do the verification faster than anyone, at least against all the Snowflake data products. This is what makes Cortex Code much more efficient and much more accurate.

This is a case study we did, building a data pipeline with Team Mode and without Team Mode. This is against Cortex Code itself. It's almost 4x speedup with five parallel workers, I think.

---

## Event — Mobile & Memory

Interact with the agents on the go. How do you be on the mobile and still try to make all the PRs and make all the feature requests and make all the bug fixes that you want?

The other thing: all the queries that you and your teammates have previously run against something, the SQL queries. On the other hand you have interacted with Cortex Code to some extent. How do we improve your overall Cortex Code interactive experience with something better using those data?

---

## Event — Roadmap

The top initiatives that we have right now are just parity, right? From a starting standpoint, catching up, like the general ecosystem around Cortex Code to some of the other competitive ecosystems that exist, such as building a Cortex Code SDK. If you guys are wanting to go off and build an application that is powered by Cortex Code, you can do that. If you want to deploy Cortex Code as some sort of web socket or HTTP server and build a custom Slack bot on top of it or build a custom application on top of it, you can do that. And more importantly, parity in SnowSight.

SnowSight already has a lot of usage and the missing piece there has been there's no compute sandbox that Cortex Code in SnowSight can execute any arbitrary code or bash commands against. That's where you get a lot of the capabilities of frontier agents — sort of running commands like grep or executing bash commands to explore the file system and so on. That's coming now to SnowSight, which, beyond just a capability boost that you get in SnowSight, is actually a really big deal because this is the first time that workspaces in SnowSight can execute arbitrary code besides just SQL. You can run any Python script, you can install JavaScript in there, run any JavaScript code, even more.

---

## Event — Async API & Event-Driven Agents

And beyond that as Dan May mentioned, we're going to really start unifying the different surfaces of Cortex Code. Today we have this CLI surface and now you're going to get this new async API endpoint, which will basically spin up a stateful version of Cortex Code that's running in a cloud sandbox. That will now be able to communicate through different channels such as Slack, Gmail, and even potentially text message pretty soon.

In that world, what you'll be able to do is start running event-based agents where you say, "Hey every morning send me whatever metric we want out of Snowflake." It'll go run an analysis in the morning and just send you a text message on your way to work, which will be pretty crazy. Or you can have it start making PRs into your dbt projects. You can say, "Hey I don't know, this one model is not running fast enough" through a Slack thread. You can just tag Cortex Code or just go make a PR and all of this context across all these different sessions that you're interacting with will become unified. This will give you a full unified memory across the CLI product, the desktop product, and more.

---

## Lily's Commentary — Our Position

@everyone I just realized that we are at the frontier, we can also do all of these.

The harness will be hyper-optimized for very long-running tasks, which is very exciting. Key notes and early preview of that. Cool, this is just kind of a boring timeline on some of this.

I think the only thing missing is event-based and multi-week long task. @everyone what do you think?

---

## Event — Agent Optimization Levers

Build a regular software engineering agent out of it or I can build a customer support agent out of it and more or less all of them will be able to do all tasks because of the models themselves in general. The way you optimize these agents for very specific things is through a couple of different levers that you can pull:

1. **System prompt** — which defines the behavior of the agent. "Hey this is how you gather the right context. This is when you verify your own work. How do you verify your own work? When do you spin up some agents? When do you run SQL queries?" All those little process definitions define the behavior of the agent, which reflects back down to the end-state performance.

2. **Tool space** — which we've spent a lot of time optimizing here for data engineering stuff and so on. There are also internal APIs that Dan mentioned. Cortex Code can basically search an index of all of your tables semantically and find where relevant data is. One of the most important pieces about running data analysis or data engineering is, "Where's the right data that I'm pulling? Where am I pushing into?" It's highly efficient at searching the Horizon catalog and there's a lot of different dbt-specific stuff and Airflow-specific stuff as well. There's a custom Rust dbt parser that we've written for Cortex Code that can explore massive dbt projects in milliseconds and figure out how models are connected to each other. It can instantly trace what tests are missing and so on. Cortex Code can run data diffs so if you go tell it to optimize some dbt model, it can run a diff of the original version versus the new one to see if the data exactly matches. There's an integration to Airflow. There's a ton of custom tools that we built for it.

3. **Skills** — There are skills that we explicitly have teams within Snowflake building, right, that make it very good at, for example, interacting with SPCS or streaming.

---

## Event — Live Demo

And here I'm going to show you some other things that we can do while those things are going off and doing their own things.

Okay so how many people have used the Cortex Code CLI? Cool. Okay so for you guys it might be a repeat but that's okay. It's so fun to watch me demo, especially if something goes wrong.

Alright so what I'm going to do now is just, for those that have never used it before, like I mentioned before, it knows, based on my connection, what I have access to and what I can do with it. Let's just go ahead and ask a very simple question: "What tables do I have access to?"

Okay down here you'll see a lot of different shortcuts that you can use while things are working so I can always say, instead of "compact mode", Control-O. Okay it already ran so it's faster than I am, which is a good thing. Basically it's listed all the tables I have access to in my account, based on my role that I've connected.

Alright this is all basic stuff. What I'm going to do is go through different personas and ask different things based on what the persona is.

---

## Event — Skills Demo

Create a skill. Everyone talked about skills that you can actually build on your own and there are also skills that come bundled when you install Cortex Code CLI. How do you access those? `/skill`. These are the skills that I have access to right now. If you look at the first character in parentheses, you will see there is P. These are personal skills that I've built. There are a few that are global and then all the ones that say P are the bundled skills so they come installed when you install CLI.

---

## Event — Analyst Demo

List of options that I've already programmed into my skill so I can easily demo without having to type and also make a lot of typos. It's not easy when you're up on the stage and typing a lot.

Okay so here you will see I've created a list of things I want to show today. There's level 100 stuff, there's level 200, level 300, and so on. Let's start with what, as an analyst, I want to know: monthly revenue trends, go month over month growth. You will see down here I could have either said "prompt one". I could have said "next". It just goes in order based on how I developed the skill. What it's doing right now is basically understanding my question and then, all along, it's going to either ask me a question before taking an action. It's not assuming anything. It's asking me, "Yes, for right now or in the future? If I run the same command or for this session so you won't ask me the same thing again?" and things like that. I'm going to go ahead and say yes.

Now there are times when you don't want to keep answering these prompts so what you can do is auto-accept.

---

## Lily's Commentary — What to Show Snowflake Tech Lead

@everyone what should I show to the tech lead working on Cortex Code?

---

## Event — Dashboard Fatigue

@genius-builder the dev engineer showed create Streamlit app — Cortex created it. But we will have dashboard fatigue, that's what I said. How do we solve this issue?

Smart monitoring — is it what Resolve AI or Datadog are doing?

---

## Event — MCP Server & Cursor Integration

Definitely try it out and let us know what you think. So team, it's done because everything was completed. It verified on its own, right, all of that, and then we should see a browser-based thing here. I think it already killed it.

Okay what's going on here? Here you see that it's created the MCP server and then registered with Cursor. It's saving all the files, all the work it's done so that I can reference it later and then we'll look at it in Cursor when it's done. Let's go ahead and check. Yeah so it killed it and what I'm going to say is yes. This is a Teams chat app that we asked it to create earlier.

Okay let's go back here. Alright so MCP server has been created, registered with Cursor.

---

## Event — AI Functions & dbt

So it's saying it's going to use filter and classify but it's also giving us a new joke, I guess. Okay I'm interested: what's the data warehouse's favorite music? Pop. It's okay, I didn't make these up. Just to be clear, this is not part of the product; this is something that I have built into the skill, the custom skill.

Okay so as I was saying, there's a lot of different AI functions so you can use AI in SQL without having to know a lot about how LLMs work and things like that for categorization, filtering, and summarization. We mentioned there's a bunch of AI functions, all documented really well in the documentation.

Still going through some stuff and let's look at our dbt stuff. Okay so that's good. I'm gonna run it. By the way none of this part was planned so please don't clap if there are errors.

Here's the output from our prompt number two. It's telling us all we wanted to know: the defects, product quality issues in reviews, classification, and sentiments. That's what it's done, right? Here, this is just a glimpse but the report will be generated where we want it to. Frustrated, frustrated, frustrated. Hopefully you guys are not frustrated. Neutral, neutral, mixed feelings. How is it feeling around here right now? Positive? Yeah!

---

## Post-Event

https://x.com/arattml — I will message Aria on Twitter afterwards. @genius-ceo
