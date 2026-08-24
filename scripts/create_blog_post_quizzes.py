#!/usr/bin/env python3
"""
create_blog_post_quizzes.py — Create the 14 weekly "Blog Post" declaration
quizzes for BIOL 1113 (Weeks 2-15) via the Canvas API, assigned to the
"Blog Posts" assignment group.

Each week's blog post is graded via a short quiz rather than a file
upload, since the actual deliverable is a public post on the student's
own blog, not something uploaded to Canvas:

  Q1 (all points): True/False -- student affirms they wrote and
     published this week's post.

The quiz description includes a [PLACEHOLDER] paragraph for that week's
specific blog topic. This script deliberately does NOT invent that
content -- Dr. Wiggins is particular about what each week's post should
connect to, and CLAUDE.md's own topic table has already drifted out of
sync with earlier drafts once this semester. Replace the placeholder
paragraph with the real prompt before publishing each week's quiz.

This script is idempotent: it looks up the "Blog Posts" group and each
week's quiz by name before creating anything, so re-running it after
partial completion (or after fixing a placeholder) won't create
duplicates.

What this script does:
  - Finds or creates a Canvas Assignment Group named "Blog Posts"
  - Sets a drop_lowest = 4 rule on that group (best 10 of 14 weeks
    count, 16 pts/week x 14 weeks = 224 pts available, need 168 --
    matches CLAUDE.md / syllabus.html)
  - Finds or creates 14 quizzes, "Week 2 Blog Post" ... "Week 15 Blog
    Post", each worth 16 points, one True/False question, assigned to
    the group, created as UNPUBLISHED drafts

Due dates: set for Weeks 2-14 (Sunday 11:59 PM Central, same dates used
by create_learning_notes_group.py). Week 15 is left WITHOUT a due date,
same reasoning as Learning Notes -- "Nov 30-Dec 4" breaks the normal
Monday-Sunday week pattern; set it by hand once Jodie confirms it.

Usage:
  python3 scripts/create_blog_post_quizzes.py <target>
  python3 scripts/create_blog_post_quizzes.py sandbox

  <target> is looked up in canvas_targets.py for course_id/base_url,
  same pattern as build/build.sh and upload_to_canvas.py. Intended for
  "sandbox" and "live" only -- the hybrid course has no Blog Posts
  group (Small Group Participation replaces it there).

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

GROUP_NAME = "Blog Posts"
POINTS_PER_WEEK = 16
DROP_LOWEST = 4
WEEKS = list(range(2, 16))  # 2..15

# Human-readable due-date labels, Sunday 11:59 PM Central of that week --
# same source dates as create_learning_notes_group.py's DUE_DATES_UTC.
DUE_DATE_LABELS = {
    2:  "August 30, 2026",
    3:  "September 6, 2026",
    4:  "September 13, 2026",
    5:  "September 20, 2026",
    6:  "September 27, 2026",
    7:  "October 4, 2026",
    8:  "October 11, 2026",
    9:  "October 18, 2026",
    10: "October 25, 2026",
    11: "November 1, 2026",
    12: "November 8, 2026",
    13: "November 15, 2026",
    14: "November 22, 2026",
    15: None,  # Nov 30-Dec 4 doesn't fit the pattern -- set by hand
}

# UTC ISO8601 due_at, computed from the labels above (11:59 PM Central,
# with proper DST handling for the Nov 1 fall-back).
DUE_DATES_UTC = {
    2:  "2026-08-31T04:59:00Z",
    3:  "2026-09-07T04:59:00Z",
    4:  "2026-09-14T04:59:00Z",
    5:  "2026-09-21T04:59:00Z",
    6:  "2026-09-28T04:59:00Z",
    7:  "2026-10-05T04:59:00Z",
    8:  "2026-10-12T04:59:00Z",
    9:  "2026-10-19T04:59:00Z",
    10: "2026-10-26T04:59:00Z",
    11: "2026-11-02T05:59:00Z",   # DST ends this day
    12: "2026-11-09T05:59:00Z",
    13: "2026-11-16T05:59:00Z",
    14: "2026-11-23T05:59:00Z",
    15: None,
}


def quiz_description(week_num, course_id):
    due_label = DUE_DATE_LABELS[week_num]
    due_line = f"Due Sunday, {due_label} at 11:59 PM" if due_label else "Due date TBD"
    return f"""<p><strong>Week {week_num} Blog Post</strong> &middot; {due_line}</p>

<hr />

<p><strong>What this quiz is for:</strong> This quiz confirms that you wrote and published this week's blog post. It is not graded on your answer here &mdash; it is graded on whether the post itself is live, public, on your blog.</p>

<p><strong>[PLACEHOLDER &mdash; Week {week_num} blog post topic]</strong><br />
Before publishing this quiz, replace this paragraph with what this week's post should be about &mdash; the specific connection to this week's biology content you want students to make. See the <a href="/courses/{course_id}/pages/blog-setup">Blog Setup &amp; Guidelines</a> page for the general requirements every post must meet (length, tone, sourcing, internet safety).
</p>

