# CLAUDE.md — BIOL 1113 Project Context

## Project

Canvas course build for BIOL 1113 — Introductory Biology, Concurrent Enrollment.  
Instructor: Dr. Jodie Wiggins, Oklahoma State University.  
Primary text: OpenStax Biology 2e (free OER, https://openstax.org/details/books/biology-2e).

## Critical Rules

1. **Never write or suggest hardcoding Canvas credentials.** All tokens go in `.env` (gitignored). The `.env.example` file documents variable names only.
2. **Never create content for week folders without explicit instruction.** Dr. Wiggins is particular about biological content. Build structure, not substance.
3. **Never assign full textbook chapters.** Specific sections only, per the instructor's pedagogy.
4. **Never edit files in `build/biol1113/`.** They are generated and will be overwritten.
5. **Never put `<style>` blocks in HTML source files.** All CSS goes in `course-styles.css`.

## Course Structure

**Source of truth:** `1.Intro_Bio/1.2026/schedules/Weekly_topic_schedule_DRAFT.xlsx`, `topic_schedule` tab.
Updated here July 31, 2026. If this list and that sheet disagree, the sheet wins.

15 weeks + finals. Topics in order:

| Week | Topic | Dates |
|---|---|---|
| 1 | Learning & Nature of Science | Aug 17–23 |
| 2 | The Cell & Its Membrane | Aug 24–30 |
| 3 | Cell Communication | Aug 31–Sep 6 |
| 4 | Transport & Communication in Action | Sep 7–13 (Labor Day Sep 7) |
| 5–6 | Biological Systems (membranes & signaling applied) | Sep 14–27 |
| 7–9 | Genetics (compressed from 4 weeks to 3) | |
| 10 | Evolution & Natural Selection | Oct 19–25 |
| 11 | Speciation & Ecology | Oct 26–Nov 1 |
| 12 | Ecosystems | Nov 2–8 |
| 13 | Cellular Respiration | Nov 9–15 |
| 14 | Photosynthesis | Nov 16–22 |
| 15 | Human Impacts on Biological Systems | Nov 30–Dec 4 |

Fall Break Nov 23–25; University Holiday Nov 26–27. No new content that week.

**This changed in July 2026.** Biological Systems moved from Week 13 to Weeks 5–6, and
genetics compressed from 4 weeks to 3. Cellular Respiration and Photosynthesis moved
from Weeks 11–12 to Weeks 13–14. Older docs referencing the previous order are stale.

**Weeks 1–4 finalized Aug 10, 2026** with real video titles and topic names (see
`week01`–`week04` `week.html`): Week 2 is membrane transport (with a cholera throughline),
Week 3 is cell signaling (with a cholera throughline), Week 4 applies both to animal body
systems — tissues/homeostasis, the nervous system, the endocrine system, and disease/immune
disruption of homeostasis. **⚠️ This overlaps with the Weeks 5–6 label above** ("Biological
Systems — membranes & signaling applied"), which was written before Week 4 absorbed the
nervous/endocrine/homeostasis content. What's actually left to cover in Weeks 5–6 once
Week 4 exists needs Jodie's review — this doc hasn't been reconciled that far yet.

**Test windows:** Test 1 opens Week 5 (covers Weeks 1–4). Test 2 opens Week 9 (covers
Weeks 5–8). Test 3 opens Week 13 (covers Weeks 9–12). Test weeks carry lighter content.

**Open scheduling decision (in the sheet, not yet resolved):** Option A adds a new topic
in the week freed by genetics compression; Option B expands Biological Systems to 2 full
weeks. Weeks 1–4 and 10–15 are identical either way.

## Assessments

Choice-based grading: more points are available than required for any grade. Students earn points across categories; floors prevent skipping entire areas.

| Category | Available | Floor | Notes |
|---|---|---|---|
| Tests 1–3 | 300 | All 3 required | 100 pts each; proctored via Measure Learning/ProctorU or testing center |
| Final Exam | 150 | Required | Proctored |
| Learning Notes | 240 | Best 11 of 15 weeks (need 176 pts) | Photo-of-notes submission per **week** (not per video, changed Aug 11, 2026) — one Canvas Assignment per week (15 total), 16 pts each, grouped under the Learning Notes assignment group with a drop_lowest=4 rule |
| Blog Posts | 224 | Best 10 of 14 (need 168 pts) ⚠️ see note below | Weeks 2–15; tied to prior week's content; 16 pts each; 4 lowest dropped in Canvas |
| Blog Comments | 112 | Best 10 of 14 (need 80 pts) | 2 structured comments per post; verified via Canvas declaration quiz; 8 pts each; 4 lowest dropped |
| Take-Home HW | 100 | Optional (no floor) | Earns toward total; no penalty for skipping |
| **Total available** | **1126** | | |

**⚠️ Known inconsistency (flagged to Jodie, unresolved as of Aug 11, 2026):** Blog Comments and Learning Notes both cleanly match "drop 4 lowest of N" (10/14×8=80, 11/15×16=176). Blog Posts doesn't: 10/14×16=160, but the syllabus shows 168 (75% of 224, a different rule). Applied 168 everywhere per Jodie's source file until she decides whether to change it to 160 or update the "10 of 14" wording instead.

**Grade thresholds (custom Canvas grading scheme, points-based — NOT a percentage of the 1,126 available):**

| Grade | Points |
|---|---|
| A | 900+ |
| B | 800–899 |
| C | 700–799 |
| D | 600–699 |

Tests are self-scheduled asynchronously. Test weeks still have module content (reduced, not absent).

Blog comments are verified via a Canvas declaration quiz: students affirm completion (true/false) and submit URLs of the posts they commented on.

**⚠️ The table above is the sandbox/live grading scheme only.** The hybrid course (see below) has a different one.

## Hybrid Course (lecture + small group, course id 239593)

Added Aug 13, 2026. A separate live section with real structural differences from sandbox/live, not just a different Canvas id — see `canvas_targets.py`'s `hybrid` entry (`content_root: "hybrid"`) and the `hybrid/` folder, which mirrors the repo root layout (`hybrid/homepage.html`, `hybrid/syllabus.html`, `hybrid/weekNN/week.html`).

What's different:
- **No Blog Posts / Blog Comments.** Replaced by **Small Group Participation** — students meet weekly in a small group led by GTA Claudia Goss for hands-on active learning, graded on attendance/completion (same model as Learning Notes).
- **Each week's first video is covered live instead of online.** Students attend lecture with Dr. Wiggins, **Mondays, 3:30–4:20 PM, NRC 106**, instead of watching that video. The week page's first video slot becomes a `.lecture-notice` card (see `course-styles.css`) naming the topic; no focus questions under it (Jodie's call, Aug 13, 2026).
- Everything else (other videos, readings, objectives, Learning Notes, Tests, Final, Take-Home HW) is unchanged from the root course content — `scripts/create_hybrid_week_pages.py` derives `hybrid/weekNN/week.html` mechanically from the current root `weekNN/week.html`, so re-run it after editing root week content to keep hybrid in sync (it does NOT re-run automatically).

**Hybrid grading (see `hybrid/syllabus.html` for full text):**

| Category | Available | Floor | Notes |
|---|---|---|---|
| Tests 1–3 | 300 | All 3 required | Unchanged from sandbox/live |
| Final Exam | 150 | Required | Unchanged from sandbox/live |
| Small Group Participation | 360 | Best 13 of 15 weeks (need 312 pts) | 24 pts/week × 15 weeks; one Canvas Assignment per week, `drop_lowest=2`; created via `scripts/create_small_group_group.py` |
| Learning Notes | 240 | Best 11 of 15 weeks (need 176 pts) | Unchanged from sandbox/live |
| Take-Home HW | 100 | Optional (no floor) | Unchanged from sandbox/live |
| **Total available** | **1150** | | |

**Grade thresholds (recalculated proportionally from sandbox/live's 900/800/700/600 out of 1,126, per Jodie's explicit choice Aug 13, 2026 — NOT the same flat numbers as sandbox/live):**

| Grade | Points |
|---|---|
| A | 919+ |
| B | 817–918 |
| C | 715–816 |
| D | 613–714 |

**Setup still needed before this target is usable end-to-end:** run `python3 scripts/create_learning_notes_group.py hybrid` and `python3 scripts/create_small_group_group.py hybrid` (both take the target name directly now — no more editing `.env`'s `CANVAS_COURSE_ID` by hand; `.env` only needs `CANVAS_TOKEN`), paste the resulting ids into `canvas_targets.py`'s `hybrid` entry, then run `scripts/upload_chart_to_canvas.py hybrid` (chart PNG already rendered — `scripts/chart_output_hybrid.png`, from `scripts/chart_source_hybrid.svg`) and paste its URL in too. Until then `build/build.sh hybrid` builds fine but leaves Learning Notes/Small Group/chart links unresolved (falls back to unlinked/broken image by design, not silently wrong).

**Small group sections (confirmed Aug 13, 2026):** all led by GTA Claudia Goss. 70929 Tue 12:00–12:50 PM, NRD 305. 70931 Tue 3:00–3:50 PM, CLB 319. 70927 Wed 3:30–4:20 PM, PS 301B. 70932 Thu 3:00–3:50 PM, CLB 319. 70928 Fri 3:30–4:20 PM, PS 301B. Listed in a table in `hybrid/syllabus.html`'s Grades & Assessment section ("Small Group Meeting Times").

**Open, not decided:** the grade calculation workbook (linked from the "Canvas and Grades" box in the syllabus) still reflects the 1,126-point sandbox/live scheme — needs its own hybrid version or a course-aware update before students rely on it. Small group assignment due dates aren't set (see `create_small_group_group.py` docstring — sections meet at different times, no single Sunday deadline applies).

## Key Deadlines

- **June 11, 2026** — ITLE syllabus + Week 1 sample activity submitted to CCO
- **July 17, 2026** — Peer review ends
- **July 31, 2026** — Instructor target: all content complete
- **August 12, 2026** — Final CCO submission due

## File Structure

```
biol1113/
├── .env.example         ← Credential template (committed; no real values)
├── .gitignore           ← Excludes .env, build output, exams, quizzes
├── CLAUDE.md             ← You are here
├── README.md
├── canvas_targets.py     ← Per-course config (sandbox/live/hybrid) — course ids, content_root, assignment ids
├── course-styles.css     ← Single CSS source of truth (sandbox/live/hybrid all use this)
├── homepage.html         ← sandbox/live homepage (root-level; hybrid has its own, see below)
├── syllabus.html         ← sandbox/live syllabus (root-level; hybrid has its own, see below)
├── build/
│   ├── build.sh          ← Run this to build Canvas-ready HTML (takes a target arg)
│   ├── inline_css.py     ← CSS inliner + per-target placeholder resolver
│   └── biol1113-<target>/ ← Generated output per target, e.g. biol1113-sandbox/ (gitignored)
├── scripts/
│   ├── upload_to_canvas.py         ← Upload pages via Canvas API (takes a target arg)
│   ├── create_module_items.py      ← Create Canvas module structure
│   ├── create_week_pages.py        ← (Re)generate root weekNN/week.html scaffolding (weeks 5-15 stubs)
│   ├── create_hybrid_week_pages.py ← Derive hybrid/weekNN/week.html from root weekNN/week.html
│   ├── create_learning_notes_group.py ← Create the Learning Notes Canvas Assignment Group
│   ├── create_small_group_group.py    ← Create the Small Group Participation group (hybrid only)
│   ├── chart_source.svg / chart_source_hybrid.svg ← Grade donut chart source (sandbox/live vs hybrid numbers)
│   ├── generate_chart_png.py / upload_chart_to_canvas.py ← Render + upload the chart PNG per target
│   └── clean_sandbox.py            ← Wipe sandbox only (safety guarded)
├── templates/
│   └── week.html         ← Single-page week template (one page per week; root course only)
├── docs/
│   └── MODULE-STANDARDS.md
├── slides/               ← Keynote/PPT source files (large; may be gitignored)
├── week01/ – week15/     ← Root course (sandbox/live) — one folder per week, one week.html each
└── hybrid/               ← Hybrid course content root (see "Hybrid Course" above) — mirrors the
    ├── homepage.html         layout above: homepage.html, syllabus.html, weekNN/week.html.
    ├── syllabus.html         Genuinely different content, not shared with sandbox/live.
    └── week01/ – week15/
```

## Build Workflow

Every build/upload script takes a **target** as its first argument (`sandbox`, `live`, or `hybrid` — see `canvas_targets.py`). There is no longer a no-argument form.

1. Edit `weekNN/*.html` (root course) or `hybrid/weekNN/*.html` (hybrid course) source files — for hybrid, prefer editing the root week and re-running `scripts/create_hybrid_week_pages.py` over hand-editing `hybrid/` directly, so the two don't drift.
2. Edit `course-styles.css` if styles change (shared by all targets).
3. `bash build/build.sh <target>` — generates Canvas-ready HTML in `build/biol1113-<target>/`
4. `python3 scripts/upload_to_canvas.py <target>` — pushes to Canvas as drafts (also syncs `syllabus.html` into the course's native Syllabus tool via `syllabus_body`, when syllabus is part of the run)
5. Publish pages manually in Canvas after review

## Standards

See `docs/MODULE-STANDARDS.md` for full conventions on page structure, CSS components, naming, and what belongs in the repo vs. Canvas.

## CCO Requirements

This course is part of the OSU Cowboy Concurrent Online (CCO) program. Required Canvas elements:
- Welcoming course homepage directing students where to begin
- Weekly instructor presence (video or announcement)
- All content organized in Modules with scheduled release dates
- Welcome + orientation video (introduces instructor, syllabus, Canvas navigation)
- ITLE-compliant syllabus

## What Claude Should and Should Not Do

**Do:**
- Build and maintain repo infrastructure (scripts, templates, CSS, build pipeline)
- Fix bugs in build scripts
- Format or restructure HTML that Dr. Wiggins has written
- Check that page structure matches MODULE-STANDARDS.md
- Help draft canvas module structure scripts

**Do not:**
- Write biological content, learning objectives, or explanations of biology concepts without explicit instruction
- Choose which OpenStax sections to assign
- Draft Learning Notes templates or test questions
- Curate external videos or readings
- Make content decisions on behalf of the instructor
