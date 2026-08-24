#!/usr/bin/env python3
"""
create_hybrid_week_pages.py — Derive hybrid/weekNN/week.html from the
existing root-level weekNN/week.html for all 15 weeks.

Why this exists: the hybrid course (lecture + GTA-led small group, no blog
posts/comments) is genuinely different content, not just a different Canvas
id — see canvas_targets.py's "hybrid" entry and its content_root field. But
its videos, readings, and objectives are otherwise the SAME as the root
course, so this script transforms the current root week page into its
hybrid equivalent rather than requiring a hand-maintained duplicate that
would drift the moment weeks 1-4's real content changes.

Three mechanical transforms, run against each weekNN/week.html:

  1. The first video slot (the .video-card with id="video-1", together with
     its preceding "View and engage with:" material-label) is replaced with
     a .lecture-notice block: that content is covered live at the Monday
     lecture (NRC 106, 3:30-4:20 PM) instead of watched online. The video's
     original title becomes the lecture's listed topic. Per Jodie's
     decision (Aug 13, 2026), no focus questions are carried over — just
     the attendance notice.

  2. In the Assignments list: any Blog Post / Blog Comment Declaration <li>
     (linked or unlinked) is removed, and a Small Group Participation link
     is inserted right after Learning Notes. The Learning Notes <li> itself
     is normalized to the {{LEARNING_NOTES_URL}} placeholder regardless of
     what the source had — weeks 5-15 currently carry a baked-in SANDBOX
     Learning Notes URL (a pre-existing bug: create_week_pages.py resolves
     it from .env at generation time instead of leaving the placeholder
     other files use — see SESSION_NOTES.md), which would be wrong for the
     hybrid course. Everything else (readings, other videos, Syllabus Quiz,
     Test placeholders) is left untouched.

  3. A "Small Group" section is inserted right before Learning Materials
     (i.e. right after Objectives): a short paragraph directing students to
     attend their assigned small group meeting and complete their
     declaration, with "your assigned small group meeting" linking to the
     hybrid course's "Small Groups" wiki page (added Aug 14, 2026 at
     Jodie's request, once that page existed). Uses {{COURSE_ID}} rather
     than a hardcoded course id, same as every other Canvas link in this
     repo, even though hybrid only ever resolves against one course — see
     hybrid/homepage.html for the same convention.

Usage:
  python3 scripts/create_hybrid_week_pages.py          # all 15 weeks
  python3 scripts/create_hybrid_week_pages.py 1        # single week
  python3 scripts/create_hybrid_week_pages.py 1 4      # range (inclusive)

Source weekNN/week.html files are NOT modified. Existing hybrid/weekNN/
week.html files are overwritten (re-run this after editing root week
content to keep hybrid in sync).
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

VIDEO1_BLOCK_RE = re.compile(
    r'  <p class="material-label">View and engage with:</p>\s*\n'
    r'  <div class="video-card" id="video-1">.*?\n  </div>',
    re.DOTALL
)

VIDEO1_TITLE_RE = re.compile(
    r'<div class="video-title"><strong>(.*?)</strong></div>', re.DOTALL
)

LI_RE = re.compile(r'    <li[^>]*>.*?</li>', re.DOTALL)

LEARNING_NOTES_LI = '    <li><a href="{{LEARNING_NOTES_URL}}">Learning Notes</a></li>'
SMALL_GROUP_LI = '    <li><a href="{{SMALL_GROUP_URL}}">Small Group Participation</a></li>'

LEARNING_MATERIALS_START_RE = re.compile(r'  <!-- Learning Materials start -->')

SMALL_GROUP_SECTION = (
    '  <!-- Small Group start -->\n\n'
    '  <h2 class="section-heading" id="small-group">Small Group</h2>\n\n'
    '  <p>Attend and participate in '
    '<a href="/courses/{{COURSE_ID}}/pages/small-groups">your assigned small group meeting</a> '
    'and complete your declaration.</p>\n\n'
    '  <!-- Small Group end -->\n\n\n'
)


def lecture_notice_block(topic):
    return (
        '  <!-- Lecture (in-person) start -->\n\n'
        '  <div class="lecture-notice" id="week-lecture">\n\n'
        '    <div class="lecture-label">In-Person Lecture</div>\n\n'
        '    <div class="lecture-details">Come to lecture in NRC 106, 3:30&ndash;4:20 PM.</div>\n\n'
        f'    <div class="lecture-topic">Topic: <strong>{topic}</strong></div>\n\n'
        '  </div>\n\n'
        '  <!-- Lecture (in-person) end -->'
    )


def transform_video1(html):
    m = VIDEO1_BLOCK_RE.search(html)
    if not m:
        print("    [warn] no video-1 block found — page left unchanged in this step")
        return html
    title_m = VIDEO1_TITLE_RE.search(m.group(0))
    topic = title_m.group(1) if title_m else "{{VIDEO_1_TITLE}}"
    return html[:m.start()] + lecture_notice_block(topic) + html[m.end():]


def transform_assignments(html):
    ul_m = re.search(r'<ul class="assignment-links">(.*?)</ul>', html, re.DOTALL)
    if not ul_m:
        print("    [warn] no assignment-links list found — assignments left unchanged")
        return html

    inner = ul_m.group(1)
    # Strip HTML comment blocks first (e.g. the commented-out "BLOG POST —
    # add only on blog post weeks" / HOMEWORK / WRITING ASSIGNMENT / UNLINKED
    # EXAMPLE template scaffolding create_week_pages.py copies into every stub
    # week from templates/week.html). Without this, LI_RE below matches <li>
    # markup INSIDE those comments too and incorrectly "activates" it as real
    # content — those examples aren't relevant to hybrid pages anyway.
    inner = re.sub(r'<!--.*?-->', '', inner, flags=re.DOTALL)
    items = LI_RE.findall(inner)

    new_items = []
    found_learning_notes = False
    for li in items:
        if "Blog Post" in li or "Blog Comment Declaration" in li:
            continue  # dropped — replaced by Small Group Participation below
        if ">Learning Notes<" in li:
            new_items.append(LEARNING_NOTES_LI)
            new_items.append(SMALL_GROUP_LI)
            found_learning_notes = True
        else:
            new_items.append(li)

    if not found_learning_notes:
        # Shouldn't happen (Learning Notes is present every week) but don't
        # silently drop Small Group Participation if the pattern ever changes.
        new_items.insert(0, LEARNING_NOTES_LI)
        new_items.insert(1, SMALL_GROUP_LI)
        print("    [warn] no Learning Notes <li> matched — inserted both at the top")

    new_inner = "\n\n".join(new_items)
    new_ul = f'<ul class="assignment-links">\n\n{new_inner}\n\n  </ul>'
    return html[:ul_m.start()] + new_ul + html[ul_m.end():]


def transform_add_small_group_section(html):
    if '<h2 class="section-heading" id="small-group">' in html:
        return html  # already present (idempotent — safe to re-run)
    m = LEARNING_MATERIALS_START_RE.search(html)
    if not m:
        print("    [warn] no 'Learning Materials start' marker found — Small Group section not inserted")
        return html
    return html[:m.start()] + SMALL_GROUP_SECTION + html[m.start():]


def process_week(num):
    src = REPO / f"week{num:02d}" / "week.html"
    if not src.exists():
        print(f"  SKIP  week{num:02d} — {src} not found")
        return

    html = src.read_text(encoding="utf-8")
    html = transform_video1(html)
    html = transform_assignments(html)
    html = transform_add_small_group_section(html)
    # hybrid/weekNN/ sits one directory deeper than root weekNN/, so the
    # relative link to course-styles.css needs an extra "../" — otherwise
    # the page previews unstyled in a browser (harmless for the actual
    # Canvas build, which inlines CSS and strips <link> regardless, but
    # local preview is a stated design goal — see MODULE-STANDARDS.md).
    html = html.replace(
        '<link rel="stylesheet" href="../course-styles.css">',
        '<link rel="stylesheet" href="../../course-styles.css">'
    )

    out_dir = REPO / "hybrid" / f"week{num:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "week.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"  OK    hybrid/week{num:02d}/week.html")


def main():
    args = sys.argv[1:]
    if not args:
        nums = list(range(1, 16))
    elif len(args) == 1:
        nums = [int(args[0])]
    elif len(args) == 2:
        nums = list(range(int(args[0]), int(args[1]) + 1))
    else:
        print("Usage: create_hybrid_week_pages.py [start [end]]")
        sys.exit(1)

    for num in nums:
        process_week(num)

    print("\nDone. Run 'bash build/build.sh hybrid' to build Canvas-ready HTML.")


if __name__ == "__main__":
    main()
