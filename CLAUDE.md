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

15 weeks + finals. Topics in order:
1. Learning & Nature of Science
2. Biological Molecules
3. Cells & Biological Organization
4. Biological Membranes & Cell Signaling
5. DNA & Genetic Variation
6. Gene Expression
7. Cell Division
8. Inheritance
9. Evolution & Natural Selection
10. Population Genetics & Speciation
11. Cellular Respiration
12. Photosynthesis
13. Biological Systems
14. Ecosystems
15. Human Impacts on Biological Systems

## Assessments

| Item | Points |
|------|--------|
| ELQs (embedded in videos) | 150 |
| Writing Assignments (×2) | 100 |
| Take-Home HW | 100 |
| Tests 1, 2, 3 (150 each) | 450 |
| Final Exam | 200 |
| **Total** | **1000** |

Tests are taken via Measure Learning/ProctorU or a registered testing center — self-scheduled asynchronously. Test weeks still have module content (reduced, not absent).

## Key Deadlines

- **June 11, 2026** — ITLE syllabus + Week 1 sample activity submitted to CCO
- **July 17, 2026** — Peer review ends
- **July 31, 2026** — Instructor target: all content complete
- **August 12, 2026** — Final CCO submission due

## File Structure

```
biol1113/
├── .env.example        ← Credential template (committed; no real values)
├── .gitignore          ← Excludes .env, build output, exams, quizzes
├── CLAUDE.md           ← You are here
├── README.md
├── course-styles.css   ← Single CSS source of truth
├── build/
│   ├── build.sh        ← Run this to build Canvas-ready HTML
│   ├── inline_css.py   ← CSS inliner
│   └── biol1113/       ← Generated output (gitignored)
├── scripts/
│   ├── upload_to_canvas.py   ← Upload pages via Canvas API
│   ├── create_module_items.py← Create Canvas module structure
│   └── clean_sandbox.py      ← Wipe sandbox only (safety guarded)
├── templates/
│   ├── week-overview.html
│   ├── week-materials.html
│   └── week-assignments.html
├── docs/
│   └── MODULE-STANDARDS.md
├── slides/             ← Keynote/PPT source files (large; may be gitignored)
└── week01/ – week15/   ← One folder per week, three HTML files each
```

## Build Workflow

1. Edit `weekNN/*.html` source files
2. Edit `course-styles.css` if styles change
3. `bash build/build.sh` — generates Canvas-ready HTML in `build/biol1113/`
4. `python3 scripts/upload_to_canvas.py` — pushes to Canvas as drafts
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
- Draft ELQ or test questions
- Curate external videos or readings
- Make content decisions on behalf of the instructor
