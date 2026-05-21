# BIOL 1113 – Canvas Course Build Plan
**Introductory Biology, Concurrent Enrollment**  
Dr. Jodie Wiggins | Oklahoma State University  
Build window: May 21 – July 31, 2026  
Final due: August 12, 2026

---

## Hard Deadlines

| Date | Milestone |
|------|-----------|
| May 11 | Online training opens |
| May 13 | Kick-Off Webinar (live or recorded) |
| **June 11** | **Training complete + syllabus + sample activity submitted** |
| June 12–July 17 | Peer review period |
| **July 20–31** | **Course revisions and template finalization** |
| August 3–4 | Mandatory in-person workshop |
| **August 12** | **Final course template and revision documentation due** |

---

## ⚠️ Security: Protecting Canvas Access

The reference repo (rose-build) uses a Python Canvas API script. The single most important security rule for this repo is:

**Your Canvas API token must never appear in any committed file.**

Concrete actions:
1. Create a `.env` file locally for your token — this file is gitignored and never committed
2. Create a `.env.example` file that documents the variable name (e.g., `CANVAS_TOKEN=your_token_here`) but contains no real value — this IS committed
3. The `upload_to_canvas.py` script reads from `.env` at runtime only
4. Gitignore all quiz/exam source files (answers in plaintext)
5. Never store student names, emails, grades, or IDs anywhere in the repo
6. Use a Canvas sandbox course ID for all testing; hard-code a guard that refuses to wipe non-sandbox courses

What is safe to commit: HTML page templates, CSS, build scripts, reading lists, slide outlines, assignment descriptions without answers.

---

## Course Overview

**15 weeks + finals. 1,000 points total.**

| Assessment | Points |
|------------|--------|
| Embedded Learning Questions (ELQs) | 150 |
| Writing Assignments (×2) | 100 |
| Take-Home Assignments (HW) | 100 |
| Test 1, 2, 3 (150 pts each) | 450 |
| Final Exam | 200 |

**Week-by-week topics:**

| Week | Topic |
|------|-------|
| 1 | Learning and The Nature of Science |
| 2 | Biological Molecules and the Chemical Basis of Life |
| 3 | Cells and Biological Organization |
| 4 | Biological Membranes and Cell Signaling |
| 5 | DNA and Genetic Variation |
| 6 | Gene Expression |
| 7 | Cell Division |
| 8 | Inheritance |
| 9 | Evolution and Natural Selection |
| 10 | Population Genetics and Speciation |
| 11 | Cellular Respiration |
| 12 | Photosynthesis |
| 13 | Biological Systems |
| 14 | Ecosystems |
| 15 | Human Impacts on Biological Systems |
| Finals | Final Exam |

**Test placement (to be decided):** Tests 1, 2, and 3 need specific weeks assigned. A natural grouping: Test 1 after Week 4 (chemistry through signaling), Test 2 after Week 8 (genetics), Test 3 after Week 12 (energy/metabolism), Final covers everything.

---

## Repo Structure (adapted from rose-build)

```
biol1113/
├── .env.example              ← Documents required env vars; NO real values
├── .gitignore                ← Excludes .env, build output, exams, quizzes
├── CLAUDE.md                 ← Project context for AI-assisted work
├── README.md                 ← Human-readable orientation
├── course-styles.css         ← Single CSS source of truth for all pages
├── build/
│   ├── build.sh              ← CSS inliner and HTML builder
│   ├── inline_css.py         ← Inlines CSS for Canvas upload
│   └── biol1113/             ← Canvas-ready output (gitignored)
├── scripts/
│   ├── upload_to_canvas.py   ← Canvas API page uploader (reads .env)
│   ├── create_module_items.py← Creates Canvas module structure via API
│   └── clean_sandbox.py      ← Sandbox-only wipe tool
├── templates/
│   ├── week-overview.html
│   ├── week-materials.html   ← Readings + curated videos
│   └── week-assignments.html
├── docs/
│   ├── MODULE-STANDARDS.md
│   ├── WRITING-STANDARDS.md
│   └── CANVAS-SETUP-GUIDE.md
├── glossary.json
├── slides/                   ← Slide deck outlines (Keynote/PPT source)
└── week01/ through week15/   ← One folder per week
    ├── overview.html
    ├── materials.html        ← Readings + curated external videos
    └── assignments.html
```

---

## What Each Weekly Module Needs

Every week requires these Canvas components:

**Page content (HTML, built and uploaded):**
- Overview page: objectives, "what you'll do this week," links to all materials and assignments
- Materials page: OpenStax reading sections (specific, never full chapters), curated external videos with focus questions, ELQ guidance
- Assignment page: describes HW if applicable, writing assignments when relevant, links to tests when applicable

