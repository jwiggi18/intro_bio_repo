#!/usr/bin/env python3
"""
create_small_group_declarations.py -- Create the 90 (15 weeks x 6 sections)
"Small Group Declaration" quizzes for the BIOL 1113 hybrid course, each
restricted to a single course section and openable only during the last
10 minutes of that section's weekly 50-minute meeting.

Each quiz:
  - Belongs to the existing "Small Group Participation" assignment group
    (id 484125), worth 24 pts, matching the manually-graded assignments
    it replaces.
  - Has ONE true/false question: a self-declared attendance/participation
    affirmation (exact wording supplied by Jodie Wiggins, Aug 2026).
  - Has a unique 4-digit access_code (passcode), given verbally by GTA
    Claudia Goss near the end of each session.
  - Is visible ONLY to its one course section (only_visible_to_overrides +
    a single AssignmentOverride carrying that section's specific
    unlock_at/lock_at/due_at -- the last 10 minutes of its meeting).
  - allowed_attempts=1, time_limit=10 minutes, published=False (draft).

Calendar: Week 1 Monday = Aug 17, 2026. Weeks 1-14 follow consecutively.
Week 15 is NOT Nov 23 (that week is Fall Break, Nov 23-27) -- it resumes
Nov 30, so Week 15's Monday is Nov 30, 2026. Confirmed with Jodie Aug 2026.

Idempotent: looks up existing quizzes by title before creating, and
(re)applies only_visible_to_overrides + the section override even for
quizzes that already existed, so a partial/interrupted prior run is safe
to re-run.

Usage:
  python3 create_small_group_declarations.py            (dry run -- prints plan, no API calls)
  python3 create_small_group_declarations.py --live      (actually creates in Canvas)

Requires .env (CANVAS_TOKEN) and canvas_targets.py in the same directory.
"""
import sys
import json
import random
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
from canvas_targets import get_target

CENTRAL = ZoneInfo("America/Chicago")
GROUP_ID = 484125          # "Small Group Participation" assignment group, hybrid course
POINTS_PER_QUIZ = 24
BASE_MONDAY = datetime.date(2026, 8, 17)  # Week 1 Monday

SECTIONS = [
    {"crn": "70927", "section_id": 241419, "day": "Wed", "start": "15:30", "end": "16:20", "room": "PS 301B"},
    {"crn": "70928", "section_id": 241423, "day": "Fri", "start": "15:30", "end": "16:20", "room": "PS 301B"},
    {"crn": "70929", "section_id": 241422, "day": "Tue", "start": "12:00", "end": "12:50", "room": "NRD 305"},
    {"crn": "70930", "section_id": 241421, "day": "Thu", "start": "12:00", "end": "12:50", "room": "NRD 305"},
    {"crn": "70931", "section_id": 241420, "day": "Tue", "start": "15:00", "end": "15:50", "room": "CLB 319"},
    {"crn": "70932", "section_id": 241424, "day": "Thu", "start": "15:00", "end": "15:50", "room": "CLB 319"},
]
WEEKDAY_INDEX = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4}

DECLARATION_TEXT = (
    "I affirm that I attended my assigned small group session for "
    "<strong>the entirety of class time</strong>. I affirm that I "
    "<strong>fully participated</strong> in <strong>all</strong> activities. "
    "I affirm that I asked questions about concepts or procedures that I "
    "was unclear on."
)


def week_monday(week_num):
    if week_num == 15:
        return datetime.date(2026, 11, 30)  # Fall Break (Nov 23-27) pushes Week 15 past it
    return BASE_MONDAY + datetime.timedelta(weeks=week_num - 1)


def fmt12(hhmm):
    h, m = map(int, hhmm.split(":"))
    dt = datetime.time(h, m)
    return dt.strftime("%I:%M %p").lstrip("0")


def short_range(start_hhmm, end_hhmm):
    start_s = fmt12(start_hhmm)
    end_s = fmt12(end_hhmm)
    start_ampm = start_s.split()[-1]
    end_ampm = end_s.split()[-1]
    if start_ampm == end_ampm:
        start_s = start_s.split()[0]
    return f"{start_s}–{end_s}"


def local_dt(date_, hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime.datetime(date_.year, date_.month, date_.day, h, m, tzinfo=CENTRAL)


def to_utc_z(dt_local):
    return dt_local.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:00Z")


def build_plan():
    random.seed(20260815)  # deterministic, reproducible across dry-run and live-run
    used_codes = set()

    def gen_code():
        while True:
            code = f"{random.randint(0, 9999):04d}"
            if code not in used_codes:
                used_codes.add(code)
                return code

    rows = []
    for week in range(1, 16):
        monday = week_monday(week)
        for sec in SECTIONS:
            meeting_date = monday + datetime.timedelta(days=WEEKDAY_INDEX[sec["day"]])
            end_local = local_dt(meeting_date, sec["end"])
            unlock_local = end_local - datetime.timedelta(minutes=10)
            lock_local = end_local
            rows.append({
                "week": week,
                **sec,
                "meeting_date": meeting_date.isoformat(),
                "time_range": f"{sec['day']} {short_range(sec['start'], sec['end'])}",
                "unlock_local": unlock_local,
                "lock_local": lock_local,
                "unlock_utc": to_utc_z(unlock_local),
                "lock_utc": to_utc_z(lock_local),
                "passcode": gen_code(),
                "title": f"Week {week} Small Group Declaration — CRN {sec['crn']} ({sec['day']} {short_range(sec['start'], sec['end'])})",
            })
    return rows


def quiz_description(row):
    return f"""<p><strong>Week {row['week']} Small Group Declaration</strong> &middot; CRN {row['crn']} &middot; {row['time_range']}, {row['room']}</p>
<hr />
<p><strong>This quiz is only open during the last 10 minutes of your small group session</strong> ({row['unlock_local'].strftime('%-I:%M')}&ndash;{row['lock_local'].strftime('%-I:%M %p')} on {row['meeting_date']}). Claudia will give you the passcode in person near the end of class &mdash; this cannot be completed outside of class.</p>
<p>This quiz confirms your attendance and participation in this week's small group session. Submitting it falsely is an academic integrity violation and may be spot-checked.</p>"""


# ---------------------------------------------------------------------------
# Canvas API helpers (same pattern as the rest of the repo's scripts)
# ---------------------------------------------------------------------------

def load_env():
    env_path = Path(__file__).parent / ".env"
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
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"  HTTP {e.code} on {method} {url}\n  {err_body[:500]}")
        raise


