#!/usr/bin/env python3
"""
upload_learning_notes_to_canvas.py — Upload the per-video guided Learning
Notes .docx handouts (Weeks 1-2) to a Canvas course's Files as hotlinkable
downloads, and print the notes_urls dict to paste into canvas_targets.py.

Why a separate upload step from the page build: these are .docx files (not
page HTML), so they go through Canvas's Files API rather than the wiki
page/syllabus_body endpoints upload_to_canvas.py uses. Each Canvas course
gets its own copy of every file with its own URL -- files are not shared
across courses even when the course content is otherwise identical -- so
this needs to run once per target, same as upload_multipage_pdf_to_canvas.py
and upload_chart_to_canvas.py.

Source files live in
"1.courses_taught/1.Intro_Bio/1.2026/learning_notes/" (iCloud, not this
repo) and are staged into scripts/learning_notes_source/ before running this
script (see HOW_TO_upload_learning_notes.md if that doesn't exist yet --
otherwise just copy the .docx files into that folder with matching names).

Usage:
  python3 scripts/upload_learning_notes_to_canvas.py sandbox
  python3 scripts/upload_learning_notes_to_canvas.py live
  python3 scripts/upload_learning_notes_to_canvas.py hybrid

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - scripts/learning_notes_source/*.docx present (one file per NOTES dict
    entry below)

Requires Python 3.8+. Standard library only.
"""

import sys
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target

SOURCE_DIR = ROOT / "scripts" / "learning_notes_source"

# key -> source filename (source of truth: the learning_notes/ folder on
# iCloud). Key naming reuses the same stems as slides_urls in
# canvas_targets.py where a matching slide deck exists, for consistency.
NOTES = {
    "Course_Overview_Syllabus": "1-1 — Course Overview and the Syllabus.docx",
    "Instructor_Intro": "1-2 — Instructor Introduction.docx",
    "Neuroscience_of_Learning": "1-3 — The Neuroscience of Learning & Learning Misconceptions.docx",
    "How_to_Study_Effectively": "1-4 — How to Study Effectively- Six Evidence-Based Strategies.docx",
    "What-is-biology": "1-5 — What is Biology? Themes and the Organization of Life.docx",
    "Science_and_Peer_Review": "1-6 — Science as a Way of Knowing- The Scientific Process and Peer Review.docx",
    "The_cell_intro": "2-1 — Cell Introduction- Eukaryotic vs. Prokaryotic Cells.docx",
    "Cholera_intro": "2-2 — Cholera Intro.docx",
    "Cell_Membrane_Passive_Transport": "2-4 — The Cell Membrane- Passive Transport.docx",
    "Cell_membrane_active_transport": "2-5 — The Cell Membrane- Active Transport.docx",
    "Cholera_explained": "2-6 — Cholera Explained.docx",
    # 2-3 (Why Chemistry? / The Cell Membrane: Water, Chemical Bonds, and
    # Phospholipid Structure) intentionally omitted -- that video was cut
    # from Week 2 (Jodie, Aug 17 2026).
}

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("Error: .env file not found.")
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, val = line.partition('=')
            env[key.strip()] = val.strip()
    return env


def get_token():
    env = load_env()
    token = env.get('CANVAS_TOKEN')
    if not token or 'your_' in token:
        print("Error: CANVAS_TOKEN missing or unfilled in .env")
        sys.exit(1)
    return token


def upload_file(file_path, token, base_url, course_id):
    # Canvas's multipart upload step chokes on the raw em dash in the source
    # filenames when it's not RFC 2231-encoded -- swap it for a plain hyphen
    # in the *uploaded* filename only (source files on disk keep their real
    # names).
    file_name = file_path.name.replace('—', '-')
    file_bytes = file_path.read_bytes()

    step1_data = urllib.parse.urlencode({
        'name': file_name,
        'size': len(file_bytes),
        'content_type': DOCX_CONTENT_TYPE,
        'parent_folder_path': 'learning_notes',
    }).encode()
    req1 = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/courses/{course_id}/files",
        data=step1_data,
        headers={'Authorization': f'Bearer {token}'},
        method='POST',
    )
    with urllib.request.urlopen(req1) as resp:
        step1 = json.loads(resp.read().decode('utf-8'))

    upload_url = step1['upload_url']
    upload_params = step1['upload_params']

    boundary = '----BIOL1113LearningNotesUploadBoundary'
    parts = []
    for k, v in upload_params.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: {DOCX_CONTENT_TYPE}\r\n\r\n'.encode()
    )
    parts.append(file_bytes)
    parts.append(f'\r\n--{boundary}--\r\n'.encode())
    body = b''.join(parts)

    req2 = urllib.request.Request(
        upload_url,
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req2) as resp2:
            result = json.loads(resp2.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303):
            location = e.headers.get('Location')
            req3 = urllib.request.Request(location, headers={'Authorization': f'Bearer {token}'})
            with urllib.request.urlopen(req3) as resp3:
                result = json.loads(resp3.read().decode('utf-8'))
        else:
            body_text = e.read().decode('utf-8')
            print(f"  HTTP {e.code} uploading file bytes")
            print(f"  Response: {body_text[:300]}")
            raise

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/upload_learning_notes_to_canvas.py <target>")
        print("  target = sandbox, live, hybrid -- see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)

    if not SOURCE_DIR.exists():
        print(f"Error: {SOURCE_DIR} not found. Stage the .docx files there first.")
        sys.exit(1)

    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']

    print(f"Uploading {len(NOTES)} Learning Notes file(s) to Canvas course {course_id} "
          f"(target: {target_name})...")

    results = {}
    for key, filename in NOTES.items():
        path = SOURCE_DIR / filename
        if not path.exists():
            print(f"  [skip] {key} — source file not found: {filename}")
            continue
        result = upload_file(path, token, base_url, course_id)
        file_id = result.get('id')
        file_url = result.get('url')
        results[key] = file_url
        print(f"  [uploaded] {key} — file id {file_id}")

    print()
    print(f'Paste this into canvas_targets.py under the "{target_name}" target:')
    print()
    print('        "notes_urls": {')
    for key, url in results.items():
        print(f'            "{key}": "{url}",')
    print('        },')


if __name__ == '__main__':
    main()
