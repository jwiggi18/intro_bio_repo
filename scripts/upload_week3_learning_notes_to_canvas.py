#!/usr/bin/env python3
"""
upload_week3_learning_notes_to_canvas.py — Upload the per-video guided
Learning Notes .docx handouts for WEEK 3 ONLY to a Canvas course's Files as
hotlinkable downloads, and print the notes_urls entries to paste into
canvas_targets.py.

Split out from upload_learning_notes_to_canvas.py (which covers Weeks 1-2)
so that re-running the Week 3 upload never re-uploads the Weeks 1-2 files
(those source .docx also happen to still sit in scripts/learning_notes_source/,
and the original script's NOTES dict would re-upload all of them, creating
duplicate Canvas Files each run). Same upload mechanics, same .env
requirement, same source folder.

Usage:
  python3 scripts/upload_week3_learning_notes_to_canvas.py sandbox
  python3 scripts/upload_week3_learning_notes_to_canvas.py live
  python3 scripts/upload_week3_learning_notes_to_canvas.py hybrid

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - scripts/learning_notes_source/*.docx present (one file per NOTES dict
    entry below)

Requires Python 3.8+. Standard library only.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

import upload_learning_notes_to_canvas as base

# Week 3 only. Key naming follows the same convention as the Weeks 1-2 NOTES
# dict in upload_learning_notes_to_canvas.py (short stem describing the
# video, reused for {{NOTES_URL:<key>}} on the week page).
base.NOTES = {
    "Cell_Signaling_Types": "3-1 — Cell Communication- Cell Signaling Types.docx",
    "Receptors_and_Transduction": "3-2 — Cell Communication- Receptors and Transduction.docx",
    "Cholera_Communication_Connection": "3-3 — Cholera- The Communication Connection.docx",
    "Amoeba_Sisters_Dehydration_Hydrolysis": "3-4 — Amoeba Sisters- Dehydration Synthesis and Hydrolysis.docx",
}

if __name__ == '__main__':
    base.main()
