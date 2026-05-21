#!/usr/bin/env python3
"""
upload_to_canvas.py — Upload built HTML pages to Canvas as wiki pages.

Reads Canvas credentials from .env (never hardcoded).
Uploads body-only HTML from build/biol1113/ to your Canvas course.

Usage:
  python3 scripts/upload_to_canvas.py              # upload all built pages
  python3 scripts/upload_to_canvas.py week01/      # upload one week
  python3 scripts/upload_to_canvas.py week01/overview.html  # upload one file

Requirements:
  - .env file in repo root with CANVAS_TOKEN, CANVAS_BASE_URL, CANVAS_COURSE_ID
  - Run build/build.sh first to generate build/biol1113/ output

Requires Python 3.8+. Standard library only.
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
BUILD_DIR = ROOT / "build" / "biol1113"

# ---------------------------------------------------------------------------
# Load .env
# ---------------------------------------------------------------------------

def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env file not found.")
        print("Copy .env.example to .env and fill in your Canvas credentials.")
        sys.exit(1)

    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, val = line.partition('=')
            env[key.strip()] = val.strip()
    return env


def get_config():
    env = load_env()
    required = ['CANVAS_TOKEN', 'CANVAS_BASE_URL', 'CANVAS_COURSE_ID']
    missing = [k for k in required if not env.get(k) or 'your_' in env.get(k, '')]
    if missing:
        print(f"Error: Missing or unfilled values in .env: {', '.join(missing)}")
        sys.exit(1)
    return env


# ---------------------------------------------------------------------------
# Canvas API helpers
# ---------------------------------------------------------------------------

def canvas_request(method, path, token, base_url, data=None):
    """Make a Canvas API request. Returns parsed JSON response."""
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"  HTTP {e.code} on {method} {url}")
        print(f"  Response: {body[:300]}")
        raise


def page_slug_from_path(html_path):
    """
    Derive a Canvas page URL slug from the file path.
    e.g. week01/overview.html → biol1113-week01-overview
    """
    rel = Path(html_path).relative_to(BUILD_DIR)
    parts = list(rel.parts)
    # Remove .html extension from last part
    parts[-1] = parts[-1].replace('.html', '')
    slug = 'biol1113-' + '-'.join(parts)
    # Canvas slugs: lowercase, hyphens only
    slug = re.sub(r'[^a-z0-9-]', '-', slug.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def page_title_from_path(html_path):
    """Derive a human-readable title from the file path."""
    rel = Path(html_path).relative_to(BUILD_DIR)
    parts = list(rel.parts)
    parts[-1] = parts[-1].replace('.html', '')
    return ' — '.join(p.replace('-', ' ').title() for p in parts)


def upsert_page(html_path, token, base_url, course_id):
    """Create or update a Canvas wiki page from a built HTML file."""
    html_path = Path(html_path)
    body = html_path.read_text(encoding='utf-8')
    slug = page_slug_from_path(html_path)
    title = page_title_from_path(html_path)

    page_data = {
        'wiki_page': {
            'title': title,
            'body': body,
            'published': False,   # Upload as draft; publish manually in Canvas
        }
    }

    # Try to update existing page first, then create
    try:
        result = canvas_request(
            'PUT',
            f'courses/{course_id}/pages/{slug}',
            token, base_url,
            data=page_data
        )
        print(f"  [updated] {slug}")
        return result
    except urllib.error.HTTPError as e:
        if e.code == 404:
            result = canvas_request(
                'POST',
                f'courses/{course_id}/pages',
                token, base_url,
                data=page_data
            )
            print(f"  [created] {slug}")
            return result
        raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_built_files(target=None):
    if not BUILD_DIR.exists():
        print(f"Error: Build output not found at {BUILD_DIR}")
        print("Run 'bash build/build.sh' first.")
        sys.exit(1)

    if target is None:
        return sorted(BUILD_DIR.rglob('*.html'))
    else:
        p = BUILD_DIR / Path(target).relative_to(ROOT) if Path(target).is_absolute() else BUILD_DIR / target
        if p.is_dir():
            return sorted(p.glob('*.html'))
        elif p.suffix == '.html':
            return [p]
    return []


def main():
    config = get_config()
    token = config['CANVAS_TOKEN']
    base_url = config['CANVAS_BASE_URL']
    course_id = config['CANVAS_COURSE_ID']

    target = sys.argv[1] if len(sys.argv) > 1 else None
    files = collect_built_files(target)

    if not files:
        print("No built HTML files found to upload.")
        sys.exit(0)

    print(f"Uploading {len(files)} page(s) to Canvas course {course_id}...")
    print(f"Instance: {base_url}")
    print()

    for f in files:
        upsert_page(f, token, base_url, course_id)

    print(f"\nDone. {len(files)} page(s) uploaded as drafts.")
    print("Review and publish them in Canvas.")


if __name__ == '__main__':
    main()
