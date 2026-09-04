#!/usr/bin/env python3
"""
patch_declaration_quizzes_etiquette.py — One-off patch: add the "Blog
Commenting Etiquette" section to the 14 already-existing "Week N Blog
Comment Declaration" quizzes (weeks 2-15) on a target, and fill in Week 2's
"specific instructions" paragraph.

Why a separate one-off rather than just re-running
create_declaration_quizzes.py: that script only *creates* quizzes that don't
exist yet (find_quiz() short-circuits on an existing title without touching
its description). These 14 quizzes already exist as unpublished drafts on
sandbox/live (created by that script weeks ago), so getting the new
template content onto them needs an explicit PUT.

Safety: this does NOT blindly overwrite. For each quiz it GETs the current
description and only proceeds if it still matches the known original
template *exactly* (i.e. nobody has hand-edited it since it was created --
confirmed via project notes that these were all still raw as of Aug 23,
2026). Any quiz whose description doesn't match is skipped and reported,
not clobbered. Preserves the quiz's current published state explicitly.

Usage:
  python3 scripts/patch_declaration_quizzes_etiquette.py sandbox
  python3 scripts/patch_declaration_quizzes_etiquette.py live
  python3 scripts/patch_declaration_quizzes_etiquette.py sandbox --dry-run

Requirements:
  - .env with CANVAS_TOKEN
  - canvas_targets.py has the target's course_id/base_url filled in

Requires Python 3.8+. Standard library only.
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target
from scripts.create_declaration_quizzes import (
    quiz_description as new_description,
    WEEKS,
)


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env file not found.")
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


def canvas_request(method, path, token, base_url, data=None):
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def paginated_get(path, token, base_url):
    results = []
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {'Authorization': f'Bearer {token}'}
    while url:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            results.extend(json.loads(r.read().decode('utf-8')))
            link = r.headers.get('Link', '')
            next_url = None
            for part in link.split(','):
                if 'rel="next"' in part:
                    next_url = part.split(';')[0].strip().strip('<>')
            url = next_url
    return results


# Recognizing an untouched quiz: Canvas rewrites saved HTML on the way back
# out (entities like &mdash; become real characters, "<hr />" becomes
# "<hr>", relative hrefs get absolutized with data-api-endpoint attributes
# added -- all confirmed benign, same as file-download links elsewhere in
# this repo), so comparing the *exact* original template string never
# matches. Instead: presence of the literal "[PLACEHOLDER" marker (survives
# Canvas's rewriting untouched, since it's plain text, not markup) means the
# quiz is still in its pristine as-created state; presence of "Blog
# Commenting Etiquette" means this patch has already run against it.
PLACEHOLDER_MARKER = "[PLACEHOLDER"
ETIQUETTE_MARKER = "Blog Commenting Etiquette"


def find_quiz(title, quizzes):
    for q in quizzes:
        if q['title'] == title:
            return q
    return None


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']
    if len(args) != 1:
        print("Usage: python3 scripts/patch_declaration_quizzes_etiquette.py <target> [--dry-run]")
        sys.exit(1)

    target_name = args[0]
    target_config = get_target(target_name)
    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']

    print(f"Target: {target_name} (course {course_id}){' [DRY RUN]' if dry_run else ''}\n")

    quizzes = paginated_get(f'courses/{course_id}/quizzes?per_page=100', token, base_url)

    patched, skipped = [], []
    for week_num in WEEKS:
        title = f"Week {week_num} Blog Comment Declaration"
        quiz = find_quiz(title, quizzes)
        if not quiz:
            print(f"  [missing] {title} — no such quiz on this course, skipping")
            skipped.append(week_num)
            continue

        full = canvas_request('GET', f"courses/{course_id}/quizzes/{quiz['id']}", token, base_url)
        current_desc = full.get('description') or ''

        if ETIQUETTE_MARKER in current_desc:
            print(f"  [skip] {title} (id {quiz['id']}) — already has the Etiquette section, "
                  f"not touching it again")
            skipped.append(week_num)
            continue

        if PLACEHOLDER_MARKER not in current_desc:
            print(f"  [skip] {title} (id {quiz['id']}) — no [PLACEHOLDER] marker found "
                  f"(hand-edited already?) — not touching it, needs a manual look")
            skipped.append(week_num)
            continue

        new_desc = new_description(week_num, course_id).strip()
        if dry_run:
            print(f"  [would patch] {title} (id {quiz['id']}) — published={full.get('published')}")
            patched.append(week_num)
            continue

        canvas_request(
            'PUT', f"courses/{course_id}/quizzes/{quiz['id']}", token, base_url,
            {'quiz': {'description': new_desc, 'published': full.get('published', False)}}
        )
        print(f"  [patched] {title} (id {quiz['id']}) — published stayed {full.get('published')}")
        patched.append(week_num)

    verb = "Would patch" if dry_run else "Patched"
    print(f"\n{verb} {len(patched)}/{len(WEEKS)} quizzes. Skipped: {skipped or 'none'}.")


if __name__ == '__main__':
    main()
