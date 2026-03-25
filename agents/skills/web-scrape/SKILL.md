# /web-scrape

Lightweight web scraping toolkit for ML research. Searches HuggingFace, GitHub, and arXiv from the CLI with structured table output.

## Location

`scripts/web_scrape.py` (repo root)

## Dependencies

```bash
pip install beautifulsoup4 requests tabulate
```

## Commands

### HuggingFace trending datasets

```bash
python scripts/web_scrape.py hf-trending --limit 20
```

Returns: Dataset ID, downloads, likes, last updated, description, URL.

### GitHub trending repos

```bash
python scripts/web_scrape.py github-trending --topic "agent" --limit 20
```

Returns: Repo name, stars, language, last push date, description, URL. Searches repos pushed in the last 7 days, sorted by stars.

### arXiv paper search

```bash
python scripts/web_scrape.py arxiv-search "coding agent training" --limit 10
```

Returns: Title, authors, published date, summary, URL. Sorted by submission date (newest first).

## Output

All commands print formatted tables to stdout. If `tabulate` is installed, uses clean table formatting; otherwise falls back to plain-text columns.

## Notes

- No authentication required for any source
- GitHub search API has rate limits (~10 req/min unauthenticated)
- arXiv API is generally unrestricted but be courteous with request frequency
- All network requests have a 15-second timeout