**Canvas items (created via API or manually):**
- Weekly module in Canvas with scheduled release (Monday 12:00 AM)
- ELQ quizzes embedded in or linked from videos (via Kaltura or Canvas quiz)
- HW assignment submissions (not every week — see schedule)
- Announcements (template created, sent at module open)

**Instructor-produced videos (Jodie records):**
- 2–3 focused videos per week, each under 10 minutes
- Slides built first; video recorded from slides
- ELQ questions embedded at key moments

---

## Video Production Reality Check

This is the hardest constraint in the build. Here's the honest math:

- 15 weeks × 2–3 videos = ~35–40 instructor-created videos
- At ~10 min each: ~6 hours of raw recording
- Editing (basic cuts, captions): ~15 hours
- Slide building: ~2 hours/week × 15 weeks = ~30 hours
- **Total video production work: ~50–55 hours**

That's ~5–6 hours/week over the 10-week build window — very achievable, but only if slides are ready before recording begins each week. The slides need to be built 1–2 weeks ahead of recording so there's no bottleneck.

Jodie's own teaching philosophy (from the syllabus) already anticipates this: "I also intentionally incorporate well-produced educational videos from reputable scientific communicators" — so external curation can fill gaps and reduce the number of instructor-created videos needed.

---

## Division of Labor

### Claude can build/automate:
- Repo structure, .gitignore, build scripts
- All HTML page templates and Canvas page content
- OpenStax reading section mappings (specific sections, not full chapters)
- Curated external video lists with rationale for each topic
- ELQ question drafts (you review and finalize)
- Slide deck outlines (structure, key points, suggested visuals per slide)
- ITLE-compliant syllabus reformatting
- Canvas module structure scripts
- Glossary (biological terms with definitions)
- Writing assignment prompts + rubrics
- HW assignment drafts
- Weekly announcement templates

### Jodie must do:
- Record all videos (only you can do this)
- Review and approve all content before it goes to Canvas
- Complete CCO online training (required by June 11)
- Watch/watch recording of Kick-Off Webinar
- Finalize test dates and test question writing (or review AI drafts)
- Make all Canvas configuration decisions
- Peer review feedback review and response

---

## Phased Timeline

### Phase 0: Repo Foundation (May 21–27)
**Goal: Everything is scaffolded and ready to build into.**

- [ ] Initialize repo, create all folder structure
- [ ] Write `.gitignore` with credential + exam protection
- [ ] Write `.env.example`
- [ ] Adapt build scripts from rose-build (CSS inliner, Canvas uploader)
- [ ] Create HTML templates for all three page types
- [ ] Write CLAUDE.md with full project context
- [ ] Create `course-styles.css` starter
- [ ] Map all 15 weeks to specific OpenStax Biology 2e sections

**Jodie this week:**
- Complete Kick-Off Webinar (or watch recording)
- Begin CCO online training modules
- Decide test placement weeks

---

### Phase 1: June 11 Submission (May 28–June 11)
**Goal: ITLE-compliant syllabus + fully-built sample module submitted for review.**

**Which module to submit:** Week 1 (Learning and Nature of Science) is the best choice — it's conceptually accessible, sets up expectations, and is the most polished thing to show a reviewer. It also includes the welcome/orientation material CCO requires.

**Build Week 1 fully:**
- [ ] Overview page (HTML)
- [ ] Materials page with OpenStax Ch. 1 sections + curated science/epistemology videos
- [ ] Assignment page (no HW Week 1 — introduce ELQs and syllabus quiz)
- [ ] Welcome + orientation video script written
- [ ] Course homepage built (directs students to begin here)

**Finalize syllabus:**
- [ ] Reformat current BIOL_1113 draft into ITLE syllabus template
- [ ] Add missing sections: accessibility, institutional requirements, CCO-specific policies
- [ ] Confirm test dates and fill in blanks (Week __ for Tests 1–3, Final)
- [ ] Add virtual office hours schedule (currently TBD)

**Jodie this week:**
- Record welcome + orientation video (script provided)
- Complete online training
- Review and approve Week 1 content
- Fill in syllabus blanks (test dates, office hours)

---

### Phase 2: Content Build (June 11–July 17)
**Goal: All 15 weeks fully built. Slide decks done. Videos recorded.**

This phase runs concurrently with peer review. Build 1–2 weeks of content per calendar week. Peer review feedback won't arrive until mid-July, so use this time for maximum build output.

**Recommended build order** (front-load hardest content):

