#!/usr/bin/env python3
"""
inline_css.py — CSS inliner for BIOL 1113 Canvas pages.

Canvas strips <style> and <link> tags from wiki pages. This script:
  1. Reads a source HTML file that references course-styles.css via <link>
  2. Inlines all matching CSS rules into each element's style="" attribute
  3. Outputs body-only HTML suitable for pasting into the Canvas HTML editor
     or uploading via the Canvas API

Usage:
  python3 build/inline_css.py week01/overview.html
  python3 build/inline_css.py week01/           (processes all .html in folder)
  python3 build/inline_css.py                   (processes all week*/  folders)

Output goes to build/biol1113/ mirroring the source structure.

Requires Python 3.8+. Standard library only — no external dependencies.
"""

import sys
import re
import os
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).parent.parent
CSS_PATH = ROOT / "course-styles.css"
BUILD_DIR = ROOT / "build" / "biol1113"


# ---------------------------------------------------------------------------
# CSS parsing — extract selector → declarations map
# ---------------------------------------------------------------------------

def parse_css(css_text):
    """
    Parse CSS into a list of (selector, declarations_string) tuples.
    Handles simple rules and :root custom properties.
    Strips comments first.
    """
    # Remove comments
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

    rules = []
    # Match selector { declarations }
    for match in re.finditer(r'([^{]+)\{([^}]*)\}', css_text):
        selector = match.group(1).strip()
        declarations = match.group(2).strip()
        if selector and declarations:
            rules.append((selector, declarations))
    return rules


def resolve_custom_properties(css_text):
    """
    Replace var(--name) references with their :root values.
    Simple single-pass resolution (no nested vars).
    """
    # Extract :root custom properties
    root_match = re.search(r':root\s*\{([^}]*)\}', css_text)
    custom_props = {}
    if root_match:
        for m in re.finditer(r'(--[\w-]+)\s*:\s*([^;]+);', root_match.group(1)):
            custom_props[m.group(1).strip()] = m.group(2).strip()

    def replacer(m):
        prop = m.group(1).strip()
        fallback = m.group(2).strip() if m.group(2) else ''
        return custom_props.get(prop, fallback)

    return re.sub(r'var\((--[\w-]+)(?:,\s*([^)]*))?\)', replacer, css_text)


# ---------------------------------------------------------------------------
# HTML processing — apply inline styles
# ---------------------------------------------------------------------------

VOID_ELEMENTS = {
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
    'link', 'meta', 'param', 'source', 'track', 'wbr'
}

SKIP_TAGS = {'style', 'script', 'link'}  # Remove these tags from output


def selector_matches(selector, tag, classes, element_id):
    """
    Evaluate whether a simple CSS selector matches an element.
    Supports: tag, .class, #id, tag.class, and simple descendant chains
    (for descendant selectors we apply conservatively to the last segment only).
    Pseudo-classes (:hover, :root, etc.) are skipped.
    """
    selector = selector.strip()

    # Skip pseudo-class-only and @-rules
    if selector.startswith('@') or selector.startswith(':root'):
        return False
    if ':' in selector and not re.search(r'\[.*:.*\]', selector):
        selector = re.sub(r':[\w-]+(\([^)]*\))?', '', selector).strip()
        if not selector:
            return False

    # For descendant/child selectors, only look at the last segment
    # (conservative: we apply the style if the element matches the last part)
    parts = re.split(r'\s+(?=[.#\w])', selector)
    selector = parts[-1].strip() if parts else selector

    # Parse simple selector: tag, class(es), id
    sel_tag = ''
    sel_classes = set()
    sel_id = ''

    tag_m = re.match(r'^([a-zA-Z][a-zA-Z0-9]*)', selector)
    if tag_m:
        sel_tag = tag_m.group(1).lower()
        selector = selector[len(sel_tag):]

    for cls_m in re.finditer(r'\.([a-zA-Z_][\w-]*)', selector):
        sel_classes.add(cls_m.group(1))

    id_m = re.search(r'#([\w-]+)', selector)
    if id_m:
        sel_id = id_m.group(1)

    # Match tag
    if sel_tag and sel_tag != tag:
        return False
    # Match id
    if sel_id and sel_id != element_id:
        return False
    # Match all classes
    if sel_classes and not sel_classes.issubset(classes):
        return False
    # If selector was only a class (no tag, no id), it matches any tag
    if not sel_tag and not sel_id and not sel_classes:
        return False

    return True


def merge_styles(existing, new_decls):
    """Merge new declarations into existing inline style string."""
    existing = existing.rstrip(';').strip() if existing else ''
    new_decls = new_decls.rstrip(';').strip()
    if existing:
        return existing + '; ' + new_decls
    return new_decls