<p style="color: #57606a; font-size: 18px;"><em>Blog posts are spot-checked. Submitting this declaration falsely is an academic integrity violation.</em></p>"""


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
    target = get_target(target_name)
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
# Group + quizzes
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
    count, so the rule has to be applied after the 14 quizzes exist."""
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


def find_quiz(title, existing_quizzes):
    for q in existing_quizzes:
        if q['title'] == title:
            return q
    return None


def touch_quiz_points(quiz_id, expected_points, token, base_url, course_id):
    """Canvas doesn't recompute a quiz's points_possible from its questions
    until the quiz itself is re-saved -- a bare POST of questions leaves
    points_possible null (and the paired assignment's points_possible null
    too), which is wrong in the gradebook and breaks drop_lowest math. A
    no-op PUT forces the recalculation. Only touches it if it's actually
    out of sync, so this is safe to call on every quiz, every run."""
    quiz = canvas_request('GET', f'courses/{course_id}/quizzes/{quiz_id}', token, base_url)
    if quiz.get('points_possible') == expected_points:
        return
    canvas_request(
        'PUT', f'courses/{course_id}/quizzes/{quiz_id}', token, base_url,
        {'quiz': {'notify_of_update': False}}
    )
    print(f"    [fixed] points_possible was {quiz.get('points_possible')!r}, now {expected_points}")


def ensure_week_quiz(week_num, group_id, token, base_url, course_id, existing_quizzes):
    title = f"Week {week_num} Blog Post"
    existing = find_quiz(title, existing_quizzes)
    if existing:
        print(f"  [exists] {title} (id: {existing['id']})")
        touch_quiz_points(existing['id'], POINTS_PER_WEEK, token, base_url, course_id)
        return existing['id'], title

    quiz_payload = {
        'quiz': {
            'title': title,
            'description': quiz_description(week_num, course_id),
            'quiz_type': 'assignment',
            'assignment_group_id': group_id,
            'points_possible': POINTS_PER_WEEK,
            'allowed_attempts': 2,
            'published': False,
            'show_correct_answers': False,
            'shuffle_answers': False,
            'time_limit': None,
        }
    }
    due_at = DUE_DATES_UTC.get(week_num)
    if due_at:
        quiz_payload['quiz']['due_at'] = due_at

    quiz = canvas_request('POST', f'courses/{course_id}/quizzes', token, base_url, quiz_payload)
    quiz_id = quiz['id']

    canvas_request('POST', f'courses/{course_id}/quizzes/{quiz_id}/questions', token, base_url, {
        'question': {
            'question_name': 'Completion Declaration',
            'question_text': 'I affirm that I completed the above blog post and published it to my blog.',
            'question_type': 'true_false_question',
            'points_possible': POINTS_PER_WEEK,
            'answers': [
                {'text': 'True',  'weight': 100},
                {'text': 'False', 'weight': 0},
            ],
        }
    })

    touch_quiz_points(quiz_id, POINTS_PER_WEEK, token, base_url, course_id)

    due_note = due_at if due_at else "no due date set (see script docstring)"
    print(f"  [created] {title} (id: {quiz_id}) — {due_note}")
    return quiz_id, title


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/create_blog_post_quizzes.py <target>")
        print("  e.g.: python3 scripts/create_blog_post_quizzes.py sandbox")
        sys.exit(1)

    target_name = sys.argv[1]
    cfg = get_config(target_name)
    token     = cfg['CANVAS_TOKEN']
    base_url  = cfg['CANVAS_BASE_URL']
    course_id = cfg['CANVAS_COURSE_ID']

    print(f"Target: {target_name} (course {course_id})\n")

    group = ensure_group(token, base_url, course_id)
    group_id = group['id']

    existing_quizzes = paginated_get(f'courses/{course_id}/quizzes?per_page=100', token, base_url)

    created = []
    for week_num in WEEKS:
        try:
            quiz_id, title = ensure_week_quiz(week_num, group_id, token, base_url, course_id, existing_quizzes)
            created.append((week_num, quiz_id, title))
        except Exception as e:
            print(f"  [error]   Week {week_num}: {e}")

    if len(created) >= DROP_LOWEST:
        set_group_drop_rule(group_id, token, base_url, course_id)
    else:
        print(f"  [skip] drop_lowest not set -- fewer than {DROP_LOWEST} quizzes exist yet")

    print(f"\nDone. {len(created)}/{len(WEEKS)} quizzes present, as unpublished drafts.")
    print("\nNext steps:")
    print("  1. In Canvas > Assignments, find the 'Blog Posts' group.")
    print("  2. Before publishing each week's quiz, open it and replace the")
    print("     [PLACEHOLDER] paragraph with that week's specific blog topic.")
    print("  3. Publish when you're ready for students to see it.")


if __name__ == '__main__':
    main()
