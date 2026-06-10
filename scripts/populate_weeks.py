#!/usr/bin/env python3
"""
populate_weeks.py — Fill in mechanical placeholders across all 15 week folders.

What this script changes:
  overview.html    — removes/replaces {{OPTIONAL_HW_TASK}}, {{OPTIONAL_TEST_TASK}},
                     {{OPTIONAL_CONTEXT_PARAGRAPH}}
  assignments.html — fills {{DUE_DATE}}, removes {{OPTIONAL_HW_BLOCK}} and
                     {{OPTIONAL_WRITING_BLOCK}}, fills/removes {{OPTIONAL_TEST_BLOCK}}
  materials.html   — removes {{OPTIONAL_SUPPLEMENTAL_SECTION}}

What this script does NOT touch:
  - {{OBJECTIVE_*}} — biological content, left for Dr. Wiggins
  - {{VIDEO_*}} placeholders — content decisions
  - {{READING_*}} placeholders — content decisions
  - Any existing non-placeholder text

Run from the repo root:
  python3 scripts/populate_weeks.py
"""

from pathlib import Path

REPO = Path(__file__).parent.parent

# ── Week data ──────────────────────────────────────────────────────────────
# (num, topic, due_date, test_num, test_coverage, test_open_date)
# test_num=None means no test opens this week

WEEKS = [
    ( 1, "Learning and the Nature of Science",       "August 23",    None, None, None),
    ( 2, "Biological Molecules",                      "August 30",    None, None, None),
    ( 3, "Cells and Biological Organization",         "September 6",  None, None, None),
    ( 4, "Biological Membranes and Cell Signaling",   "September 13", None, None, None),
    ( 5, "DNA and Genetic Variation",                 "September 20", 1,    "Weeks 1–4", "September 14"),
    ( 6, "Gene Expression",                           "September 27", None, None, None),
    ( 7, "Cell Division",                             "October 4",    None, None, None),
    ( 8, "Inheritance",                               "October 11",   None, None, None),
    ( 9, "Evolution and Natural Selection",           "October 18",   2,    "Weeks 5–8", "October 12"),
    (10, "Population Genetics and Speciation",        "October 25",   None, None, None),
    (11, "Cellular Respiration",                      "November 1",   None, None, None),
    (12, "Photosynthesis",                            "November 8",   None, None, None),
    (13, "Biological Systems",                        "November 15",  3,    "Weeks 9–12", "November 9"),
    (14, "Ecosystems",                                "November 22",  None, None, None),
    (15, "Human Impacts on Biological Systems",       "December 6",   None, None, None),
]

# ── HTML snippets ──────────────────────────────────────────────────────────

def test_overview_task(test_num, coverage):
    return f"""    <li>
      <span class="task-icon">📝</span>
      <div>
        <div class="task-label">Schedule and complete Test {test_num}</div>
        <div class="task-detail">Test {test_num} opens this week and covers {coverage}. Schedule your appointment through <strong>Measure Learning&nbsp;/ ProctorU</strong> or at a registered testing center. Do not wait — testing centers fill up quickly.</div>
      </div>
    </li>"""


def test_assignment_block(test_num, coverage, open_date):
    return f"""  <div class="assignment-block">
    <h3>Test {test_num} <span class="points-badge">150 pts</span></h3>
    <p>Test {test_num} covers {coverage}. You must complete it through <strong>Measure Learning&nbsp;/ ProctorU</strong> or at a registered testing center. You schedule the appointment yourself — it does not have to be taken on a specific day within the window.</p>
    <p><strong>Window opens:</strong> {open_date}. Close date: TBD — watch for a Canvas announcement.</p>
    <p>Schedule your testing appointment early. Testing centers fill up, especially near the window deadline.</p>
  </div>"""


COMMENT_HW_TASK = \
    "<!-- HW task: add <li> here when a homework assignment is scheduled for this week -->"

