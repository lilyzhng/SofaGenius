# WaveMind
**WaveMind** is a Claude Code skill that captures your thoughts, it records the raw back-and-forth as it happens, then turns it into a beautiful thinking artifacts you can revisit weeks later.

<img src="examples/teaser.png" width="800">

## Key Features
You have hundreds of ideas a day, but the human context window is limited. By the time you sit down to build, you've lost the thread between the original spark and the final decision. WaveMind preserves that thread.

**Thinking Partner** (`CLAUDE.md`)
- It acts as a thinking partner that asks good questions, pushes back when something doesn't add up, and creates productive friction instead of just agreeing. The best thinking requires disturbance. If you're only hearing "yes, great idea," something's wrong.

**Capture** (`/wavemind capture`)
- Records your conversation as it happens, round by round
- No summarization. Raw words, preserved exactly as spoken
- Say "done" or "save" when you're finished

**Visualize** (`/wavemind visualize`)
- Turns the raw artifact into a self-contained HTML document
- Editorial layout: cream background, serif headers, gold accents
- Progressive disclosure: punchline quotes visible, full transcript behind toggle
- Mobile responsive

## Installation

```bash
cp -r wavemind/ ~/.claude/skills/
```

## Usage
For most frictionless capture, I pair wavemind with voice input (I use [Wispr Flow](https://wisprflow.ai/) or [/voice](https://code.claude.com/docs/en/voice-dictation)).

```
/wavemind capture "Topic Name"    # Start recording a conversation
/wavemind capture path/to/file    # Import an existing file
/wavemind visualize thinking.md    # Generate the visual html from md
/wavemind list                    # Browse all stored artifacts
```

## Output Examples

See `data/` for a seeded input/output pair:

| File | Description |
|------|-------------|
| `data/artifacts/glm-benchmark.md` | Raw captured artifact (10 rounds, ~4500 words) |
| `data/visuals/glm-benchmark.html` | Visualized output generated from that artifact |
| `examples/wavemind-design-evolution.png` | Design evolution capture |

## Structure

```
wavemind/
├── SKILL.md          # Skill definition and instructions
├── lib/
│   ├── capture.sh    # Capture and indexing scripts
│   ├── store.sh      # Storage management
│   └── visualize.sh  # Visualization pipeline
├── examples/         # Screenshots and design references
└── data/             # Runtime data + seeded examples
    ├── .gitignore    # Ignores runtime data, keeps seeded examples
    ├── index.json    # Artifact registry (created at runtime)
    ├── artifacts/    # Raw markdown files
    └── visuals/      # Generated HTML files
```

## Design Principles
- **Raw, not summarized.** Fix typos, but don't rephrase. The original words matter.
- **Editorial, not generative.** Extract what was actually said. Don't generate insights.
- **First person.** It's your living memory, not a third-party report.
- **Progressive disclosure.** Punchline visible, full transcript on demand.

## License

[MIT](LICENSE)