def paginated_get(path, token, base_url):
    results = []
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"}
    while url:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as r:
            results.extend(json.loads(r.read().decode("utf-8")))
            link = r.headers.get("Link", "")
            next_url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>")
            url = next_url
    return results


def ensure_quiz(row, token, base_url, course_id, existing_by_title):
    title = row["title"]
    existing = existing_by_title.get(title)
    if existing:
        quiz_id = existing["id"]
        assignment_id = existing["assignment_id"]
        print(f"  [exists] {title} (quiz {quiz_id})")
    else:
        payload = {
            "quiz": {
                "title": title,
                "description": quiz_description(row),
                "quiz_type": "assignment",
                "assignment_group_id": GROUP_ID,
                "points_possible": POINTS_PER_QUIZ,
                "allowed_attempts": 1,
                "time_limit": 10,
                "access_code": row["passcode"],
                "published": False,
                "show_correct_answers": False,
                "shuffle_answers": False,
                "due_at": row["lock_utc"],
                "unlock_at": row["unlock_utc"],
                "lock_at": row["lock_utc"],
            }
        }
        quiz = canvas_request("POST", f"courses/{course_id}/quizzes", token, base_url, payload)
        quiz_id = quiz["id"]
        assignment_id = quiz["assignment_id"]

        canvas_request("POST", f"courses/{course_id}/quizzes/{quiz_id}/questions", token, base_url, {
            "question": {
                "question_name": "Attendance & Participation Declaration",
                "question_text": DECLARATION_TEXT,
                "question_type": "true_false_question",
                "points_possible": POINTS_PER_QUIZ,
                "answers": [
                    {"text": "True", "weight": 100},
                    {"text": "False", "weight": 0},
                ],
            }
        })
        # force points_possible recalculation (same fix used elsewhere in this repo)
        canvas_request("PUT", f"courses/{course_id}/quizzes/{quiz_id}", token, base_url,
                        {"quiz": {"notify_of_update": False}})
        print(f"  [created] {title} (quiz {quiz_id}, passcode {row['passcode']})")

    # Restrict visibility to this one section, every run (idempotent / safe to re-apply)
    canvas_request("PUT", f"courses/{course_id}/assignments/{assignment_id}", token, base_url,
                    {"assignment": {"only_visible_to_overrides": True}})

    existing_overrides = canvas_request(
        "GET", f"courses/{course_id}/assignments/{assignment_id}/overrides", token, base_url
    )
    has_override = any(o.get("course_section_id") == row["section_id"] for o in existing_overrides)
    if not has_override:
        canvas_request("POST", f"courses/{course_id}/assignments/{assignment_id}/overrides", token, base_url, {
            "assignment_override": {
                "course_section_id": row["section_id"],
                "title": f"CRN {row['crn']}",
                "due_at": row["lock_utc"],
                "unlock_at": row["unlock_utc"],
                "lock_at": row["lock_utc"],
            }
        })

    return quiz_id, assignment_id


def main():
    live = "--live" in sys.argv
    rows = build_plan()

    if not live:
        print(f"DRY RUN -- {len(rows)} quizzes planned, no API calls made.\n")
        for r in rows[:6]:
            print(f"  Wk{r['week']:>2} {r['crn']} {r['meeting_date']} {r['unlock_local'].strftime('%I:%M')}-{r['lock_local'].strftime('%I:%M %p')} code={r['passcode']}  {r['title']}")
        print("  ...")
        with open("plan.json", "w") as f:
            json.dump([{**r, "unlock_local": r["unlock_local"].isoformat(),
                        "lock_local": r["lock_local"].isoformat()} for r in rows], f, indent=2)
        print("\nWrote plan.json. Re-run with --live to create in Canvas.")
        return

    env = load_env()
    token = env["CANVAS_TOKEN"]
    target = get_target("hybrid")
    base_url = target["base_url"]
    course_id = target["course_id"]

    print(f"LIVE RUN -- target hybrid (course {course_id}), {len(rows)} quizzes\n")

    existing_quizzes = paginated_get(f"courses/{course_id}/quizzes?per_page=100", token, base_url)
    existing_by_title = {q["title"]: q for q in existing_quizzes}

    created = []
    for row in rows:
        try:
            quiz_id, assignment_id = ensure_quiz(row, token, base_url, course_id, existing_by_title)
            created.append({**row, "quiz_id": quiz_id, "assignment_id": assignment_id,
                             "html_url": f"{base_url}/courses/{course_id}/quizzes/{quiz_id}"})
        except Exception as e:
            print(f"  [error] Week {row['week']} CRN {row['crn']}: {e}")

    out = []
    for r in created:
        r2 = dict(r)
        r2["unlock_local"] = r["unlock_local"].isoformat()
        r2["lock_local"] = r["lock_local"].isoformat()
        out.append(r2)
    with open("created_quizzes.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nDone. {len(created)}/{len(rows)} quizzes present as unpublished drafts.")
    print("Wrote created_quizzes.json")


if __name__ == "__main__":
    main()
