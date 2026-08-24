#!/usr/bin/env python3
"""
upload_syllabus_to_canvas.py — Upload syllabus.html to Canvas course syllabus.

Canvas strips <style> blocks, so this script:
  1. Extracts CSS from the <style> block in syllabus.html
     (excludes @media print and @page rules — screen styles only)
  2. Inlines matching CSS rules as style="" attributes on each element
  3. Removes web-only elements (sticky nav, print button)
  4. Extracts body content and PUTs it to the Canvas syllabus API

Usage:
  python3 scripts/upload_syllabus_to_canvas.py

Requirements:
  - .env with CANVAS_TOKEN, CANVAS_BASE_URL, CANVAS_COURSE_ID
  - Python 3.8+, standard library only
"""

import sys
import re
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / 'syllabus.html'

# Borrow the CSS inliner logic from build/inline_css.py
sys.path.insert(0, str(ROOT / 'build'))
from inline_css import (
    parse_css,
    resolve_custom_properties,
    inline_styles_in_html,
    extract_body,
)


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def load_env():
    env_path = ROOT / '.env'
    if not env_path.exists():
        print("Error: .env not found. Copy .env.example and fill in credentials.")
        sys.exit(1)
    env = {}
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, val = line.partition('=')
        env[key.strip()] = val.strip()
    return env


def get_config():
    env = load_env()
    required = ['CANVAS_TOKEN', 'CANVAS_BASE_URL', 'CANVAS_COURSE_ID']
    missing = [k for k in required if not env.get(k) or 'your_' in env.get(k, '')]
    if missing:
        print(f"Error: Missing or unfilled values in .env: {', '.join(missing)}")
        sys.exit(1)
    return env


# ---------------------------------------------------------------------------
# CSS extraction
# ---------------------------------------------------------------------------

def extract_screen_css(html):
    """
    Pull the contents of the <style> block and strip @media print,
    @media screen wrappers, and @page rules — keeping only rules that
    apply to screen rendering, which is what Canvas will display.
    """
    style_m = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL | re.IGNORECASE)
    if not style_m:
        return ''
    css = style_m.group(1)

    # Remove nested @media blocks (handles one level of nesting)
    def remove_media(media_type, text):
        pattern = re.compile(
            r'@media\s+' + media_type + r'\s*\{', re.IGNORECASE
        )
        result = []
        i = 0
        while i < len(text):
            m = pattern.search(text, i)
            if not m:
                result.append(text[i:])
                break
            result.append(text[i:m.start()])
            depth = 1
            j = m.end()
            while j < len(text) and depth > 0:
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                j += 1
            i = j  # skip the entire @media block
        return ''.join(result)

    css = remove_media('print', css)
    css = remove_media('screen', css)

    # Remove @page rules
    css = re.sub(r'@page\s*[^{]*\{[^}]*\}', '', css)

    return css


# ---------------------------------------------------------------------------
# HTML cleanup — remove web-only elements before inlining
# ---------------------------------------------------------------------------

WEB_ONLY_CLASSES = ['sticky-nav', 'print-btn-wrap']

def remove_web_only_elements(html):
    """Remove elements that only make sense on the web (nav bar, print button)."""
    for cls in WEB_ONLY_CLASSES:
        # Match opening tag with this class, then remove to closing tag
        pattern = re.compile(
            r'<([\w]+)[^>]*class=["\'][^"\']*\b' + re.escape(cls) + r'\b[^"\']*["\'][^>]*>.*?</\1>',
            re.DOTALL | re.IGNORECASE
        )
        html = pattern.sub('', html)
    return html


# ---------------------------------------------------------------------------
# Canvas API
# ---------------------------------------------------------------------------

def canvas_put(path, token, base_url, data):
    url = f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}"
    body = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method='PUT')
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8')[:400]}")
        raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

import urllib.parse

def main():
    if not SRC.exists():
        print(f"Error: {SRC} not found.")
        sys.exit(1)

    config    = get_config()
    token     = config['CANVAS_TOKEN']
    base_url  = config['CANVAS_BASE_URL']
    course_id = config['CANVAS_COURSE_ID']

    print("Reading syllabus.html ...")
    html = SRC.read_text(encoding='utf-8')

    # 1. Extract screen CSS and resolve custom properties
    print("Extracting and resolving CSS ...")
    raw_css  = extract_screen_css(html)
    resolved = resolve_custom_properties(raw_css)
    rules    = parse_css(resolved)
    print(f"  {len(rules)} CSS rules loaded.")

    # 2. Remove web-only elements
    html = remove_web_only_elements(html)

    # 3. Inline CSS
    print("Inlining styles ...")
    html = inline_styles_in_html(html, rules)

    # 4. Extract body content only
    body_html = extract_body(html)

    # 5. Upload to Canvas syllabus
    print(f"Uploading to Canvas course {course_id} syllabus ...")
    canvas_put(
        f'courses/{course_id}',
        token, base_url,
        {'course[syllabus_body]': body_html}
    )
    print("Done. Open Canvas → Syllabus to review.")


if __name__ == '__main__':
    main()
