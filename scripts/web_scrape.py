#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight web scraping toolkit for ML research.

Usage:
    python scripts/web_scrape.py hf-trending [--limit N]
    python scripts/web_scrape.py github-trending [--topic TOPIC] [--limit N]
    python scripts/web_scrape.py arxiv-search "query" [--limit N]
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus

import requests

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


TIMEOUT = 15
USER_AGENT = "SofaGenius-Researcher/1.0"


def truncate(text: str, length: int = 80) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:length] + "..." if len(text) > length else text


def print_table(headers: list[str], rows: list[list], title: str = ""):
    if title:
        print(f"\n=== {title} ===\n")
    if not rows:
        print("  (no results)")
        return
    if HAS_TABULATE:
        print(tabulate(rows, headers=headers, tablefmt="simple", maxcolwidths=80))
    else:
        # Plain text fallback
        col_widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(len(headers))]
        col_widths = [min(w, 80) for w in col_widths]
        fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
        print(fmt.format(*[str(h)[:80] for h in headers]))
        print(fmt.format(*["-" * w for w in col_widths]))
        for row in rows:
            print(fmt.format(*[str(c)[:80] for c in row]))
    print(f"\n  ({len(rows)} results)")


# ---------------------------------------------------------------------------
# HuggingFace trending datasets
# ---------------------------------------------------------------------------
def hf_trending(limit: int = 20):
    """Fetch trending/most-downloaded datasets from HuggingFace API."""
    url = "https://huggingface.co/api/datasets"
    params = {
        "sort": "downloads",
        "direction": -1,
        "limit": limit,
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching HuggingFace datasets: {e}", file=sys.stderr)
        return

    data = resp.json()
    rows = []
    for ds in data[:limit]:
        ds_id = ds.get("id", "")
        downloads = ds.get("downloads", 0)
        likes = ds.get("likes", 0)
        updated = ds.get("lastModified", "")[:10]
        desc = truncate(ds.get("description") or ds.get("cardData", {}).get("description", "") or "", 60)
        link = f"https://huggingface.co/datasets/{ds_id}"
        rows.append([ds_id, downloads, likes, updated, desc, link])

    print_table(
        ["Dataset", "Downloads", "Likes", "Updated", "Description", "URL"],
        rows,
        title="HuggingFace Trending Datasets",
    )


# ---------------------------------------------------------------------------
# GitHub trending repos
# ---------------------------------------------------------------------------
def github_trending(topic: str = "machine-learning", limit: int = 20):
    """Fetch trending repos from GitHub search API (no auth needed)."""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"{topic} pushed:>{_days_ago(7)}",
        "sort": "stars",
        "order": "desc",
        "per_page": limit,
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github.v3+json"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching GitHub trending: {e}", file=sys.stderr)
        return

    data = resp.json()
    rows = []
    for repo in data.get("items", [])[:limit]:
        name = repo.get("full_name", "")
        stars = repo.get("stargazers_count", 0)
        lang = repo.get("language", "") or ""
        updated = repo.get("pushed_at", "")[:10]
        desc = truncate(repo.get("description", "") or "", 60)
        link = repo.get("html_url", "")
        rows.append([name, stars, lang, updated, desc, link])

    print_table(
        ["Repo", "Stars", "Lang", "Pushed", "Description", "URL"],
        rows,
        title=f"GitHub Trending — \"{topic}\"",
    )


def _days_ago(n: int) -> str:
    from datetime import timedelta
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# arXiv paper search
# ---------------------------------------------------------------------------
def arxiv_search(query: str, limit: int = 10):
    """Search arXiv for recent papers matching query."""
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{quote_plus(query)}",
        "start": 0,
        "max_results": limit,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching arXiv papers: {e}", file=sys.stderr)
        return

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    entries = root.findall("atom:entry", ns)

    rows = []
    for entry in entries[:limit]:
        title = truncate((entry.findtext("atom:title", "", ns) or "").strip(), 70)
        published = (entry.findtext("atom:published", "", ns) or "")[:10]
        summary = truncate((entry.findtext("atom:summary", "", ns) or "").strip(), 60)
        authors = ", ".join(
            a.findtext("atom:name", "", ns)
            for a in entry.findall("atom:author", ns)[:3]
        )
        if len(entry.findall("atom:author", ns)) > 3:
            authors += " et al."
        link = ""
        for lnk in entry.findall("atom:link", ns):
            if lnk.get("type") == "text/html" or lnk.get("title") == "pdf":
                pass
            href = lnk.get("href", "")
            if "/abs/" in href:
                link = href
                break
        if not link:
            link_el = entry.find("atom:id", ns)
            link = link_el.text if link_el is not None else ""

        rows.append([title, authors, published, summary, link])

    print_table(
        ["Title", "Authors", "Published", "Summary", "URL"],
        rows,
        title=f"arXiv — \"{query}\"",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Web scraping toolkit for ML research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command")

    # hf-trending
    p_hf = sub.add_parser("hf-trending", help="HuggingFace trending datasets")
    p_hf.add_argument("--limit", type=int, default=20)

    # github-trending
    p_gh = sub.add_parser("github-trending", help="GitHub trending repos")
    p_gh.add_argument("--topic", type=str, default="machine-learning")
    p_gh.add_argument("--limit", type=int, default=20)

    # arxiv-search
    p_ax = sub.add_parser("arxiv-search", help="arXiv paper search")
    p_ax.add_argument("query", type=str)
    p_ax.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "hf-trending":
        hf_trending(limit=args.limit)
    elif args.command == "github-trending":
        github_trending(topic=args.topic, limit=args.limit)
    elif args.command == "arxiv-search":
        arxiv_search(query=args.query, limit=args.limit)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
