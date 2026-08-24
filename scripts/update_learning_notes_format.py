#!/usr/bin/env python3
"""
update_learning_notes_format.py — PATCH the description and allowed_extensions
on the 15 EXISTING "Week N Learning Notes" assignments for a target course.

Why this exists separately from create_learning_notes_group.py: that script
only creates assignments and skips ones that already exist (idempotent
create, not update). Once the 45 Learning Notes assignments across
sandbox/live/hybrid already existed, changing their description/format
policy needed a dedicated update path. Run this instead of re-running
create_learning_notes_group.py when the wording or accepted file formats
change.

What it does, per target:
  - Finds the existing "Week N Learning Notes" assignment (N = 1..15)
  - PATCHes its description to assignment_description(N, pdf_url) (imported
    from create_learning_notes_group.py, so both scripts always agree on copy)
  - PATCHes allowed_extensions to ['pdf'] only
  - Leaves name, points, due dates, published state, and everything else
    untouched

Usage:
  python3 scripts/update_learning_notes_format.py sandbox
  python3 scripts/update_learning_notes_format.py live
  python3 scripts/update_learning_notes_format.py hybrid

Requirements:
  - .env with CANVAS_TOKEN
  - canvas_targets.py has the target's course_id/base_url/learning_notes_ids
    filled in, ideally with multipage_pdf_url set too (run
    scripts/upload_multipage_pdf_to_canvas.py first if not)
  - Standard library only (no pip installs)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from create_learning_notes_group import (
    get_config, canvas_request, paginated_get, find_assignment,
    assignment_description, WEEKS,
)

NEW_ALLOWED_EXTENSIONS = ['pdf']


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/update_learning_notes_format.py <target>")
        print("  target = sandbox, live, hybrid -- see canvas_targets.py")
        sys.exit(1)
    target_name = sys.argv[1]

    cfg = get_config(target_name)
    token = cfg['CANVAS_TOKEN']
    base_url = cfg['CANVAS_BASE_URL']
    course_id = cfg['CANVAS_COURSE_ID']
    pdf_url = cfg['TARGET'].get('multipage_pdf_url')

    if not pdf_url:
        print(f"  [warn] no multipage_pdf_url set for target '{target_name}' -- "
              f"descriptions will reference the doc without a direct link. "
              f"Run scripts/upload_multipage_pdf_to_canvas.py against this target first.")

    print(f"Target: {target_name} (course {course_id})")
    print("Fetching existing assignments...")
    existing_assignments = paginated_get(f'courses/{course_id}/assignments?per_page=100', token, base_url)

    updated = 0
    missing = []
    for week_num in WEEKS:
        name = f"Week {week_num} Learning Notes"
        existing = find_assignment(name, existing_assignments)
        if not existing:
            missing.append(name)
            print(f"  [missing] {name} -- not found in course {course_id}, skipping")
            continue

        payload = {
            'assignment': {
                'description': assignment_description(week_num, pdf_url),
                'allowed_extensions': NEW_ALLOWED_EXTENSIONS,
            }
        }
        canvas_request(
            'PUT',
            f'courses/{course_id}/assignments/{existing["id"]}',
            token, base_url,
            payload
        )
        print(f"  [updated] {name} (id: {existing['id']})")
        updated += 1

    print(f"\nDone. {updated}/15 Learning Notes assignments updated for target '{target_name}'.")
    if missing:
        print(f"  {len(missing)} assignment(s) not found (never created?): {', '.join(missing)}")


if __name__ == '__main__':
    main()
