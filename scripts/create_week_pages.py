#!/usr/bin/env python3
"""
create_week_pages.py — Generate weekNN/week.html for all 15 weeks.

Creates one comprehensive HTML page per week (replacing the old three-file
overview/materials/assignments structure). Fills in all mechanical data
(dates, Learning Notes links, test reminders) and leaves content
placeholders for the instructor.

Usage:
  python3 scripts/create_week_pages.py          # all 15 weeks
  python3 scripts/create_week_pages.py 1        # single week
  python3 scripts/create_week_pages.py 1 4      # range (inclusive)

Existing weekNN/week.html files are overwritten.
Old overview.html / materials.html / assignments.html are removed if present.

Note on the Assignments section: it links name -> Canvas assignment/quiz
only (see templates/week.html for why — points/descriptions/due dates live
on the Canvas item itself now). LEARNING_NOTES_ASSIGNMENT_IDS below maps
each week to its real Canvas assignment id (created Aug 11, 2026 via
scripts/create_learning_notes_group.py). Blog Post and Test items don't
have Canvas assignments yet, so they're generated as unlinked placeholders
-- fill in the real id once each one is created in Canvas.
"""

import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
TEMPLATE = REPO / "templates" / "week.html"

# ── Canvas config (for building assignment URLs; falls back to a
#    placeholder if .env isn't present, e.g. in a fresh clone) ─────────────

def load_canvas_config():
    env_path = REPO / ".env"
    if not env_path.exists():
        return None, None
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        env[key.strip()] = val.strip()
    return env.get('CANVAS_BASE_URL'), env.get('CANVAS_COURSE_ID')


CANVAS_BASE_URL, CANVAS_COURSE_ID = load_canvas_config()

# ── Week data ──────────────────────────────────────────────────────────────
# (num, topic, date_range, due_date, test_num, test_coverage, test_open_date, is_blog_week)

WEEKS = [
    ( 1, "Learning and the Nature of Science",       "August 17–23, 2026",       "August 23",    None, None, None,           False),
    ( 2, "Biological Molecules",                      "August 24–30, 2026",       "August 30",    None, None, None,           True),
    ( 3, "Cells and Biological Organization",         "August 31–September 6, 2026", "September 6", None, None, None,        True),
    ( 4, "Biological Membranes and Cell Signaling",   "September 7–13, 2026",     "September 13", None, None, None,          True),
    ( 5, "DNA and Genetic Variation",                 "September 14–20, 2026",    "September 20", 1, "Weeks 1–4", "September 14", True),
    ( 6, "Gene Expression",                           "September 21–27, 2026",    "September 27", None, None, None,          True),
    ( 7, "Cell Division",                             "September 28–October 4, 2026", "October 4", None, None, None,         True),
    ( 8, "Inheritance",                               "October 5–11, 2026",       "October 11",   None, None, None,          True),
    ( 9, "Evolution and Natural Selection",           "October 12–18, 2026",      "October 18",   2, "Weeks 5–8", "October 12", True),
    (10, "Population Genetics and Speciation",        "October 19–25, 2026",      "October 25",   None, None, None,          True),
    (11, "Cellular Respiration",                      "October 26–November 1, 2026", "November 1", None, None, None,         True),
    (12, "Photosynthesis",                            "November 2–8, 2026",       "November 8",   None, None, None,          True),
    (13, "Biological Systems",                        "November 9–15, 2026",      "November 15",  3, "Weeks 9–12", "November 9", True),
    (14, "Ecosystems",                                "November 16–22, 2026",     "November 22",  None, None, None,          True),
    (15, "Human Impacts on Biological Systems",       "November 30–December 6, 2026", "December 6", None, None, None,        True),
]

OLD_FILES = ["overview.html", "materials.html", "assignments.html"]

# Learning Notes Canvas assignment ids, one per week (course 215536 sandbox,
# created Aug 11, 2026). Update this map if the assignments are ever
# recreated (a course copy to a new Canvas course, for instance, will
# assign new ids -- see the note in templates/week.html about that).
LEARNING_NOTES_ASSIGNMENT_IDS = {
    1: 2673768,  2: 2673769,  3: 2673770,  4: 2673771,  5: 2673772,
    6: 2673773,  7: 2673774,  8: 2673775,  9: 2673776,  10: 2673777,
    11: 2673778, 12: 2673779, 13: 2673780, 14: 2673781, 15: 2673782,
}


