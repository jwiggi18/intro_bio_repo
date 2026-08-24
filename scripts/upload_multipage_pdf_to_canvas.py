#!/usr/bin/env python3
"""
upload_multipage_pdf_to_canvas.py — Upload the "Creating and Submitting a
Multipage PDF" instructional guide to a Canvas course's Files as a
hotlinkable PDF, and print the multipage_pdf_url line to paste into
canvas_targets.py.

Why a separate upload step from the page build: this is a PDF file (not
page HTML), so it goes through Canvas's Files API rather than the wiki
page/syllabus_body endpoints upload_to_canvas.py uses. Each Canvas course
gets its own copy of the file with its own URL -- files are not shared
across courses even when the course content is otherwise identical -- so
this needs to run once per target, same as upload_chart_to_canvas.py and
create_learning_notes_group.py.

Usage:
  python3 scripts/upload_multipage_pdf_to_canvas.py sandbox
  python3 scripts/upload_multipage_pdf_to_canvas.py live
  python3 scripts/upload_multipage_pdf_to_canvas.py hybrid

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - scripts/multipage_pdf_guide.pdf exists (source: Creating_and_Submitting_a_
    Multipage_PDF.docx in 1.courses_taught/1.Intro_Bio/1.2026, converted to PDF)

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

PDF_PATH = ROOT / "scripts" / "multipage_pdf_guide.pdf"


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


def upload_pdf(pdf_path, token, base_url, course_id):
    file_name = pdf_path.name
    file_bytes = pdf_path.read_bytes()

    # Step 1: tell Canvas we want to upload a file -- get a scoped upload URL.
    step1_data = urllib.parse.urlencode({
        'name': file_name,
        'size': len(file_bytes),
        'content_type': 'application/pdf',
        'parent_folder_path': 'documents',
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

    # Step 2: multipart POST the actual bytes to the upload URL Canvas gave us.
    boundary = '----BIOL1113MultipagePdfUploadBoundary'
    parts = []
    for k, v in upload_params.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: application/pdf\r\n\r\n'.encode()
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
            # Some Canvas upload targets confirm via a redirect rather than a body.
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
        print("Usage: python3 scripts/upload_multipage_pdf_to_canvas.py <target>")
        print("  target = sandbox, live, hybrid -- see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)

    if not PDF_PATH.exists():
        print(f"Error: {PDF_PATH} not found.")
        sys.exit(1)

    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']

    print(f"Uploading {PDF_PATH.name} to Canvas course {course_id} (target: {target_name})...")
    result = upload_pdf(PDF_PATH, token, base_url, course_id)

    file_id = result.get('id')
    file_url = result.get('url')  # signed download URL -- works without a login/publish state
    print(f"  [uploaded] file id {file_id}")
    print()
    print("Paste this into canvas_targets.py under the "
          f"\"{target_name}\" target:")
    print()
    print(f'    "multipage_pdf_url": "{file_url}",')


if __name__ == '__main__':
    main()
