"""
Publishes DEV_POST.md to DEV (dev.to) through the Forem API.

    set DEV_API_KEY=...            # Windows
    python scripts/publish_dev.py  # publishes live

    python scripts/publish_dev.py --draft   # creates an unpublished draft

Create the key at https://dev.to/settings/extensions -> "DEV Community API Keys".
The key is read from the environment or asked for interactively; it is never
written to disk. Front matter in DEV_POST.md supplies the title, description,
tags and cover image, so the markdown file stays the single source of truth.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://dev.to/api/articles"
POST = Path(__file__).resolve().parent.parent / "DEV_POST.md"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        raise SystemExit("DEV_POST.md must start with YAML front matter.")
    _, meta, body = text.split("---", 2)
    fields: dict[str, str] = {}
    for line in meta.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields, body.lstrip("\n")


def build_article(meta: dict[str, str], body: str, *, draft: bool) -> dict:
    tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    if len(tags) > 4:
        raise SystemExit(f"DEV accepts at most 4 tags, found {len(tags)}: {tags}")
    article = {
        "title": meta.get("title", "Untitled"),
        "body_markdown": body,
        "published": not draft,
        "tags": ", ".join(tags),
    }
    for source, target in (
        ("description", "description"),
        ("cover_image", "main_image"),
        ("canonical_url", "canonical_url"),
        ("series", "series"),
    ):
        if meta.get(source):
            article[target] = meta[source]
    return {"article": article}


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish DEV_POST.md to dev.to.")
    parser.add_argument("--draft", action="store_true", help="create a draft instead of publishing")
    parser.add_argument("--api-key", help="DEV API key (defaults to $DEV_API_KEY)")
    parser.add_argument("--file", type=Path, default=POST, help="markdown file to publish")
    args = parser.parse_args()

    key = args.api_key or os.environ.get("DEV_API_KEY") or getpass.getpass("DEV API key: ")
    if not key.strip():
        raise SystemExit("No API key provided.")

    meta, body = parse_front_matter(args.file.read_text(encoding="utf-8"))
    payload = build_article(meta, body, draft=args.draft)

    print(f"{'Draft' if args.draft else 'Publishing'}: {payload['article']['title']}")
    print(f"Tags: {payload['article']['tags']}")

    request = urllib.request.Request(
        API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": key.strip(), "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        print(f"\nDEV returned {error.code}:\n{detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"\nCould not reach dev.to: {error.reason}", file=sys.stderr)
        return 1

    print(f"\nOK: {result.get('url')}")
    print(f"State: {'draft' if not result.get('published') else 'published'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
