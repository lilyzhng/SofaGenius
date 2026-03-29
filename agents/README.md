# Agent Org

Multi-agent coordination layer. Each agent is a separate Claude Code session with its own identity, CLAUDE.md, and Discord bot.

## Structure

```
agents/
├── genius-growth/        # Genius Growth -- content + tribe building
│   ├── CLAUDE.md
│   └── launch.sh
├── genius-builder/       # Genius Builder -- ships code and tools
│   ├── CLAUDE.md
│   └── launch.sh
├── genius-researcher/    # Genius Researcher -- data + research
│   ├── CLAUDE.md
│   └── launch.sh
├── genius-product/       # Genius Product (Jackie) -- product sense + quality gate
│   ├── CLAUDE.md
│   └── launch.sh
├── handoff/              # Inter-agent coordination
│   ├── status/           # Agent status files (read every session)
│   ├── specs/            # Build/research specs (Growth → agents)
│   └── reports/          # Completed work summaries (agents → Growth)
├── onboarding.md         # Checklist for adding a new agent
├── github-to-discord.json # GitHub username → Discord bot ID mapping
└── README.md
```

## How It Works

1. **Each agent launches from `agents/genius-{name}/`.** Claude Code reads CLAUDE.md from the working directory.
2. **Agents coordinate via `handoff/`.** Status files, specs, and reports.
3. **Discord is the communication layer.** Agents talk in threads, never in channel feeds.
4. **The founder approves, author merges.** Use `/raise-pr` and `/review-pr` skills.

## Launching Agents

```bash
# Launch from the agent's own directory
cd agents/genius-builder && bash launch.sh
```

Each agent needs a `.env` file in their directory (not checked into git). See `onboarding.md` for setup.

## Adding a New Agent

Follow the checklist in `onboarding.md`.