| Calendar Week | Build These Course Weeks |
|--------------|--------------------------|
| June 11–17 | Weeks 2–3 (Biological Molecules, Cells) |
| June 18–24 | Weeks 4–5 (Membranes, DNA) |
| June 25–July 1 | Weeks 6–7 (Gene Expression, Cell Division) |
| July 2–8 | Weeks 8–9 (Inheritance, Evolution) |
| July 9–15 | Weeks 10–11 (Pop Genetics, Cell Respiration) |
| July 16–17 | Buffer / catch-up |

For each week, Claude builds: slide outlines, HTML pages, reading assignments, ELQ drafts.  
Jodie reviews, then records videos from finalized slide decks.

---

### Phase 3: Content Build continued + Revisions (July 17–31)
**Goal: Remaining weeks built + peer review feedback incorporated.**

| Calendar Week | Build These Course Weeks | Also |
|--------------|--------------------------|------|
| July 17–22 | Weeks 12–13 (Photosynthesis, Biological Systems) | Peer review feedback arrives ~July 17; triage |
| July 23–31 | Weeks 14–15 (Ecosystems, Human Impacts) + Finals | Apply revisions, finalize template |

---

### Phase 4: Final Submission (Aug 1–12)
- [ ] In-person workshop (Aug 3–4) — bring questions, bring near-final course
- [ ] Final Canvas course review
- [ ] Revision documentation written
- [ ] Submit by August 12

---

## Immediate Next Steps (This Week)

In priority order:

1. **Decide test weeks** — fill in the blanks in the syllabus (Tests 1, 2, 3, and Final)
2. **Watch Kick-Off Webinar** — understand exactly what's required for June 11 submission
3. **Start CCO training** — needs to be done by June 11
4. **Review this plan** — confirm the sample module choice (Week 1) and the topic-to-week mapping
5. **Repo initialization** — Claude can start this immediately

---

## OpenStax Biology 2e — Preliminary Section Mapping

These are starting assignments; Claude will refine these into specific sections with page links.

| Week | Topic | Primary OpenStax Sections |
|------|-------|--------------------------|
| 1 | Nature of Science | Ch. 1 (all); Unit 1 Intro |
| 2 | Biological Molecules | Ch. 2.1–2.3, Ch. 3 (all) |
| 3 | Cells | Ch. 4 (all), Ch. 5 intro |
| 4 | Membranes & Signaling | Ch. 5 (all), Ch. 9.1–9.3 |
| 5 | DNA & Genetic Variation | Ch. 14.1–14.5, Ch. 17.1 |
| 6 | Gene Expression | Ch. 15 (all), Ch. 16.1–16.5 |
| 7 | Cell Division | Ch. 10 (all) |
| 8 | Inheritance | Ch. 12 (all), Ch. 13.1–13.3 |
| 9 | Evolution & Natural Selection | Ch. 18.1–18.5, Ch. 19.1–19.3 |
| 10 | Population Genetics & Speciation | Ch. 19.3–19.5, Ch. 18.3 |
| 11 | Cellular Respiration | Ch. 7 (all) |
| 12 | Photosynthesis | Ch. 8 (all) |
| 13 | Biological Systems | Ch. 33 intro, Ch. 38.1–38.4, Ch. 40 intro |
| 14 | Ecosystems | Ch. 46 (all), Ch. 47.1–47.4 |
| 15 | Human Impacts | Ch. 47.3–47.5, Ch. 46.4–46.5 |

---

## CCO Required Canvas Elements Checklist

Per the CC Academy Course Design Expectations:

- [ ] Course homepage that welcomes students and directs them where to begin
- [ ] Weekly instructor presence (video OR announcement each week — plan for both)
- [ ] All content organized in Modules
- [ ] Release conditions / scheduled dates (no full course visible at once)
- [ ] Welcome and orientation video that:
  - [ ] Introduces Jodie
  - [ ] Reviews important syllabus information
  - [ ] Explains course expectations
  - [ ] Walks through Canvas navigation

---

## Notes on Adapting the rose-build Approach

The reference repo (rose-build by Dan Lovejoy) is well-designed and directly applicable. Key adaptations:

1. **Single course vs. two concurrent courses** — the `data-concurrent` system in rose-build isn't needed here (BIOL 1113 is standalone). Simplifies the build considerably.
2. **ELQs** — rose-build used reading quizzes via IMSCC; BIOL 1113 uses ELQs embedded in videos. These can be Canvas quizzes linked from materials pages.
3. **Labs vs. lectures** — rose-build had lab notebooks; BIOL 1113 has HW assignments and writing assignments instead. Templates will differ.
4. **Video-first design** — Jodie's philosophy puts videos at the center (not interactive demos). Every page is essentially a "here's what to watch, here's what to read, here's the ELQ."
5. **The CSS inliner and Canvas uploader from rose-build can be used almost as-is.** The main adaptation is the page templates.

---

*This document is a living plan. Update it as decisions are made and phases are completed.*
