#!/usr/bin/env python3
"""
inline_css.py — CSS inliner + per-course link resolver for BIOL 1113 Canvas
pages.

Canvas strips <style> and <link> tags from wiki pages. This script:
  1. Reads a source HTML file that references course-styles.css via <link>
  2. Inlines all matching CSS rules into each element's style="" attribute
  3. Resolves the small set of course-specific placeholders that stay
     unfilled in the checked-in source ({{LEARNING_NOTES_URL}},
     {{COURSE_ID}}) to the real values for the target Canvas course, using
     canvas_targets.py — this repo feeds more than one Canvas course, and
     the source files are written to be identical across all of them
  4. Outputs body-only HTML suitable for pasting into the Canvas HTML editor
     or uploading via the Canvas API

Usage:
  python3 build/inline_css.py sandbox                      (all files, sandbox course)
  python3 build/inline_css.py live                         (all files, live course)
  python3 build/inline_css.py sandbox week01/               (one week)
  python3 build/inline_css.py sandbox week01/overview.html  (one file)

Output goes to build/biol1113-<target>/ mirroring the source structure, so
different targets' builds never overwrite each other.

Requires Python 3.8+. Standard library only — no external dependencies.
"""

import sys
import re
import os
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from canvas_targets import get_target

CSS_PATH = ROOT / "course-styles.css"
WEEK_DIR_RE = re.compile(r"week0*([0-9]+)$")


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


def strip_at_rules(css_text):
    """Remove @media/@page/etc. blocks entirely (brace-depth aware, since
    they nest other rule blocks inside them). Inline styles can't express
    conditional or print-only rules anyway — Canvas only ever renders on
    screen — and parse_css() below doesn't handle nested braces, so these
    have to come out before parsing rather than being (mis)parsed."""
    out = []
    i, n = 0, len(css_text)
    while i < n:
        if css_text[i] == '@':
            brace_start = css_text.find('{', i)
            if brace_start == -1:
                out.append(css_text[i:])
                break
            depth = 1
            j = brace_start + 1
            while j < n and depth > 0:
                if css_text[j] == '{':
                    depth += 1
                elif css_text[j] == '}':
                    depth -= 1
                j += 1
            i = j
        else:
            out.append(css_text[i])
            i += 1
    return ''.join(out)