COMMENT_CONTEXT = \
    "<!-- OPTIONAL: add 1–2 sentences here framing why this week's topic matters -->"

COMMENT_HW_BLOCK = \
    "<!-- HW assignment block: add when a homework assignment is scheduled for this week.\n" \
    "     See template comment below for the markup to use. -->"

COMMENT_WRITING_BLOCK = \
    "<!-- Writing assignment block: add for the two writing assignment weeks only.\n" \
    "     See template comment below for the markup to use. -->"

COMMENT_TEST_BLOCK = \
    "<!-- No test opens this week. Remove this comment when adding a test block. -->"

COMMENT_SUPPLEMENTAL = \
    "<!-- Supplemental resources: add 1–2 optional external resources if desired.\n" \
    "     Keep this section short — do not let it compete with required content. -->"


# ── Process each week ──────────────────────────────────────────────────────

def process_overview(path, test_num, test_coverage):
    text = path.read_text(encoding='utf-8')

    # {{OPTIONAL_HW_TASK}}
    text = text.replace("    {{OPTIONAL_HW_TASK}}\n", f"    {COMMENT_HW_TASK}\n")

    # {{OPTIONAL_TEST_TASK}}
    if test_num:
        replacement = test_overview_task(test_num, test_coverage) + "\n"
    else:
        replacement = f"    <!-- No test opens this week -->\n"
    text = text.replace("    {{OPTIONAL_TEST_TASK}}\n", replacement)

    # {{OPTIONAL_CONTEXT_PARAGRAPH}}
    text = text.replace("{{OPTIONAL_CONTEXT_PARAGRAPH}}", COMMENT_CONTEXT)

    path.write_text(text, encoding='utf-8')


def process_assignments(path, due_date, test_num, test_coverage, test_open_date):
    text = path.read_text(encoding='utf-8')

    # {{DUE_DATE}}
    text = text.replace("{{DUE_DATE}}", due_date)

    # {{OPTIONAL_HW_BLOCK}}
    text = text.replace("  {{OPTIONAL_HW_BLOCK}}\n", f"  {COMMENT_HW_BLOCK}\n")

    # {{OPTIONAL_WRITING_BLOCK}}
    text = text.replace("  {{OPTIONAL_WRITING_BLOCK}}\n", f"  {COMMENT_WRITING_BLOCK}\n")

    # {{OPTIONAL_TEST_BLOCK}}
    if test_num:
        replacement = test_assignment_block(test_num, test_coverage, test_open_date) + "\n"
    else:
        replacement = f"  {COMMENT_TEST_BLOCK}\n"
    text = text.replace("  {{OPTIONAL_TEST_BLOCK}}\n", replacement)

    path.write_text(text, encoding='utf-8')


def process_materials(path):
    text = path.read_text(encoding='utf-8')
    text = text.replace("  {{OPTIONAL_SUPPLEMENTAL_SECTION}}\n",
                        f"  {COMMENT_SUPPLEMENTAL}\n")
    path.write_text(text, encoding='utf-8')


def main():
    changed = 0
    for (num, topic, due_date, test_num, test_coverage, test_open_date) in WEEKS:
        folder = REPO / f"week{num:02d}"
        if not folder.exists():
            print(f"  SKIP  {folder.name} — folder not found")
            continue

        overview    = folder / "overview.html"
        materials   = folder / "materials.html"
        assignments = folder / "assignments.html"

        for f in [overview, materials, assignments]:
            if not f.exists():
                print(f"  SKIP  {f} — file not found")

        process_overview(overview, test_num, test_coverage)
        process_materials(materials)
        process_assignments(assignments, due_date, test_num, test_coverage, test_open_date)

        test_label = f"(Test {test_num} opens)" if test_num else ""
        print(f"  OK    week{num:02d}  due {due_date:<14}  {test_label}")
        changed += 3

    print(f"\n{changed} files updated.")


if __name__ == "__main__":
    main()