def inline_styles_in_html(html_text, css_rules):
    """
    Walk the HTML and apply matching CSS rules as inline styles.
    Returns the modified HTML string.
    """
    # We'll do a regex-based tag replacement pass (not a full DOM parse,
    # but sufficient for well-formed template HTML)
    output = []
    pos = 0
    tag_pattern = re.compile(
        r'<(/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*)(/?)>',
        re.DOTALL
    )

    for m in tag_pattern.finditer(html_text):
        output.append(html_text[pos:m.start()])
        pos = m.end()

        closing_slash = m.group(1)   # '/' for closing tags
        tag = m.group(2).lower()
        attrs_str = m.group(3)
        self_closing = m.group(4)    # '/' for self-closing

        if closing_slash:
            output.append(m.group(0))
            continue

        if tag in SKIP_TAGS:
            # Skip to end of this tag's content
            end_pattern = re.compile(r'</' + re.escape(tag) + r'\s*>', re.IGNORECASE)
            end_m = end_pattern.search(html_text, pos)
            if end_m:
                pos = end_m.end()
            continue

        # Parse class and id from attrs
        class_m = re.search(r'class=["\']([^"\']*)["\']', attrs_str)
        id_m = re.search(r'id=["\']([^"\']*)["\']', attrs_str)
        style_m = re.search(r'style=["\']([^"\']*)["\']', attrs_str)

        classes = set(class_m.group(1).split()) if class_m else set()
        element_id = id_m.group(1) if id_m else ''
        existing_style = style_m.group(1) if style_m else ''

        # Collect matching rules
        matched_decls = []
        for selector, declarations in css_rules:
            if selector_matches(selector, tag, classes, element_id):
                matched_decls.append(declarations)

        if matched_decls:
            new_style = merge_styles(existing_style, '; '.join(matched_decls))
            # Replace or add style attribute
            if style_m:
                attrs_str = attrs_str[:style_m.start()] + f'style="{new_style}"' + attrs_str[style_m.end():]
            else:
                attrs_str = attrs_str + f' style="{new_style}"'

        output.append(f'<{tag}{attrs_str}{self_closing}>')

    output.append(html_text[pos:])
    return ''.join(output)


def extract_body(html_text):
    """Extract content between <body> and </body> tags."""
    body_m = re.search(r'<body[^>]*>(.*?)</body>', html_text, re.DOTALL | re.IGNORECASE)
    if body_m:
        return body_m.group(1).strip()
    return html_text.strip()


# ---------------------------------------------------------------------------
# Main build logic
# ---------------------------------------------------------------------------

def build_file(src_path, css_rules):
    """Process one HTML source file and write Canvas-ready output."""
    src_path = Path(src_path)
    if not src_path.exists():
        print(f"  [skip] {src_path} — not found")
        return

    html = src_path.read_text(encoding='utf-8')
    html = inline_styles_in_html(html, css_rules)
    body_html = extract_body(html)

    # Determine output path
    rel = src_path.relative_to(ROOT)
    out_path = BUILD_DIR / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body_html, encoding='utf-8')
    print(f"  [built] {rel} → build/biol1113/{rel}")


def collect_sources(target=None):
    """Return list of source HTML paths to build."""
    sources = []
    if target is None:
        # Build all week* folders
        for week_dir in sorted(ROOT.glob('week*/')):
            sources.extend(sorted(week_dir.glob('*.html')))
    else:
        p = Path(target)
        if p.is_dir():
            sources.extend(sorted(p.glob('*.html')))
        elif p.suffix == '.html':
            sources.append(p)
    return sources


def main():
    if not CSS_PATH.exists():
        print(f"Error: course-styles.css not found at {CSS_PATH}")
        sys.exit(1)

    raw_css = CSS_PATH.read_text(encoding='utf-8')
    resolved_css = resolve_custom_properties(raw_css)
    css_rules = parse_css(resolved_css)
    print(f"Loaded {len(css_rules)} CSS rules from course-styles.css")

    raw_target = sys.argv[1] if len(sys.argv) > 1 else None
    # Resolve target to absolute path so relative_to(ROOT) works correctly
    target = str((ROOT / raw_target).resolve()) if raw_target else None
    sources = collect_sources(target)

    if not sources:
        print("No HTML source files found.")
        sys.exit(0)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for src in sources:
        build_file(src, css_rules)

    print(f"\nDone. {len(sources)} file(s) written to build/biol1113/")


if __name__ == '__main__':
    main()
