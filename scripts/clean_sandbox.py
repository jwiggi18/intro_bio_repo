#!/usr/bin/env python3
"""
clean_sandbox.py — Wipe all content from the Canvas sandbox course.

SAFETY GUARDS:
  - Reads course ID from CANVAS_SANDBOX_ID in .env (NOT CANVAS_COURSE_ID)
  - Fetches the course name and aborts unless it contains 'sandbox' (case-insensitive)
  - Requires --yes flag to actually delete anything (--dry-run is the default)

This script will NEVER touch your live BIOL 1113 course.

Usage:
  python3 scripts/clean_sandbox.py --dry-run   # inventory only, no changes
  python3 scripts/clean_sandbox.py --yes        # actually wipe the sandbox
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env not found.")
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        env[k.strip()] = v.strip()
    return env


def canvas_get(path, token, base_url):
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode('utf-8'))


def canvas_delete(path, token, base_url):
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'}, method='DELETE')
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def paginated_get(path, token, base_url):
    """Fetch all pages of a paginated Canvas API endpoint."""
    results = []
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    while url:
        req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req) as r:
            results.extend(json.loads(r.read().decode('utf-8')))
            # Check for next page in Link header
            link = r.headers.get('Link', '')
            next_url = None
            for part in link.split(','):
                if 'rel="next"' in part:
                    next_url = part.split(';')[0].strip().strip('<>')
            url = next_url
    return results


def main():
    dry_run = '--yes' not in sys.argv
    if dry_run:
        print("DRY RUN — no changes will be made (use --yes to actually delete)")

    env = load_env()
    token = env.get('CANVAS_TOKEN', '')
    base_url = env.get('CANVAS_BASE_URL', '')
    sandbox_id = env.get('CANVAS_SANDBOX_ID', '')

    if not token or 'your_' in token:
        print("Error: CANVAS_TOKEN not set in .env")
        sys.exit(1)
    if not sandbox_id or 'your_' in sandbox_id:
        print("Error: CANVAS_SANDBOX_ID not set in .env")
        sys.exit(1)

    # Safety check: fetch course and verify it's a sandbox
    print(f"Fetching course {sandbox_id}...")
    try:
        course = canvas_get(f'courses/{sandbox_id}', token, base_url)
    except Exception as e:
        print(f"Error fetching course: {e}")
        sys.exit(1)

    course_name = course.get('name', '')
    print(f"Course name: {course_name}")

    if 'sandbox' not in course_name.lower():
        print(f"\nABORTED: Course name '{course_name}' does not contain 'sandbox'.")
        print("This script only works on sandbox courses. Set CANVAS_SANDBOX_ID correctly.")
        sys.exit(1)

    print(f"\nTarget confirmed as sandbox: '{course_name}'\n")

    deleted = 0

    # Pages
    pages = paginated_get(f'courses/{sandbox_id}/pages', token, base_url)
    print(f"Pages: {len(pages)}")
    for p in pages:
        if dry_run:
            print(f"  [dry-run] would delete page: {p.get('url', '?')}")
        else:
            status = canvas_delete(f"courses/{sandbox_id}/pages/{p['url']}", token, base_url)
            print(f"  [deleted] page {p.get('url', '?')} — HTTP {status}")
            deleted += 1

    # Modules (items first, then module)
    modules = paginated_get(f'courses/{sandbox_id}/modules', token, base_url)
    print(f"Modules: {len(modules)}")
    for mod in modules:
        items = paginated_get(f"courses/{sandbox_id}/modules/{mod['id']}/items", token, base_url)
        for item in items:
            if dry_run:
                print(f"  [dry-run] would delete module item: {item.get('title', '?')}")
            else:
                canvas_delete(f"courses/{sandbox_id}/modules/{mod['id']}/items/{item['id']}", token, base_url)
                deleted += 1
        if dry_run:
            print(f"  [dry-run] would delete module: {mod.get('name', '?')}")
        else:
            canvas_delete(f"courses/{sandbox_id}/modules/{mod['id']}", token, base_url)
            deleted += 1

    # Assignments
    assignments = paginated_get(f'courses/{sandbox_id}/assignments', token, base_url)
    print(f"Assignments: {len(assignments)}")
    for a in assignments:
        if dry_run:
            print(f"  [dry-run] would delete assignment: {a.get('name', '?')}")
        else:
            canvas_delete(f"courses/{sandbox_id}/assignments/{a['id']}", token, base_url)
            deleted += 1

    if dry_run:
        print("\nDry run complete. Run with --yes to execute deletions.")
    else:
        print(f"\nDone. {deleted} items deleted from sandbox '{course_name}'.")


if __name__ == '__main__':
    main()
