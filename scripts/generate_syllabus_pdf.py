#!/usr/bin/env python3
"""
generate_syllabus_pdf.py — Generate BIOL 1113 syllabus PDF using WeasyPrint.

Produces a clean, print-ready PDF with no browser headers/footers,
proper page breaks, and full color preservation.

Usage:
  python3 scripts/generate_syllabus_pdf.py

Output: BIOL1113_Syllabus_Fall2026.pdf in the repo root.

Requirements:
  pip install weasyprint
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / 'syllabus.html'
OUT  = ROOT / 'BIOL1113_Syllabus_Fall2026.pdf'

def main():
    try:
        from weasyprint import HTML
    except ImportError:
        print("WeasyPrint not installed. Run:  pip install weasyprint")
        sys.exit(1)

    if not SRC.exists():
        print(f"Error: {SRC} not found.")
        sys.exit(1)

    print(f"Generating PDF from syllabus.html ...")
    HTML(filename=str(SRC)).write_pdf(str(OUT))
    print(f"Done → {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