def extract_own_style_rules(html_text):
    """Some source files (syllabus.html, written before the shared
    course-styles.css convention existed) carry their own embedded <style>
    block instead of linking course-styles.css. Canvas strips <style> tags
    the same as it strips <link> tags, so without this those rules just
    silently vanish — extract and parse them the same way course-styles.css
    is parsed, so they get inlined too instead of disappearing."""
    m = re.search(r'<style[^>]*>(.*?)</style>', html_text, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    own_css = strip_at_rules(m.group(1))
    own_css = resolve_custom_properties(own_css)
    return parse_css(own_css)


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
    # Pseudo-ELEMENTS (::before, ::after, or the legacy single-colon form)
    # generate content/styling that doesn't belong to the real element at
    # all -- an inline style="" attribute has no way to express them, and
    # naively stripping down to the base selector (like the pseudo-CLASS
    # handling below does for :hover etc.) would leak their declarations
    # (e.g. `content: "..."`) onto the actual element. Bail out entirely
    # before the generic stripping gets a chance to do that.
    if re.search(r':{1,2}(before|after|first-line|first-letter|placeholder|selection|marker)\b', selector):
        return False
    if ':' in selector and not re.search(r'\[.*:.*\]', selector):
        selector = re.sub(r':[\w-]+(\([^)]*\))?', '', selector).strip()
        if not selector:
            return False

    # For descendant/child selectors, only look at the last segment —
    # BUT skip if the last segment is a bare tag with no class or id.
    # Bare-tag descendant selectors (e.g. ".objectives-box h2", ".task-list li")
    # cannot be accurately evaluated without DOM ancestry and would match
    # unrelated elements, corrupting their styles.
    parts = re.split(r'\s+(?=[.#\w])', selector)
    if len(parts) > 1:
        last = parts[-1].strip()
        # If last segment is only a tag (no '.' or '#'), skip — too risky
        if re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', last):
            return False
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
    """
    Merge new declarations into existing inline style string.
    Deduplicates properties — last declaration wins (CSS cascade order).
    """
    combined = (existing.rstrip(';').strip() + '; ' + new_decls.rstrip(';').strip()
                if existing else new_decls.rstrip(';').strip())
    # Parse into ordered dict so last value per property wins
    props = {}
    for decl in combined.split(';'):
        decl = decl.strip()
        if ':' in decl:
            prop, _, val = decl.partition(':')
            prop = prop.strip()
            val = val.strip()
            if prop and val:
                props[prop] = val  # overwrites earlier value — last wins
    return '; '.join(f'{p}: {v}' for p, v in props.items())


def extract_font_weight(style_str):
    """Parse a merged style string into (props_without_font_weight, is_bold).
    is_bold is True when font-weight is 'bold'/'bolder' or a numeric value
    >= 600. Returns (rebuilt_style_string, is_bold)."""
    if not style_str:
        return style_str, False
    props = {}
    for decl in style_str.split(';'):
        decl = decl.strip()
        if ':' in decl:
            prop, _, val = decl.partition(':')
            prop, val = prop.strip(), val.strip()
            if prop and val:
                props[prop] = val
    fw = props.pop('font-weight', None)
    is_bold = False
    if fw:
        fw_norm = fw.strip().lower()
        if fw_norm in ('bold', 'bolder'):
            is_bold = True
        else:
            digits = re.match(r'^(\d+)$', fw_norm)
            if digits and int(digits.group(1)) >= 600:
                is_bold = True
    return '; '.join(f'{p}: {v}' for p, v in props.items()), is_bold


def inline_styles_in_html(html_text, css_rules):
    """
    Walk the HTML and apply matching CSS rules as inline styles.

    Canvas strips the `font-weight` CSS property from every inline style
    attribute on save (confirmed empirically against both the syllabus_body
    field and regular wiki_page bodies via the API — every other property
    survives, font-weight silently vanishes). So instead of shipping
    font-weight in the style attribute (dead weight Canvas will delete
    anyway), any element whose merged style resolves to bold gets that
    declaration stripped and its content wrapped in <strong>...</strong>
    instead — real HTML semantics, not CSS, so it actually survives.

    Returns the modified HTML string.
    """
    # We'll do a regex-based tag replacement pass (not a full DOM parse,
    # but sufficient for well-formed template HTML)
    output = []
    pos = 0
    open_stack = []  # tracks open (non-void, non-self-closing) tags so the
                      # matching close tag can get the </strong> pairing
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
            if open_stack and open_stack[-1]['tag'] == tag:
                entry = open_stack.pop()
                if entry['bold_wrap']:
                    output.append('</strong>')
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

        # Merge existing inline style + matched CSS rules regardless of
        # whether any rules matched — font-weight can arrive via either
        # path (a hand-written style="" attribute, or a class-based rule)
        # and both need the same strip-and-wrap treatment.
        combined = merge_styles(existing_style, '; '.join(matched_decls)) if matched_decls else existing_style
        new_style, bold_wrap = extract_font_weight(combined)
        if tag in ('strong', 'b'):
            # Already semantically bold (and course-styles.css has a bare
            # `strong { font-weight: 700 }` reset that would otherwise match
            # here) — wrapping it in another <strong> would just nest it
            # inside itself.
            bold_wrap = False

        if new_style != existing_style:
            if style_m:
                replacement = f'style="{new_style}"' if new_style else ''
                attrs_str = attrs_str[:style_m.start()] + replacement + attrs_str[style_m.end():]
            elif new_style:
                attrs_str = attrs_str + f' style="{new_style}"'

        output.append(f'<{tag}{attrs_str}{self_closing}>')

        if not self_closing and tag not in VOID_ELEMENTS:
            open_stack.append({'tag': tag, 'bold_wrap': bold_wrap})
            if bold_wrap:
                output.append('<strong>')
        # Self-closing/void elements can't wrap text content — font-weight
        # was still stripped above (Canvas would kill it anyway), there's
        # just nothing to wrap since these elements have no children.

    output.append(html_text[pos:])
    return ''.join(output)


def extract_body(html_text):
    """Extract content between <body> and </body> tags."""
    body_m = re.search(r'<body[^>]*>(.*?)</body>', html_text, re.DOTALL | re.IGNORECASE)
    if body_m:
        return body_m.group(1).strip()
    return html_text.strip()


def week_num_from_path(src_path):
    """weekNN/week.html -> NN (int). Returns None for non-week files
    (homepage, syllabus, etc.) — those don't have a Learning Notes link."""
    m = WEEK_DIR_RE.match(src_path.parent.name)
    return int(m.group(1)) if m else None


def resolve_placeholders(html_text, src_path, target_config):
    """Fill in the course-specific placeholders that stay unresolved in the
    checked-in source so the same files can build against any configured
    Canvas course (see canvas_targets.py)."""
    html_text = html_text.replace("{{COURSE_ID}}", str(target_config["course_id"]))

    if "{{LEARNING_NOTES_URL}}" in html_text:
        num = week_num_from_path(src_path)
        assignment_id = target_config.get("learning_notes_ids", {}).get(num) if num else None
        if assignment_id:
            url = f"{target_config['base_url'].rstrip('/')}/courses/{target_config['course_id']}/assignments/{assignment_id}"
            html_text = html_text.replace("{{LEARNING_NOTES_URL}}", url)
        else:
            # This target doesn't have a Learning Notes assignment for this
            # week yet (e.g. the live course before create_learning_notes_group.py
            # has been run against it) — fall back to unlinked rather than
            # ship a broken link.
            html_text = html_text.replace(
                '<li><a href="{{LEARNING_NOTES_URL}}">Learning Notes</a></li>',
                '<li class="unlinked">Learning Notes</li>'
            )
            print(f"  [warn] {src_path.relative_to(ROOT)} — no Learning Notes id for week {num} "
                  f"in this target; left unlinked")

    if "{{SMALL_GROUP_URL}}" in html_text:
        # Hybrid-only placeholder (Small Group Participation, replaces the
        # Blog Post/Blog Comment links on sandbox/live) — same
        # exists-or-fall-back-to-unlinked pattern as Learning Notes above.
        num = week_num_from_path(src_path)
        assignment_id = target_config.get("small_group_ids", {}).get(num) if num else None
        if assignment_id:
            url = f"{target_config['base_url'].rstrip('/')}/courses/{target_config['course_id']}/assignments/{assignment_id}"
            html_text = html_text.replace("{{SMALL_GROUP_URL}}", url)
        else:
            html_text = html_text.replace(
                '<li><a href="{{SMALL_GROUP_URL}}">Small Group Participation</a></li>',
                '<li class="unlinked">Small Group Participation</li>'
            )
            print(f"  [warn] {src_path.relative_to(ROOT)} — no Small Group Participation id for week {num} "
                  f"in this target; left unlinked")

    if "{{CHART_IMAGE_URL}}" in html_text:
        chart_url = target_config.get("chart_image_url")
        if chart_url:
            html_text = html_text.replace("{{CHART_IMAGE_URL}}", chart_url)
        else:
            print(f"  [warn] {src_path.relative_to(ROOT)} — no chart_image_url set for this "
                  f"target; {{{{CHART_IMAGE_URL}}}} left UNRESOLVED (image will be broken). "
                  f"Run scripts/upload_chart_to_canvas.py against this target first.")

    if "{{MULTIPAGE_PDF_URL}}" in html_text:
        pdf_url = target_config.get("multipage_pdf_url")
        if pdf_url:
            html_text = html_text.replace("{{MULTIPAGE_PDF_URL}}", pdf_url)
        else:
            print(f"  [warn] {src_path.relative_to(ROOT)} — no multipage_pdf_url set for this "
                  f"target; {{{{MULTIPAGE_PDF_URL}}}} left UNRESOLVED (link will be broken). "
                  f"Run scripts/upload_multipage_pdf_to_canvas.py against this target first.")

    if "{{SYLLABUS_PDF_URL}}" in html_text:
        syllabus_pdf_url = target_config.get("syllabus_pdf_url")
        if syllabus_pdf_url:
            html_text = html_text.replace("{{SYLLABUS_PDF_URL}}", syllabus_pdf_url)
        else:
            print(f"  [warn] {src_path.relative_to(ROOT)} — no syllabus_pdf_url set for this "
                  f"target; {{{{SYLLABUS_PDF_URL}}}} left UNRESOLVED (link will be broken). "
                  f"Run scripts/upload_syllabus_pdf_to_canvas.py against this target first.")

    if "{{BLOG_POST_URL}}" in html_text:
        num = week_num_from_path(src_path)
        assignment_id = target_config.get("blog_post_ids", {}).get(num) if num else None
        if assignment_id:
            url = f"{target_config['base_url'].rstrip('/')}/courses/{target_config['course_id']}/assignments/{assignment_id}"
            html_text = html_text.replace("{{BLOG_POST_URL}}", url)
        else:
            html_text = html_text.replace(
                '<li><a href="{{BLOG_POST_URL}}">Blog Post</a></li>',
                '<li class="unlinked">Blog Post</li>'
            )
            print(f"  [warn] {src_path.relative_to(ROOT)} — no Blog Post id for week {num} "
                  f"in this target; left unlinked")

    if "{{BLOG_COMMENT_URL}}" in html_text:
        num = week_num_from_path(src_path)
        assignment_id = target_config.get("blog_comment_ids", {}).get(num) if num else None
        if assignment_id:
            url = f"{target_config['base_url'].rstrip('/')}/courses/{target_config['course_id']}/assignments/{assignment_id}"
            html_text = html_text.replace("{{BLOG_COMMENT_URL}}", url)
        else:
            html_text = html_text.replace(
                '<li><a href="{{BLOG_COMMENT_URL}}">Blog Comment Declaration</a></li>',
                '<li class="unlinked">Blog Comment Declaration</li>'
            )
            print(f"  [warn] {src_path.relative_to(ROOT)} — no Blog Comment Declaration id for "
                  f"week {num} in this target; left unlinked")

    if "{{SLIDES_URL:" in html_text:
        # Generic per-video placeholder: {{SLIDES_URL:<key>}}, where <key> is
        # the source video's filename stem (see scripts/extract_video_slides.py
        # output / scripts/upload_slides_to_canvas.py). One placeholder per
        # video rather than per week, since a week can have several videos
        # each with their own slide deck.
        slides_urls = target_config.get("slides_urls", {})

        def _resolve_slides_url(match):
            key = match.group(1)
            url = slides_urls.get(key)
            if url:
                return url
            print(f"  [warn] {src_path.relative_to(ROOT)} — no slides_url for '{key}' in this "
                  f"target; {{{{SLIDES_URL:{key}}}}} left UNRESOLVED (link will be broken). "
                  f"Run scripts/upload_slides_to_canvas.py against this target first.")
            return match.group(0)

        html_text = re.sub(r"\{\{SLIDES_URL:([A-Za-z0-9_-]+)\}\}", _resolve_slides_url, html_text)

    if "{{NOTES_URL:" in html_text:
        # Generic per-video placeholder for the guided Learning Notes .docx
        # handout (scripts/upload_learning_notes_to_canvas.py output), same
        # pattern as SLIDES_URL above -- one placeholder per video, keyed by
        # the video's filename stem from video_transcripts/ (see
        # 1.courses_taught/1.Intro_Bio/1.2026/learning_notes/).
        notes_urls = target_config.get("notes_urls", {})

        def _resolve_notes_url(match):
            key = match.group(1)
            url = notes_urls.get(key)
            if url:
                return url
            print(f"  [warn] {src_path.relative_to(ROOT)} — no notes_url for '{key}' in this "
                  f"target; {{{{NOTES_URL:{key}}}}} left UNRESOLVED (link will be broken). "
                  f"Run scripts/upload_learning_notes_to_canvas.py against this target first.")
            return match.group(0)

        html_text = re.sub(r"\{\{NOTES_URL:([A-Za-z0-9_-]+)\}\}", _resolve_notes_url, html_text)

    return html_text


# ---------------------------------------------------------------------------
# Main build logic
# ---------------------------------------------------------------------------

def build_file(src_path, css_rules, target_name, target_config, build_dir, content_root):
    """Process one HTML source file and write Canvas-ready output."""
    src_path = Path(src_path)
    if not src_path.exists():
        print(f"  [skip] {src_path} — not found")
        return

    html = src_path.read_text(encoding='utf-8')

    own_rules = extract_own_style_rules(html)
    file_rules = css_rules + own_rules if own_rules else css_rules
    if own_rules:
        print(f"  [note] {src_path.relative_to(ROOT)} has its own <style> block — "
              f"inlining {len(own_rules)} rule(s) from it too")

    html = inline_styles_in_html(html, file_rules)
    body_html = extract_body(html)
    body_html = resolve_placeholders(body_html, src_path, target_config)

    # Determine output path, relative to this target's content root (not
    # always ROOT — e.g. hybrid/ — so build output stays flat/clean:
    # build/biol1113-hybrid/week01/week.html, not .../hybrid/week01/week.html).
    rel = src_path.relative_to(content_root)
    out_path = build_dir / rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body_html, encoding='utf-8')
    print(f"  [built] {rel} → build/biol1113-{target_name}/{rel}")


