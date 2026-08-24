#!/usr/bin/env python3
"""
create_learning_notes_group.py — Create the "Learning Notes" Canvas Assignment
Group for BIOL 1113, plus its 15 weekly assignments.

Learning Notes replaced ELQs on Aug 10, 2026 (one embedded quiz per video ->
a photo-of-notes submission). It was then restructured Aug 10-11, 2026 from
"one assignment per video" to "one assignment per week": at the end of each
week, students submit photos of their notes over ALL of that week's videos
as a single upload. This script reflects the per-week version.

What this script does:
  - Finds or creates a Canvas Assignment Group named "Learning Notes"
  - Sets a drop_lowest = 4 rule on that group (best 11 of 15 weeks count,
    16 pts/week x 15 weeks = 240 pts available, need 176 -- matches
    syllabus.html as of Aug 11, 2026)
  - Finds or creates 15 assignments, "Week 1 Learning Notes" ... "Week 15
    Learning Notes", each worth 16 points, submission type = file/photo
    upload, assigned to the group, created as UNPUBLISHED drafts

Due dates: set for Weeks 1-14 (Sunday 11:59 PM Central of that week, per
CLAUDE.md's week table / the "assignments open Monday, due Sunday 11:59 PM"
policy in syllabus.html). Week 15 is intentionally left WITHOUT a due date:
CLAUDE.md lists it as "Nov 30-Dec 4" (Monday-Friday), which breaks the
Monday-Sunday pattern every other week follows (it sits right after Fall
Break Nov 23-25 and the University Holiday Nov 26-27), and it isn't clear
whether "due Sunday" still applies. Set Week 15's due date by hand once
that's confirmed.

What this script does NOT do:
  - Publish anything. All 15 assignments are created as drafts; review and
    publish them in Canvas when ready.
  - Touch the Blog Posts / Blog Comments groups or their drop rules.
  - Set unlock_at (module release dates) -- that's handled separately via
    Canvas Modules, not yet created for Weeks 5-15 (see SESSION_NOTES.md).

Usage:
  python3 scripts/create_learning_notes_group.py <target>
  python3 scripts/create_learning_notes_group.py hybrid

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

GROUP_NAME = "Learning Notes"
POINTS_PER_WEEK = 16
DROP_LOWEST = 4

# week_num -> due_at (UTC ISO8601), computed from Sunday 11:59 PM America/Chicago.
# None means "do not set a due date" (see Week 15 note in the module docstring).
DUE_DATES_UTC = {
    1:  "2026-08-24T04:59:00Z",   # Sun Aug 23, 11:59 PM CDT
    2:  "2026-08-31T04:59:00Z",   # Sun Aug 30
    3:  "2026-09-07T04:59:00Z",   # Sun Sep 6
    4:  "2026-09-14T04:59:00Z",   # Sun Sep 13
    5:  "2026-09-21T04:59:00Z",   # Sun Sep 20
    6:  "2026-09-28T04:59:00Z",   # Sun Sep 27
    7:  "2026-10-05T04:59:00Z",   # Sun Oct 4
    8:  "2026-10-12T04:59:00Z",   # Sun Oct 11
    9:  "2026-10-19T04:59:00Z",   # Sun Oct 18
    10: "2026-10-26T04:59:00Z",   # Sun Oct 25
    11: "2026-11-02T05:59:00Z",   # Sun Nov 1, 11:59 PM CST (DST ends this day)
    12: "2026-11-09T05:59:00Z",   # Sun Nov 8
    13: "2026-11-16T05:59:00Z",   # Sun Nov 15
    14: "2026-11-23T05:59:00Z",   # Sun Nov 22
    15: None,                     # Nov 30-Dec 4 doesn't fit the pattern -- set by hand
}

WEEKS = list(range(1, 16))


# ---------------------------------------------------------------------------
# .env loader + Canvas API helpers (same pattern as other scripts)
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
        'TARGET': target,
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


def assignment_description(week_num, pdf_url=None):
    pdf_line = (
        f'<a href="{pdf_url}" target="_blank">Creating and Submitting a Multi-Page PDF</a>'
        if pdf_url else
        "Creating and Submitting a Multi-Page PDF (see the Important Links page)"
    )
    return (
        f"<p>At the end of Week {week_num}, submit your notes over "
        f"<strong>all</strong> of this week's videos as a single upload. Use the "
        f"structured notes template provided, or take your own notes in your own "
        f"format &mdash; either is accepted.</p>"
        f"<p>Your upload must be a single PDF file, not multiple photos or documents. "
        f"{pdf_line} outlines several ways to do this depending on your equipment.</p>"
        f"<p>Graded on completion, not on being &ldquo;right.&rdquo; To earn points, "
        f"your notes must demonstrate a clear effort to correctly outline and "
        f"document this week's learning materials thoroughly.</p>"
        f"<p><em>Part of the Learning Notes assignment group (240 pts available "
        f"across the semester, best 11 of 15 weeks count). Material without a "
        f"notes prompt can still appear on exams.</em></p>"
    )


def ensure_week_assignment(week_num, group_id, token, base_url, course_id, existing_assignments, pdf_url=None):
    name = f"Week {week_num} Learning Notes"
    existing = find_assignment(name, existing_assignments)
    if existing:
        print(f"  [exists] {name} (id: {existing['id']})")
        return existing

    payload = {
        'assignment': {
            'name': name,
            'description': assignment_description(week_num, pdf_url),
            'points_possible': POINTS_PER_WEEK,
            'grading_type': 'points',
            'submission_types': ['online_upload'],
            'allowed_extensions': ['pdf'],
            'assignment_group_id': group_id,
            'published': False,
        }
    }
    due_at = DUE_DATES_UTC.get(week_num)
    if due_at:
        payload['assignment']['due_at'] = due_at

    assignment = canvas_request(
        'POST',
        f'courses/{course_id}/assignments',
        token, base_url,
        payload
    )
    due_note = due_at if due_at else "no due date set (see script docstring)"
    print(f"  [created] {name} (id: {assignment['id']}) — {due_note}")
    return assignment


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/create_learning_notes_group.py <target>")
        print("  e.g.: python3 scripts/create_learning_notes_group.py hybrid")
        sys.exit(1)
    target_name = sys.argv[1]

    cfg = get_config(target_name)
    token = cfg['CANVAS_TOKEN']
    base_url = cfg['CANVAS_BASE_URL']
    course_id = cfg['CANVAS_COURSE_ID']

    pdf_url = cfg['TARGET'].get('multipage_pdf_url')
    if not pdf_url:
        print(f"  [warn] no multipage_pdf_url set for target '{target_name}' -- "
              f"assignment descriptions will reference the doc without a direct link. "
              f"Run scripts/upload_multipage_pdf_to_canvas.py against this target first.")

    print(f"Target: {target_name} (course {course_id})")
    print(f"Checking for the '{GROUP_NAME}' assignment group in course {course_id}...")
    group = ensure_group(token, base_url, course_id)

    print(f"\nChecking for the 15 weekly Learning Notes assignments...")
    existing_assignments = paginated_get(f'courses/{course_id}/assignments?per_page=100', token, base_url)

    created_or_found = []
    for week_num in WEEKS:
        a = ensure_week_assignment(week_num, group['id'], token, base_url, course_id, existing_assignments, pdf_url)
        created_or_found.append(a)

    print(f"\nSetting the group's drop_lowest rule now that assignments exist...")
    set_group_drop_rule(group['id'], token, base_url, course_id)

    print(f"\nDone. {len(created_or_found)}/15 Learning Notes assignments exist, "
          f"all as unpublished drafts in the '{GROUP_NAME}' group (drop_lowest={DROP_LOWEST}).")
    print("\nNext steps:")
    print("  1. Review each assignment in Canvas; add it to the matching week's Module.")
    print("  2. Week 15 has no due date set — confirm the actual due date/time for the")
    print("     Nov 30-Dec 4 window (it doesn't follow the usual Sunday pattern) and set it by hand.")
    print("  3. Publish each assignment once its week's content is ready.")


if __name__ == '__main__':
    main()
