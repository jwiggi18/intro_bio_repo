#!/usr/bin/env python3
"""
patch_blog_url_questions.py — One-off patch: fix the "Blog URL 1" / "Blog
URL 2" questions on the Week 3-15 "Blog Comment Declaration" quizzes.

Bug: create_declaration_quizzes.py created these two questions as
`short_answer_question` (Canvas's auto-graded fill-in-the-blank type)
without an `answers` list. Canvas grades short_answer_question by matching
student text against that list; with an empty list, every submission is
marked incorrect regardless of what the student typed. Confirmed against
live Canvas data on the `live` target's Week 2 quiz (Sep 1, 2026):
question definition and 35 completed submissions both show
`answers: []`, `correct: false`.

Fix: change question_type to `essay_question` (free-response, never
auto-graded, so it can't show a false "incorrect"). Both questions are
worth 0 points, so this changes no scores.

Scope: WEEKS 3-15 only, both `sandbox` and `live` targets. Week 2 is
deliberately EXCLUDED -- Jodie asked to hold off on it since it already
has real student submissions (Sep 1, 2026 decision); handle it separately
if/when she decides to. Hybrid has no Blog Comments group, so it's not a
target here.

Safety:
  - Refuses to touch Week 2 even if asked (hardcoded exclusion).
  - For each week, first fetches that quiz's submission count and
    ABORTS (prints and skips) if it finds any completed submissions,
    rather than assuming due dates protect us.
  - --dry-run prints exactly what would change without writing anything.

Usage:
  python3 scripts/patch_blog_url_questions.py sandbox --dry-run
  python3 scripts/patch_blog_url_questions.py sandbox
  python3 scripts/patch_blog_url_questions.py live --dry-run
  python3 scripts/patch_blog_url_questions.py live

Requirements:
  - .env with CANVAS_TOKEN (repo root)
  - canvas_targets.py has the target's course_id/base_url filled in
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target  # noqa: E402

WEEKS = list(range(3, 16))  # 3..15 -- Week 2 deliberately excluded
TARGET_QUESTION_NAMES = {"Blog URL 1", "Blog URL 2"}


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env file not found.")
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip()
    return env


def canvas_request(method, path, token, base_url, data=None):
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"  HTTP {e.code} on {method} {url}")
        print(f"  {err_body[:400]}")
        raise


def paginated_get(path, token, base_url):
    results = []
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            results.extend(json.loads(resp.read().decode("utf-8")))
            link = resp.headers.get("Link", "")
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.split(";")[0].strip().strip("<>")
    return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    target_name = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if target_name == "week2" or "week2" in sys.argv:
        print("Refusing: Week 2 is explicitly excluded from this script.")
        sys.exit(1)

    env = load_env()
    token = env.get("CANVAS_TOKEN")
    if not token or "your_" in token:
        print("Error: CANVAS_TOKEN missing or unfilled in .env")
        sys.exit(1)

    target = get_target(target_name)
    base_url = target["base_url"]
    course_id = target["course_id"]

    print(f"=== Target: {target_name} (course {course_id}) -- dry_run={dry_run} ===\n")

    quizzes = paginated_get(f"courses/{course_id}/quizzes?per_page=100", token, base_url)
    by_title = {q["title"]: q for q in quizzes}

    for week in WEEKS:
        title = f"Week {week} Blog Comment Declaration"
        quiz = by_title.get(title)
        if not quiz:
            print(f"[skip] {title}: quiz not found")
            continue

        quiz_id = quiz["id"]

        subs = canvas_request(
            "GET", f"courses/{course_id}/quizzes/{quiz_id}/submissions?per_page=100",
            token, base_url,
        )
        completed = [
            s for s in subs.get("quiz_submissions", [])
            if s.get("workflow_state") == "complete"
        ]
        if completed:
            print(f"[ABORT] {title}: has {len(completed)} completed submission(s) -- "
                  f"skipping to be safe, this script only expects clean weeks.")
            continue

        questions = canvas_request(
            "GET", f"courses/{course_id}/quizzes/{quiz_id}/questions",
            token, base_url,
        )
        to_patch = [q for q in questions if q.get("question_name") in TARGET_QUESTION_NAMES]

        if not to_patch:
            print(f"[skip] {title}: no 'Blog URL 1'/'Blog URL 2' questions found")
            continue

        for q in to_patch:
            current_type = q.get("question_type")
            if current_type == "essay_question":
                print(f"  [already fixed] {title} -- {q['question_name']} (id {q['id']})")
                continue
            print(f"  [{'DRY-RUN ' if dry_run else ''}patch] {title} -- {q['question_name']} "
                  f"(id {q['id']}): {current_type} -> essay_question")
            if not dry_run:
                canvas_request(
                    "PUT",
                    f"courses/{course_id}/quizzes/{quiz_id}/questions/{q['id']}",
                    token, base_url,
                    {
                        "question": {
                            "question_name": q["question_name"],
                            "question_text": q["question_text"],
                            "question_type": "essay_question",
                            "points_possible": q.get("points_possible", 0),
                        }
                    },
                )

    print("\nDone." + (" (dry run -- nothing written)" if dry_run else ""))


if __name__ == "__main__":
    main()
