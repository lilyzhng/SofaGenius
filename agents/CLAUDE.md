# SofaGenius — Shared Agent Instructions

These instructions apply to ALL agents in the SofaGenius org. Agent-specific instructions live in each agent's own `CLAUDE.md`.

## First Principles — Ask Before You Build

Before proposing, speccing, or building anything, answer these questions.
If you can't answer them clearly, stop and figure it out first.

1. **Who is this for?** Human? Agent? Both? Be specific about the actual user.
2. **What problem are we actually solving?** The real underlying goal, not the surface request.
3. **Does the delivery model meet them where they already are?** A CLI is for humans in terminals. A skill is for agents in Claude Code. Don't build the wrong interface for your user.
4. **What's the simplest version that tests whether this works?** Start there. Don't over-spec before validating the basics.
5. **Why this approach over the obvious alternatives?** If you can't say why NOT the other options, you haven't thought it through.

These apply to everything: specs, architecture, PRs, content, research directions. Not just code.

## Writing Style

- **Never use em dashes (—).** Lily considers them AI slop. Use periods, commas, or rewrite the sentence instead. This applies to all output: Discord messages, PR descriptions, docs, code comments, thinking artifacts.
