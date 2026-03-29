---
name: transcript
description: Extract raw transcripts from podcast pages (Wave AI, podscripts.co, and other Next.js podcast sites). Returns speaker-attributed dialogue with timestamps.
argument-hint: <url>
allowed-tools: Read, Write, Bash
---

# Transcript Extractor

Extract raw, verbatim transcripts from podcast episode pages. Returns speaker-attributed dialogue with timestamps, not AI summaries.

## Usage

```
/transcript <url>
```

## How It Works

Most podcast sites (Wave AI, podscripts.co) are Next.js apps. The transcript is embedded in React Server Component (RSC) payloads in the HTML, not visible as regular DOM text. This skill extracts it.

## Steps

1. Fetch the page HTML:
   ```bash
   curl -s "<url>" > /tmp/transcript_page.html
   ```

2. Extract the transcript using this Python script:
   ```bash
   python3 -c "
   import json, re, sys

   with open('/tmp/transcript_page.html') as f:
       html = f.read()

   # Find transcript JSON array in Next.js RSC payload
   # Look for speaker-attributed segments: [{\"speaker\":\"...\",\"start\":...,\"text\":\"...\"}]
   pattern = r'\[{[\\\\]*\"speaker[\\\\]*\":[\\\\]*\"'
   match = re.search(pattern, html)
   if not match:
       print('ERROR: No transcript found in page. The page may not have a transcript section, or uses a different format.')
       sys.exit(1)

   # Find the start of the JSON array
   start = html.rfind('[', max(0, match.start() - 5), match.start() + 1)

   # Unescape the RSC payload
   # Content may have \\\" escaping from the RSC wrapper
   chunk = html[start:]

   # Try to find and parse the JSON array
   # Unescape first
   unescaped = chunk.replace('\\\\\"', '\"').replace('\\\\n', '\n')

   # Find matching bracket
   depth = 0
   for i, c in enumerate(unescaped):
       if c == '[': depth += 1
       elif c == ']': depth -= 1
       if depth == 0:
           try:
               segments = json.loads(unescaped[:i+1])
               for seg in segments:
                   speaker = seg.get('speaker', 'Unknown')
                   start_time = seg.get('start', 0)
                   mins = int(start_time // 60)
                   secs = int(start_time % 60)
                   text = seg.get('text', '')
                   print(f'{speaker} ({mins}:{secs:02d})')
                   print(text)
                   print()
               print(f'--- Extracted {len(segments)} segments ---', file=sys.stderr)
               sys.exit(0)
           except json.JSONDecodeError:
               continue

   print('ERROR: Found transcript data but could not parse it.')
   sys.exit(1)
   " > /tmp/transcript_output.md
   ```

3. Read the output and save it:
   - Read `/tmp/transcript_output.md`
   - If the user specified a save location, write it there
   - Otherwise, report the content and suggest where to save it

## Output Format

The transcript is formatted as:
```
Speaker Name (MM:SS)
The verbatim text of what they said.

Another Speaker (MM:SS)
Their response.
```

## Supported Sites

- **Wave AI** (pod.wave.co) - podcast summaries + transcripts
- **Podscripts.co** - podcast transcription service
- Any Next.js site with speaker-attributed transcript JSON in RSC payloads

## Limitations

- Only works with Next.js sites that embed transcript data in the initial HTML
- Sites that load transcripts via separate API calls (after page load) may not work
- Very long transcripts may need the curl output saved to a file first

## Tips

- If you get "No transcript found", the site may use a different format. Try fetching the page and searching for "speaker" or "transcript" in the raw HTML to find the data structure.
- The extracted transcript is the raw, verbatim dialogue. Clean up obvious transcription errors but preserve original words.