def canvas_assignment_url(assignment_id):
    if not (CANVAS_BASE_URL and CANVAS_COURSE_ID and assignment_id):
        return None
    return f"{CANVAS_BASE_URL.rstrip('/')}/courses/{CANVAS_COURSE_ID}/assignments/{assignment_id}"


# ── Assignments section ─────────────────────────────────────────────────────

def assignments_list(week_num, is_blog_week, test_num, test_coverage):
    items = []

    ln_url = canvas_assignment_url(LEARNING_NOTES_ASSIGNMENT_IDS.get(week_num))
    if ln_url:
        items.append(f'    <li><a href="{ln_url}">Learning Notes</a></li>')
    else:
        items.append('    <li class="unlinked">Learning Notes</li>')

    if is_blog_week:
        # No Canvas assignment for the blog post submission itself yet --
        # unlinked until one exists. (Blog Comment Declaration quizzes DO
        # already exist in Canvas for weeks 2-15 but aren't wired in here;
        # see SESSION_NOTES.md.)
        items.append('    <li class="unlinked">Blog Post</li>')

    if test_num:
        # No Canvas assignment for tests yet either.
        items.append(f'    <li class="unlinked">Test {test_num} (covers {test_coverage})</li>')

    return "\n".join(items)


# ── Generate one week ──────────────────────────────────────────────────────

def generate(num, topic, date_range, due_date, test_num, test_coverage, test_open, is_blog_week):
    template = TEMPLATE.read_text(encoding="utf-8")

    # Mechanical substitutions
    replacements = {
        "{{WEEK_NUM}}":    f"{num:02d}",
        "{{WEEK_TOPIC}}":  topic,
        "{{WEEK_DATES}}":  date_range,
        "{{DUE_DATE}}":    due_date,
    }
    for key, val in replacements.items():
        template = template.replace(key, val)

    # Assignments list replaces the whole {{OPTIONAL_TEST_LINK}} placeholder
    # AND the always-present Learning Notes <li> the template ships with,
    # since this script builds the full list itself (real Learning Notes
    # link, blog/test placeholders as applicable).
    template = template.replace(
        '    <!-- Learning Notes — present every week, do not remove -->\n'
        '    <li><a href="{{LEARNING_NOTES_URL}}">Learning Notes</a></li>',
        assignments_list(num, is_blog_week, test_num, test_coverage)
    )
    template = template.replace("    {{OPTIONAL_TEST_LINK}}\n", "")

    return template


def main():
    if not TEMPLATE.exists():
        print(f"Error: template not found at {TEMPLATE}")
        sys.exit(1)

    if not (CANVAS_BASE_URL and CANVAS_COURSE_ID):
        print("Note: .env not found or incomplete -- Learning Notes links will be left")
        print("as unlinked placeholders instead of real Canvas URLs.\n")

    # Parse CLI args for week range
    args = sys.argv[1:]
    if not args:
        nums = list(range(1, 16))
    elif len(args) == 1:
        nums = [int(args[0])]
    elif len(args) == 2:
        nums = list(range(int(args[0]), int(args[1]) + 1))
    else:
        print("Usage: create_week_pages.py [start [end]]")
        sys.exit(1)

    week_map = {row[0]: row for row in WEEKS}

    for num in nums:
        if num not in week_map:
            print(f"  SKIP  week {num} — not in WEEKS table")
            continue

        row = week_map[num]
        folder = REPO / f"week{num:02d}"
        folder.mkdir(exist_ok=True)

        # Stub out old three-file structure so they're ignored by the build
        # (build/inline_css.py now only processes week.html)
        stub = "<!-- deprecated: this file replaced by week.html -->\n"
        for old in OLD_FILES:
            old_path = folder / old
            if old_path.exists():
                old_path.write_text(stub, encoding="utf-8")
                print(f"  stub  week{num:02d}/{old}")

        # Write new single page
        html = generate(*row)
        out = folder / "week.html"
        out.write_text(html, encoding="utf-8")

        test_label = f"  ← Test {row[4]} opens" if row[4] else ""
        print(f"  OK    week{num:02d}/week.html  (due {row[3]}){test_label}")

    print(f"\nDone. Run 'bash build/build.sh' to rebuild Canvas output.")


if __name__ == "__main__":
    main()
