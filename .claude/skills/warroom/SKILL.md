---
name: warroom
description: "Task management war room. Reads a markdown task file, renders a dark-mode mobile-first dashboard with lanes, ranked items, and progress stats."
argument-hint: <source_file> [output_path]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Warroom — Task Management Dashboard

You are running the Warroom skill. It reads a markdown task file and generates a beautiful dark-mode dashboard visualization.

## Usage

```
/warroom <source_file> [output_path]
```

- `source_file`: Path to a markdown file with tasks, organized by sections
- `output_path`: Optional. Where to save the HTML. Defaults to same directory as source, with `.html` extension.

## How It Works

1. **Read** the source markdown file
2. **Parse** it into structured data:
   - Sections become lanes (e.g., "This Week", "Leads", "Ongoing", "Done")
   - Checkboxes (`- [ ]` and `- [x]`) become task items with completion status
   - Any `##` heading becomes a lane/slide
   - Items can have tags in parentheses, e.g., `(hot)`, `(blocked)`, `(due: April 2)`
   - Numbered items get rank badges (top 3 get accent styling)
3. **Calculate** stats: total tasks, completed, completion rate, blocked count
4. **Generate** a self-contained HTML file using the War Room design system

## Design System

Use this exact design language (from the proven pipeline.html template):

### Visual Identity
- **Dark mode**: `--bg: #0a0a0a`, `--card: #141414`, `--border: rgba(255,255,255,0.06)`
- **Accent**: `--accent: #c8ff00` (neon green)
- **Typography**: Outfit font, weight 300-800
- **Mobile-first**: max-width 430px, scroll-snap slides

### Layout
- **Slide 1: Overview + Active Tasks**
  - Pill badge with context name
  - Large title: "War *Room*" (Room in accent italic)
  - Subtitle from the source file's title or first line
  - Stats grid (2x2): total tasks, completed, completion %, blocked/urgent
  - Lane sections with ranked items

- **Slide 2: Completed / Shipped**
  - Cards showing completed items with dates
  - Green left-border for completed, amber for in-progress, red for blocked

- **Additional slides** as needed for more sections

### Task Item Styling
- **Top 3 items**: rank badge (accent background, dark text), larger score, accent color
- **Regular items**: dot marker, normal text, dim tag
- **Completed items**: strikethrough or green indicator
- **Blocked items**: red indicator
- **Due dates**: shown as tags

### Interactive Elements
- Nav dots (fixed right side) for slide navigation
- Scroll-snap between slides
- IntersectionObserver to highlight active nav dot

## Markdown Format

The source markdown should follow this general pattern (flexible):

```markdown
# Career Tasks

## This Week
- [ ] Send resume to Anthropic (due: April 2) (hot)
- [ ] Practice agent coding, pure Python
- [x] Ship demo on Modal

## Leads
1. Anthropic FDE — recruiter reached out (hot)
2. Modal — Felicia, presented at GTC panel
3. Prime Intellect — Twitter connection

## Ongoing
- [ ] One ML system design question per day
- [ ] Weekly: ship something visible

## Done
- [x] Presented at Modal GTC panel (Mar 22)
- [x] Built SofaGenius multi-agent system
```

But ANY markdown with `##` sections and list items will work. The skill adapts to the structure it finds.

## Output

A single self-contained HTML file. All CSS and JS inline. No external dependencies except the Google Fonts link for Outfit.

## Important

- Do NOT summarize or change the task content. Render exactly what's in the markdown.
- Keep the visual style identical to the reference (dark mode, neon green accent, mobile-first).
- The HTML must work as a standalone file openable in any browser.
