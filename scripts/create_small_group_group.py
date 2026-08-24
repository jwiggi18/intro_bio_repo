#!/usr/bin/env python3
"""
create_small_group_group.py — Create the "Small Group Participation" Canvas
Assignment Group for the BIOL 1113 hybrid course, plus its 15 weekly
assignments.

Small Group Participation replaces Blog Posts + Blog Comments in the hybrid
course (decided Aug 13, 2026): instead of writing/commenting on blog posts,
students meet weekly in a small group led by GTA Claudia Goss for hands-on
active learning. Graded on attendance/completion, same model as Learning
Notes.

What this script does:
  - Finds or creates a Canvas Assignment Group named "Small Group
    Participation"
  - Sets a drop_lowest = 2 rule on that group (best 13 of 15 weeks count,
    24 pts/week x 15 weeks = 360 pts available, need 312 -- matches
    hybrid/syllabus.html as of Aug 13, 2026)
  - Finds or creates 15 assignments, "Week 1 Small Group Participation" ...
    "Week 15 Small Group Participation", each worth 24 points, graded as
    completion (no_submission type -- Claudia enters attendance/engagement
    scores directly in the gradebook, there's nothing for students to
    upload), assigned to the group, created as UNPUBLISHED drafts

Due dates: NOT set. Unlike Learning Notes (a single Sunday-11:59-PM policy
for everyone), small group sections meet on different days/times depending
on which section a student is registered in -- there's no single due date
that's correct for every student. Set due_at by hand per section if Canvas
requires it, or leave unset and have Claudia grade after each session.

What this script does NOT do:
  - Publish anything. All 15 assignments are created as drafts; review and
    publish them in Canvas when ready.
  - Touch the Learning Notes group or its drop rule.
  - Create the small group meeting sections/times themselves -- that's a
    Canvas section-setup task, separate from assignment creation.

Usage:
  python3 scripts/create_small_group_group.py <target>
  python3 scripts/create_small_group_group.py hybrid

  <target> is looked up in canvas_targets.py for course_id/base_url --
  same pattern as build/build.sh and upload_to_canvas.py. No more editing
  .env's CANVAS_COURSE_ID by hand.

Requirements:
  - .env with CANVAS_TOKEN
  - canvas_targets.py has the target's course_id/base_url filled in
  - Standard library only (no pip installs)
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target

GROUP_NAME = "Small Group Participation"
POINTS_PER_WEEK = 24
DROP_LOWEST = 2

WEEKS = list(range(1, 16))


# ---------------------------------------------------------------------------
# .env loader (token only) + target lookup (course_id/base_url)
# ---------------------------------------------------------------------------

def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env file not found. Copy .env.example to .env and fill in credentials.")
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


def get_config(target_name):
    env = load_env()
    token = env.get('CANVAS_TOKEN')
    if not token or 'your_' in token:
        print("Error: CANVAS_TOKEN missing or unfilled in .env")
        sys.exit(1)
    target = get_target(target_name)  # exits with a clear error if unknown/no course_id
    return {
        'CANVAS_TOKEN': token,
        'CANVAS_BASE_URL': target['base_url'],
        'CANVAS_COURSE_ID': target['course_id'],
    }


def canvas_request(method, path, token, base_url, data=None):
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
        err_body = e.read().decode('utf-8')
        print(f"  HTTP {e.code} on {method} {url}")
        print(f"  {err_body[:400]}")
        raise


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


# ---------------------------------------------------------------------------
# Group + assignments
# ---------------------------------------------------------------------------

def find_group(name, token, base_url, course_id):
    groups = paginated_get(f'courses/{course_id}/assignment_groups?per_page=100', token, base_url)
    for g in groups:
        if g['name'] == name:
            return g
    return None


def ensure_group(token, base_url, course_id):
    """Find or create the group. Does NOT set the drop_lowest rule yet --
    Canvas rejects a drop rule higher than the group's current assignment
    count, so the rule has to be applied after the 15 assignments exist
    (see set_group_drop_rule, called from main() after assignment creation).
    """
    existing = find_group(GROUP_NAME, token, base_url, course_id)
    if existing:
        print(f"  [exists] {GROUP_NAME} (id: {existing['id']})")
        return existing
    group = canvas_request(
        'POST',
        f'courses/{course_id}/assignment_groups',
        token, base_url,
        {'name': GROUP_NAME}
    )
    print(f"  [created] {GROUP_NAME} (id: {group['id']})")
    return group


def set_group_drop_rule(group_id, token, base_url, course_id):
    """Set drop_lowest on the group. Must run AFTER the group has at least
    DROP_LOWEST assignments in it, or Canvas returns HTTP 400."""
    group = canvas_request('GET', f'courses/{course_id}/assignment_groups/{group_id}', token, base_url)
    current_rules = group.get('rules') or {}
    if current_rules.get('drop_lowest') == DROP_LOWEST:
        print(f"  [ok] drop_lowest already = {DROP_LOWEST}")
        return
    canvas_request(
        'PUT',
        f'courses/{course_id}/assignment_groups/{group_id}',
        token, base_url,
        {'name': GROUP_NAME, 'rules': {'drop_lowest': DROP_LOWEST}}
    )
    print(f"  [updated] drop_lowest = {DROP_LOWEST}")


def find_assignment(name, existing_assignments):
    for a in existing_assignments:
        if a['name'] == name:
            return a
    return None


def assignment_description(week_num):
    return (
        f"<p>This week, meet with your small group and GTA (Claudia Goss) for "
        f"hands-on active learning &mdash; day, time, and location are set by "
        f"your registered section; check Canvas or your syllabus for yours.</p>"
        f"<p>Graded on attendance and engagement, entered by your GTA after "
        f"the session &mdash; there's nothing for you to submit here.</p>"
        f"<p><em>Part of the Small Group Participation assignment group (360 "
        f"pts available across the semester, best 13 of 15 weeks count).</em></p>"
    )


def ensure_week_assignment(week_num, group_id, token, base_url, course_id, existing_assignments):
    name = f"Week {week_num} Small Group Participation"
    existing = find_assignment(name, existing_assignments)
    if existing:
        print(f"  [exists] {name} (id: {existing['id']})")
        return existing

    payload = {
        'assignment': {
            'name': name,
            'description': assignment_description(week_num),
            'points_possible': POINTS_PER_WEEK,
            'grading_type': 'points',
            'submission_types': ['none'],  # attendance/completion, graded by the GTA — nothing to upload
            'assignment_group_id': group_id,
            'published': False,
        }
    }
    # No due_at set — see module docstring (sections meet at different times).

    assignment = canvas_request(
        'POST',
        f'courses/{course_id}/assignments',
        token, base_url,
        payload
    )
    print(f"  [created] {name} (id: {assignment['id']}) — no due date set (see script docstring)")
    return assignment


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/create_small_group_group.py <target>")
        print("  e.g.: python3 scripts/create_small_group_group.py hybrid")
        sys.exit(1)
    target_name = sys.argv[1]

    cfg = get_config(target_name)
    token = cfg['CANVAS_TOKEN']
    base_url = cfg['CANVAS_BASE_URL']
    course_id = cfg['CANVAS_COURSE_ID']

    print(f"Target: {target_name} (course {course_id})")
    print(f"Checking for the '{GROUP_NAME}' assignment group in course {course_id}...")
    group = ensure_group(token, base_url, course_id)

    print(f"\nChecking for the 15 weekly Small Group Participation assignments...")
    existing_assignments = paginated_get(f'courses/{course_id}/assignments?per_page=100', token, base_url)

    created_or_found = []
    for week_num in WEEKS:
        a = ensure_week_assignment(week_num, group['id'], token, base_url, course_id, existing_assignments)
        created_or_found.append(a)

    print(f"\nSetting the group's drop_lowest rule now that assignments exist...")
    set_group_drop_rule(group['id'], token, base_url, course_id)

    print(f"\nDone. {len(created_or_found)}/15 Small Group Participation assignments exist, "
          f"all as unpublished drafts in the '{GROUP_NAME}' group (drop_lowest={DROP_LOWEST}).")
    print("\nNext steps:")
    print("  1. Paste the printed assignment ids into canvas_targets.py's \"hybrid\" target,")
    print("     under small_group_ids (same pattern as learning_notes_ids).")
    print("  2. Set due dates by hand per section if you want Canvas to enforce them.")
    print("  3. Review each assignment in Canvas; add it to the matching week's Module.")
    print("  4. Publish each assignment once its week's content is ready.")
    print("\n  Assignment ids (for canvas_targets.py):")
    ids_line = ", ".join(f"{w}: {a['id']}" for w, a in zip(WEEKS, created_or_found))
    print(f"    {{{ids_line}}}")


if __name__ == '__main__':
    main()
