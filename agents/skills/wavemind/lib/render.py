#!/usr/bin/env python3
"""WaveMind render — takes JSON analysis, produces HTML from template.

Usage:
    python3 render.py < analysis.json > output.html
    python3 render.py analysis.json output.html
    python3 render.py analysis.json  # prints to stdout
"""

import json
import sys
import os
from html import escape
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template.html")


def render_dialogue(dialogue, participants):
    """Render dialogue bubbles. First participant = user (left), others = other (right)."""
    if not dialogue:
        return ""
    # Determine the "user" speaker (first participant listed)
    user_speaker = participants.split("+")[0].strip().lower() if participants else ""
    lines = []
    for entry in dialogue:
        speaker = entry.get("speaker", "")
        text = escape(entry.get("text", ""))
        is_user = speaker.lower().strip() == user_speaker
        bubble_class = "user" if is_user else "other"
        lines.append(
            f'        <div class="bubble {bubble_class}">\n'
            f'          <span class="speaker">{escape(speaker.strip())}</span>\n'
            f'          {text}\n'
            f'        </div>'
        )
    return "\n".join(lines)


def render_transcript(raw_transcript):
    """Render the expandable transcript section."""
    if not raw_transcript:
        return ""
    # Split into paragraphs if it's a single string
    if isinstance(raw_transcript, str):
        paragraphs = [p.strip() for p in raw_transcript.split("\n\n") if p.strip()]
    elif isinstance(raw_transcript, list):
        paragraphs = raw_transcript
    else:
        return ""
    lines = []
    for p in paragraphs:
        # Bold speaker names at the start of paragraphs
        text = escape(p)
        # Re-apply bold for speaker labels like "Lily:" or "CEO:"
        for prefix in ["Lily:", "CEO:", "Growth:", "Builder:", "Jackie:", "Researcher:"]:
            escaped_prefix = escape(prefix)
            if text.startswith(escaped_prefix):
                text = f"<strong>{escaped_prefix}</strong>" + text[len(escaped_prefix):]
                break
        lines.append(f"        <p>{text}</p>")
    return "\n".join(lines)


def render_section(section, participants):
    """Render a single timeline section."""
    round_num = section.get("round", 1)
    header = escape(section.get("header", f"Round {round_num}"))
    quote = escape(section.get("quote", ""))
    is_pivot = section.get("is_pivoting_moment", False)
    dialogue = section.get("dialogue", [])
    raw_transcript = section.get("raw_transcript", "")

    pivot_class = " pivot" if is_pivot else ""
    pivot_badge = '      <div class="pivot-badge">Pivoting Moment</div>\n' if is_pivot else ""

    dialogue_html = render_dialogue(dialogue, participants)
    transcript_html = render_transcript(raw_transcript)

    # Only show transcript toggle if there's a transcript
    transcript_block = ""
    if transcript_html:
        transcript_block = (
            '      <button class="toggle-btn" onclick="toggleTranscript(this)">\n'
            '        <span class="arrow">&#9654;</span> Read original\n'
            '      </button>\n'
            '      <div class="transcript">\n'
            f'{transcript_html}\n'
            '      </div>'
        )

    return (
        f'  <!-- Round {round_num} -->\n'
        f'  <div class="section{pivot_class}">\n'
        f'    <div class="left-col">\n'
        f'      <div class="round-label">Round {round_num}</div>\n'
        f'{pivot_badge}'
        f'      <div class="quote-callout">\n'
        f'        <span class="quote-mark">&ldquo;</span>\n'
        f'        <p>{quote}</p>\n'
        f'      </div>\n'
        f'    </div>\n'
        f'    <div class="right-col">\n'
        f'      <h2 class="section-header">{header}</h2>\n'
        f'      <div class="dialogue">\n'
        f'{dialogue_html}\n'
        f'      </div>\n'
        f'{transcript_block}\n'
        f'    </div>\n'
        f'  </div>'
    )


def render_actionables(actionables):
    """Render the actionable items section at the bottom."""
    if not actionables:
        return ""
    why = actionables.get("why_it_matters", "")
    items = actionables.get("items", [])
    if not why and not items:
        return ""

    items_html = "\n".join(
        f"      <li>{escape(item)}</li>" for item in items
    )

    return (
        '  <div class="actionables">\n'
        '    <h2 class="actionables-header">What Came Out of This</h2>\n'
        '    <div class="actionables-grid">\n'
        '      <div class="actionables-col why">\n'
        '        <h3>Why It Matters</h3>\n'
        f'        <p>{escape(why)}</p>\n'
        '      </div>\n'
        '      <div class="actionables-col items">\n'
        '        <h3>Actionables</h3>\n'
        '        <ul>\n'
        f'{items_html}\n'
        '        </ul>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>'
    )


def format_date(date_str):
    """Convert 2026-03-29 to March 29, 2026."""
    try:
        parts = date_str.split("-")
        months = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{months[int(parts[1])]} {int(parts[2])}, {parts[0]}"
    except (IndexError, ValueError):
        return date_str


def render(analysis):
    """Render the full HTML from a JSON analysis dict."""
    with open(TEMPLATE_PATH, "r") as f:
        template = f.read()

    title = analysis.get("title", "Untitled")
    date_str = analysis.get("date", str(date.today()))
    participants = analysis.get("participants", "")
    sections = analysis.get("sections", [])

    formatted_date = format_date(date_str)
    round_count = len(sections)
    today_formatted = format_date(str(date.today()))

    # Render all sections
    sections_html = "\n\n".join(
        render_section(s, participants) for s in sections
    )

    # Render actionables (optional)
    actionables = analysis.get("actionables", None)
    actionables_html = render_actionables(actionables)

    # Replace placeholders
    html = template
    html = html.replace("{{TITLE}}", escape(title))
    html = html.replace("{{DATE}}", formatted_date)
    html = html.replace("{{PARTICIPANTS}}", escape(participants))
    html = html.replace("{{ROUND_COUNT}}", str(round_count))
    html = html.replace("{{SECTIONS}}", sections_html)
    html = html.replace("{{ACTIONABLES}}", actionables_html)
    html = html.replace("{{CAPTURED_DATE}}", formatted_date)
    html = html.replace("{{VISUALIZED_DATE}}", today_formatted)

    return html


def main():
    # Read JSON from file argument or stdin
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1], "r") as f:
            analysis = json.load(f)
    else:
        analysis = json.load(sys.stdin)

    html = render(analysis)

    # Write to file argument or stdout
    if len(sys.argv) > 2:
        with open(sys.argv[2], "w") as f:
            f.write(html)
    else:
        print(html)


if __name__ == "__main__":
    main()
