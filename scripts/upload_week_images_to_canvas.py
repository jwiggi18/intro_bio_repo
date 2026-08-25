#!/usr/bin/env python3
"""
upload_week_images_to_canvas.py — Upload the weekly "cute happy img" (one
per week, sits at the bottom of every week page) to a Canvas course's Files
as hotlinkable images, and print the week_image_urls dict to paste into
canvas_targets.py.

Why a separate upload step from the page build: these are .JPG files (not
page HTML), so they go through Canvas's Files API rather than the wiki
page/syllabus_body endpoints upload_to_canvas.py uses. Each Canvas course
gets its own copy of every file with its own URL -- files are not shared
across courses even when the course content is otherwise identical -- so
this needs to run once per target, same as upload_learning_notes_to_canvas.py
and upload_chart_to_canvas.py.

Source files live in
"1.courses_taught/1.Intro_Bio/1.2026/cute_happy_imgs" (iCloud, not this
repo) and are staged into scripts/week_images_source/ before running this
script -- copy the 15 weekly JPGs in there with matching names if that
folder doesn't exist yet.

Usage:
  python3 scripts/upload_week_images_to_canvas.py sandbox
  python3 scripts/upload_week_images_to_canvas.py live
  python3 scripts/upload_week_images_to_canvas.py hybrid

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - scripts/week_images_source/*.JPG present (one file per WEEK_IMAGES entry)

Requires Python 3.8+. Standard library only.
"""

import sys
import json
import mimetypes
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target

SOURCE_DIR = ROOT / "scripts" / "week_images_source"

# week key -> source filename (source of truth: the cute_happy_imgs/ folder
# on iCloud). Week 15 has two candidate files in that folder
# (Week15_dino_lemon.JPG and Week_15_Octopus_purse.JPG) -- dino_lemon is the
# one Jodie chose (Aug 24, 2026), matching the WeekN_ naming every other
# week uses.
WEEK_IMAGES = {
    "week01": "Week1_wierd_little_things.JPG",
    "week02": "Week2_shark_squid_jelly.JPG",
    "week03": "Week3_isnt_failure.JPG",
    "week04": "Week4_bee_umbrella.JPG",
    "week05": "Week5_naturalism_journal.JPG",
    "week06": "Week6_happy_skink.JPG",
    "week07": "Week7_octopods_bikes.JPG",
    "week08": "Week8_crows.JPG",
    "week09": "Week9_possum_dont_give_up.JPG",
    "week10": "Week10_octopus_stars.JPG",
    "week11": "Week11_being_ready_myth_.JPG",
    "week12": "Week12_only_sidequests.JPG",
    "week13": "Week13_whack_energy.JPG",
    "week14": "Week14_duck_butt.JPG",
    "week15": "Week15_dino_lemon.JPG",
}


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
    file_name = file_path.name
    file_bytes = file_path.read_bytes()
    content_type = mimetypes.guess_type(file_name)[0] or 'image/jpeg'

    step1_data = urllib.parse.urlencode({
        'name': file_name,
        'size': len(file_bytes),
        'content_type': content_type,
        'parent_folder_path': 'week_images',
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

    boundary = '----BIOL1113WeekImageUploadBoundary'
    parts = []
    for k, v in upload_params.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: {content_type}\r\n\r\n'.encode()
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
        print("Usage: python3 scripts/upload_week_images_to_canvas.py <target>")
        print("  target = sandbox, live, hybrid -- see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)

    if not SOURCE_DIR.exists():
        print(f"Error: {SOURCE_DIR} not found. Stage the weekly .JPG files there first.")
        sys.exit(1)

    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']

    print(f"Uploading {len(WEEK_IMAGES)} weekly image(s) to Canvas course {course_id} "
          f"(target: {target_name})...")

    results = {}
    for key, filename in WEEK_IMAGES.items():
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
    print(f'Paste this into canvas_targets.py under the "{target_name}" target '
          f'(replacing "week_image_urls": {{}}):')
    print()
    print('        "week_image_urls": {')
    for key, url in results.items():
        print(f'            "{key}": "{url}",')
    print('        },')


if __name__ == '__main__':
    main()
