#!/usr/bin/env python3
"""
upload_chart_to_canvas.py — Upload the rendered grade-chart PNG to a Canvas
course's Files as a hotlinkable image, and print the chart_image_url line to
paste into canvas_targets.py.

Why a separate upload step from the page build: the chart is a PNG file (not
page HTML), so it goes through Canvas's Files API rather than the wiki
page/syllabus_body endpoints upload_to_canvas.py uses. Each Canvas course
gets its own copy of the file with its own URL — files are not shared across
courses even when the course content is otherwise identical — so this needs
to run once per target, same as create_learning_notes_group.py.

Usage:
  python3 scripts/generate_chart_png.py          # regenerate the PNG first if numbers changed
  python3 scripts/upload_chart_to_canvas.py sandbox
  python3 scripts/upload_chart_to_canvas.py live

Requirements:
  - .env file in repo root with CANVAS_TOKEN
  - scripts/chart_output.png exists (run generate_chart_png.py first)

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

DEFAULT_PNG_PATH = ROOT / "scripts" / "chart_output.png"


def png_path_for(target_name):
    """Pick the right chart PNG for this target. Targets whose grade
    breakdown genuinely differs (e.g. hybrid, with Small Group Participation
    instead of Blog Posts/Comments) get their own chart_output_<target>.png;
    everything else falls back to the shared chart_output.png."""
    per_target = ROOT / "scripts" / f"chart_output_{target_name}.png"
    return per_target if per_target.exists() else DEFAULT_PNG_PATH


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


def upload_chart(png_path, token, base_url, course_id):
    file_name = png_path.name
    file_bytes = png_path.read_bytes()

    # Step 1: tell Canvas we want to upload a file -- get a scoped upload URL.
    step1_data = urllib.parse.urlencode({
        'name': file_name,
        'size': len(file_bytes),
        'content_type': 'image/png',
        'parent_folder_path': 'images',
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
    boundary = '----BIOL1113ChartUploadBoundary'
    parts = []
    for k, v in upload_params.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f'Content-Type: image/png\r\n\r\n'.encode()
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
        print("Usage: python3 scripts/upload_chart_to_canvas.py <target>")
        print("  target = sandbox, live, etc. -- see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)
    png_path = png_path_for(target_name)

    if not png_path.exists():
        print(f"Error: {png_path} not found. Run scripts/generate_chart_png.py first.")
        sys.exit(1)

    token = get_token()
    base_url = target_config['base_url']
    course_id = target_config['course_id']

    print(f"Uploading {png_path.name} to Canvas course {course_id} (target: {target_name})...")
    result = upload_chart(png_path, token, base_url, course_id)

    file_id = result.get('id')
    file_url = result.get('url')  # signed download URL -- works without a login/publish state
    print(f"  [uploaded] file id {file_id}")
    print()
    print("Paste this into canvas_targets.py under the "
          f"\"{target_name}\" target:")
    print()
    print(f'    "chart_image_url": "{file_url}",')


if __name__ == '__main__':
    main()
