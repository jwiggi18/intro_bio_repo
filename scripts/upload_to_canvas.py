#!/usr/bin/env python3
"""
upload_to_canvas.py — Upload built HTML pages to Canvas as wiki pages.

Reads Canvas credentials from .env (never hardcoded); reads the target
course's id/base_url from canvas_targets.py.

Usage:
  python3 scripts/upload_to_canvas.py sandbox              # upload all built pages
  python3 scripts/upload_to_canvas.py sandbox week01/      # upload one week
  python3 scripts/upload_to_canvas.py hybrid                # upload all hybrid pages

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - canvas_targets.py has the target's course_id/base_url filled in
  - Run build/build.sh <target> first to generate build/biol1113-<target>/ output

Requires Python 3.8+. Standard library only.
"""

import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target

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


def get_token():
    env = load_env()
    token = env.get('CANVAS_TOKEN')
    if not token or 'your_' in token:
        print("Error: CANVAS_TOKEN missing or unfilled in .env")
        sys.exit(1)
    return token


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


def page_slug_from_path(html_path, build_dir):
    """
    Derive a Canvas page URL slug from the file path.
    e.g. week01/week.html → week01-week
         homepage.html    → homepage
    """
    rel = Path(html_path).relative_to(build_dir)
    parts = list(rel.parts)
    parts[-1] = parts[-1].replace('.html', '')
    slug = '-'.join(parts)
    slug = re.sub(r'[^a-z0-9-]', '-', slug.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug


def page_title_from_path(html_path, build_dir):
    """Derive a human-readable title from the file path."""
    rel = Path(html_path).relative_to(build_dir)
    parts = list(rel.parts)
    parts[-1] = parts[-1].replace('.html', '')
    # e.g. week01/week → Week 01 — Week
    return ' — '.join(p.replace('-', ' ').title() for p in parts)


def upsert_page(html_path, build_dir, token, base_url, course_id):
    """Create or update a Canvas wiki page from a built HTML file."""
    html_path = Path(html_path)
    body = html_path.read_text(encoding='utf-8')
    slug = page_slug_from_path(html_path, build_dir)
    title = page_title_from_path(html_path, build_dir)

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
        if e.code == 400:
            # Front page cannot be set to unpublished — retry as published
            page_data['wiki_page']['published'] = True
            result = canvas_request(
                'PUT',
                f'courses/{course_id}/pages/{slug}',
                token, base_url,
                data=page_data
            )
            print(f"  [updated] {slug} (front page — kept published)")
            return result
        raise


def update_syllabus_body(syllabus_html_path, token, base_url, course_id):
    """Push syllabus.html's built content into course.syllabus_body — the
    field behind Canvas's native Syllabus tool (/courses/:id/assignments/
    syllabus), which is a completely different thing from the syllabus wiki
    page (/pages/syllabus) upsert_page() above pushes to. Both need to carry
    the same content since the homepage links to the native tool."""
    body = syllabus_html_path.read_text(encoding='utf-8')
    canvas_request(
        'PUT',
        f'courses/{course_id}',
        token, base_url,
        data={'course': {'syllabus_body': body}}
    )
    print(f"  [updated] course syllabus_body (native Syllabus tool)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_built_files(build_dir, subset=None):
    if not build_dir.exists():
        print(f"Error: Build output not found at {build_dir}")
        print(f"Run 'bash build/build.sh <target>' first.")
        sys.exit(1)

    # Upload: any root-level .html and weekNN/week.html — skip legacy shells
    def is_uploadable(p):
        if p.parent == build_dir and p.suffix == '.html':
            return True
        if p.name == 'week.html' and p.parent.name.startswith('week'):
            return True
        return False

    if subset is None:
        return sorted(f for f in build_dir.rglob('*.html') if is_uploadable(f))
    else:
        p = build_dir / subset
        if p.is_dir():
            return sorted(f for f in p.glob('*.html') if is_uploadable(f))
        elif p.suffix == '.html':
            return [p] if is_uploadable(p) else []
    return []


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/upload_to_canvas.py <target> [file/folder]")
        print("  target = sandbox, live, hybrid, etc. — see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)  # exits with a clear error if unknown/unconfigured
    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']
    build_dir = ROOT / "build" / f"biol1113-{target_name}"

    raw_subset = sys.argv[2] if len(sys.argv) > 2 else None
    files = collect_built_files(build_dir, raw_subset)

    if not files:
        print("No built HTML files found to upload.")
        sys.exit(0)

    print(f"Uploading {len(files)} page(s) to Canvas course {course_id} (target: {target_name})...")
    print(f"Instance: {base_url}")
    print()

    for f in files:
        upsert_page(f, build_dir, token, base_url, course_id)

    # If syllabus.html is part of what's being uploaded, also sync it into
    # the native Syllabus tool's syllabus_body field (separate from the wiki
    # page above) — only when it's actually in this run, so a single-week
    # push doesn't touch it.
    syllabus_file = build_dir / "syllabus.html"
    if syllabus_file in files:
        update_syllabus_body(syllabus_file, token, base_url, course_id)

    print(f"\nDone. {len(files)} page(s) uploaded as drafts.")
    print("Review and publish them in Canvas.")


if __name__ == '__main__':
    main()
