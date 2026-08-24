# BIOL 1113 Syllabus — Production Notes

Running log of decisions, toolchain, and how to update the syllabus. Update this file whenever a structural or design decision is made.

---

## Toolchain

The syllabus is a single self-contained HTML file (`syllabus.html`) with all CSS embedded in a `<style>` block. PDF is generated from it using WeasyPrint.

**Source file:** `syllabus.html`
**PDF output:** `BIOL1113_Syllabus_Fall2026.pdf`
**Generate PDF:**
```bash
python3 scripts/generate_syllabus_pdf.py
```
**Install WeasyPrint (one-time):**
```bash
pip install weasyprint
```

WeasyPrint was chosen over browser printing because browser print dialogs inject date, URL, and page number headers into the margins that can't be suppressed with CSS. WeasyPrint produces a clean PDF with no browser chrome, proper page breaks, and full color preservation.

---

## Page Layout

- **Page size:** US Letter (8.5 × 11 in)
- **Margins:** 0.4 in (narrowed from 0.65 in to improve content fit)
- **Font size (print):** 10pt body
- **Page breaks:** Each major section (#grades, #schedule, #policies, #ai, #accessibility) begins on a new page. The cover gets its own page.

---

## Sections

| # | ID | Title |
|---|---|---|
| Cover | — | Two-column: nav + instructor info |
| 01 | `#overview` | Course Overview + Teaching Philosophy |
| 02 | `#how-it-works` | How This Course Works |
| 03 | `#objectives` | Learning Objectives |
| 04 | `#grades` | Grades & Assessment |
| 05 | `#schedule` | Course Schedule |
| 06 | `#policies` | Policies |
| 07 | `#ai` | AI Acceptable Use |
| 08 | `#accessibility` | Accessibility & Support |

---

## Grading Structure Decisions

**Date:** July 2026

Moved from a traditional fixed-point system to a choice-based grading model. Key decisions:

- **Tests reduced from 65% to ~40% of available points.** Original structure had tests at 450/1000 pts (45%) + final at 200/1000 (20%) = 65%. Concern: multiple-choice exams are a poor measure of concept mastery at that weight.
- **Writing assignments replaced by blog posts + comments.** Low-stakes, frequent writing is more pedagogically sound than two high-stakes papers. Blog posts are tied to the *prior* week's content to allow processing time.
- **Blog comments verified via Canvas declaration quiz.** Students affirm completion (true/false) and submit URLs of posts they commented on. Eliminates need to manually audit comment threads.
- **Learning Notes floor expressed as points, not weeks.** Students must earn ≥ 100 of 150 available Learning Notes points. Framing as a point threshold (not "miss no more than 3 weeks") is more accurate — the requirement is per video, not per week. (Aug 10, 2026: replaced ELQs — see [[project_biol1113]] / SESSION_NOTES.md for the change.)
- **Homework is optional but strongly encouraged.** No floor/floor requirement. Students who do HW earn extra points toward their total; those who skip lose cushion but aren't penalized.
- **Canvas implementation:** Use "drop lowest N" within assignment groups for blog posts (drop 4 of 14) and comments (drop 4 of 14). Learning Notes is its own Canvas Assignment Group too, but with no drop-lowest rule — the ≥100/150 threshold already gives the same flexibility, since points simply accumulate across whichever videos a student submits notes for. Use a custom Canvas grading scheme with letter grade cutoffs set to raw point thresholds (A ≥ 900, B ≥ 800, etc.) since the total available (1,120) exceeds what any grade requires.

**Point summary:**

| Category | Available | Floor |
|---|---|---|
| Tests 1–3 | 300 | All required |
| Final Exam | 150 | Required |
| Blog Posts (14 × 20 pts) | 280 | Complete ≥ 10 |
| Blog Comments (14 × 10 pts) | 140 | Complete ≥ 10 |
| Learning Notes | 150 | Earn ≥ 100 pts |
| Take-Home HW | 100 | Optional |
| **Total available** | **1,120** | |

---

## Design Notes

- All CSS is embedded directly in `syllabus.html` — no external stylesheet. This is intentional: the file is self-contained and can be shared or opened anywhere without dependency issues. (This is different from the week pages, which use `course-styles.css`.)
- The cover uses a two-column flex layout (navy left panel, white right panel). WeasyPrint 69 handles this correctly.
- The donut chart is a static SVG — no JavaScript, no external libraries. Arc paths were computed programmatically when the point structure changed. If points change again, rerun the SVG generator in the chat history or recompute manually.
- `print-color-adjust: exact` is not needed for WeasyPrint (it always renders colors). It is still present for any future browser-print use.

---

## Update Checklist

When editing the syllabus, work through this list:

- [ ] Edit `syllabus.html` directly (all content and styles are in one file)
- [ ] If the grading point totals change, recompute the SVG donut chart arc paths
- [ ] Update this production notes file with any structural or design decisions
- [ ] Update `CLAUDE.md` if the assessment structure changes
- [ ] Regenerate the PDF: `python3 scripts/generate_syllabus_pdf.py`
- [ ] Commit both `syllabus.html` and `BIOL1113_Syllabus_Fall2026.pdf` to git