def collect_sources(content_root, subset=None):
    """Return list of source HTML paths to build, rooted at content_root
    (ROOT for sandbox/live, ROOT/hybrid for the hybrid target — see
    canvas_targets.py's content_root field).
    Processes:
      - week*/week.html  (one per week folder)
      - root-level *.html files (homepage, syllabus, blog pages, etc.)
    Legacy stub files (overview/materials/assignments) inside week folders
    are ignored even if present.
    """
    sources = []
    if subset is None:
        # Root-level HTML files (homepage, syllabus, blog-setup, blog-directory, etc.)
        for html_file in sorted(content_root.glob('*.html')):
            sources.append(html_file)
        # Week folders — single week.html per folder
        for week_dir in sorted(content_root.glob('week*/')):
            week_file = week_dir / 'week.html'
            if week_file.exists():
                sources.append(week_file)
    else:
        p = Path(subset)
        if p.is_dir():
            week_file = p / 'week.html'
            if week_file.exists():
                sources.append(week_file)
        elif p.suffix == '.html':
            sources.append(p)
    return sources


def main():
    if not CSS_PATH.exists():
        print(f"Error: course-styles.css not found at {CSS_PATH}")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python3 build/inline_css.py <target> [file/folder]")
        print("  target = sandbox, live, hybrid, etc. — see canvas_targets.py")
        sys.exit(1)

    target_name = sys.argv[1]
    target_config = get_target(target_name)  # exits with a clear error if unknown/unconfigured
    build_dir = ROOT / "build" / f"biol1113-{target_name}"
    content_root = ROOT / target_config.get("content_root", ".")

    raw_css = CSS_PATH.read_text(encoding='utf-8')
    resolved_css = resolve_custom_properties(raw_css)
    css_rules = parse_css(resolved_css)
    print(f"Loaded {len(css_rules)} CSS rules from course-styles.css")
    print(f"Target: {target_name} (course {target_config['course_id']}, content root: {content_root.relative_to(ROOT) if content_root != ROOT else '.'})")

    raw_subset = sys.argv[2] if len(sys.argv) > 2 else None
    # Resolve subset to absolute path so relative_to(content_root) works correctly
    subset = str((content_root / raw_subset).resolve()) if raw_subset else None
    sources = collect_sources(content_root, subset)

    if not sources:
        print("No HTML source files found.")
        sys.exit(0)

    build_dir.mkdir(parents=True, exist_ok=True)
    for src in sources:
        build_file(src, css_rules, target_name, target_config, build_dir, content_root)

    print(f"\nDone. {len(sources)} file(s) written to build/biol1113-{target_name}/")


if __name__ == '__main__':
    main()
