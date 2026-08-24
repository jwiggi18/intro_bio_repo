#!/usr/bin/env python3
"""
generate_chart_png.py — Render the syllabus grade-breakdown donut chart to a
PNG for embedding in syllabus.html.

Why this exists: Canvas's syllabus_body field (the course-level field behind
the native Syllabus tool) strips <svg> elements entirely, unlike wiki pages.
The chart in syllabus.html is an <img src="{{CHART_IMAGE_URL}}"> that
build/upload_to_canvas.py resolves per Canvas course after uploading this
PNG as a Canvas file (see upload_chart_to_canvas.py).

scripts/chart_source.svg is the single source of truth for the chart's
numbers/geometry. If grade point values or percentages change:
  1. Edit scripts/chart_source.svg
  2. Re-run this script to regenerate the PNG
  3. Run scripts/upload_chart_to_canvas.py <target> for each target to
     re-upload it and refresh canvas_targets.py's chart_image_url
  4. Rebuild and re-upload the syllabus page

Renders at 2x (520x520px) for retina sharpness; the <img> tag in
syllabus.html displays it at 260x260 via its width/height attributes.

Requires: playwright (pre-installed in this environment's Chromium at
/opt/pw-browsers/chromium).

Usage:
  python3 scripts/generate_chart_png.py           # default chart (sandbox/live)
  python3 scripts/generate_chart_png.py hybrid     # target-specific chart, if
                                                    # scripts/chart_source_<target>.svg exists
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCALE = 2  # render at 2x the display size for retina sharpness


def paths_for(target_name):
    """Pick the right SVG source / PNG output for this target. Targets whose
    grade breakdown genuinely differs (e.g. hybrid) get their own
    chart_source_<target>.svg / chart_output_<target>.png; everything else
    falls back to the shared chart_source.svg / chart_output.png."""
    if target_name:
        svg = ROOT / "scripts" / f"chart_source_{target_name}.svg"
        if svg.exists():
            return svg, ROOT / "scripts" / f"chart_output_{target_name}.png"
    return ROOT / "scripts" / "chart_source.svg", ROOT / "scripts" / "chart_output.png"


def main():
    from playwright.sync_api import sync_playwright

    target_name = sys.argv[1] if len(sys.argv) > 1 else None
    SVG_SOURCE, OUT_PATH = paths_for(target_name)

    svg_markup = SVG_SOURCE.read_text(encoding="utf-8")
    # Bump the outer width/height attrs by SCALE; viewBox stays the same so
    # the rendered content scales up crisply rather than just being cropped.
    svg_markup = svg_markup.replace('width="260" height="260"',
                                     f'width="{260*SCALE}" height="{260*SCALE}"', 1)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>html,body {{ margin:0; padding:0; background:transparent; }}</style>
</head><body>{svg_markup}</body></html>"""

    tmp_html = ROOT / "scripts" / "_chart_render_tmp.html"
    tmp_html.write_text(html, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        page = browser.new_page(viewport={"width": 260 * SCALE, "height": 260 * SCALE})
        page.goto(f"file://{tmp_html}")
        el = page.query_selector("svg")
        el.screenshot(path=str(OUT_PATH), omit_background=True)
        browser.close()

    tmp_html.unlink()
    print(f"[written] {OUT_PATH}")


if __name__ == "__main__":
    main()
