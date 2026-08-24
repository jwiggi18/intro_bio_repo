#!/usr/bin/env python3
"""
extract_video_slides.py — Turn a VideoScribe-style (whiteboard/hand-drawn
reveal) instructional video into a printable/accessible PDF "slide deck" by
grabbing a still frame at each point where the animation is holding still
(i.e. the drawing has paused so the narration can catch up), rather than
sampling on a fixed timer or on every pixel change.

Why this approach: VideoScribe content is *continuously* animating (the pen
is always drawing something), so naive frame-diff/scene-detection tools fire
constantly and produce hundreds of near-duplicate images. This script uses
ffmpeg's `freezedetect` filter to find genuinely static holds — the moments
the video is actually "resting" — then filters/thins/dedupes them so you get
roughly one image per drawn element instead of one per micro-pause between
brush strokes or a flood of frames from continuous motion.

Two-phase design (so a long video's scan can be split across multiple runs
if you're driving this from something with a short per-call time budget):

    # one call, does everything (fine for shorter videos):
    python3 extract_video_slides.py run INPUT.mp4 OUTPUT.pdf [options]

    # OR, split the slow part (the freezedetect scan) into chunks:
    python3 extract_video_slides.py scan INPUT.mp4 EVENTS.json --start 0 --dur 300
    python3 extract_video_slides.py scan INPUT.mp4 EVENTS.json --start 300 --dur 300
    python3 extract_video_slides.py scan INPUT.mp4 EVENTS.json --start 600 --dur 300
    python3 extract_video_slides.py build INPUT.mp4 EVENTS.json OUTPUT.pdf [options]

`scan` appends to EVENTS.json each time it's called (safe to call repeatedly
over consecutive time ranges); `build` reads it, does the filtering/thinning/
dedup/extraction/PDF-assembly, and is the only phase that needs the tuning
options below.

Options for `run`/`build` (defaults tuned for a dense, per-element slide
deck — roughly one slide per drawn item/beat, ~25-40 slides for a 5-6 min
video):
    --min-hold SECONDS      Minimum hold duration to count as a real pause
                             (screens out only sub-second freezedetect noise,
                             not genuine short pauses between drawn
                             elements). Default 1.5.
    --merge-gap SECONDS     Bridges freeze events that are literally
                             overlapping/touching. Default 0.0 (off) —
                             consecutive VideoScribe holds are usually
                             visually distinct elements even when they sit
                             0.0s apart in the freeze log, so merging them by
                             default would undo the density this mode is for.
                             Raise this only if you want fewer, coarser
                             slides.
    --min-spacing SECONDS   Minimum time between two selected slides. If
                             candidates are closer than this, only the
                             longest hold is kept. Default 2.5.
    --max-slides N          Hard cap on number of slides (keeps the N
                             longest holds if more are found). Default 60.
    --label / --no-label    Stamp "<video name> — MM:SS" in the corner of
                             each slide for traceability back to the video.
                             Default: on.
    --freeze-db DB          freezedetect noise floor in dB (more negative =
                             stricter/requires a more perfectly still frame).
                             Default -30 (also used by `scan`).

`build` also runs two cleanup passes on top of the raw candidate list:
  - a stability check (re-samples short holds a moment later and drops any
    candidate that changed a lot — catches frames caught mid scene-wipe)
  - a near-duplicate check against the previously kept slide (catches cases
    where ffmpeg logs one long pause as two adjacent freeze events)

If a video has few or no long holds (e.g. it's a talking-head recording, not
a VideoScribe animation), `build` falls back to evenly spaced sampling every
~45 seconds so you still get a usable handout, and prints a warning.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

import img2pdf
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def run_freezedetect(path, freeze_db, start=None, dur=None):
    """Run a downscaled (but full-framerate) freezedetect pass over the
    whole file, or a [start, start+dur) window of it, and return a list of
    (start, end) tuples for every raw freeze event >= 1s (fine-grained;
    filtering/thinning happens in `build`). Note: framerate is NOT reduced
    here — dropping fps smooths over the constant small pen motion in
    whiteboard-animation video and makes the whole video look "frozen",
    which defeats the purpose."""
    cmd = ["ffmpeg"]
    if start is not None:
        cmd += ["-ss", f"{start:.2f}"]
    if dur is not None:
        cmd += ["-t", f"{dur:.2f}"]
    cmd += [
        "-i", path, "-an",
        "-vf", f"scale=320:-1,freezedetect=n={freeze_db}dB:d=1.0",
        "-map", "0:v", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    log = proc.stderr

    starts = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"freeze_end:\s*([\d.]+)", log)]
    events = list(zip(starts, ends[: len(starts)]))
    if start is not None:
        # freezedetect timestamps are relative to the -ss'd input; shift
        # back to absolute video time.
        events = [(s + start, e + start) for s, e in events]
    return events


def merge_events(events, merge_gap):
    """Bridge only events that are strictly back-to-back-or-overlapping
    within merge_gap. NOTE: many consecutive VideoScribe freeze events sit
    exactly 0.0s apart (one ends the instant the next starts) despite being
    visually distinct drawn elements — a merge_gap of 0 (the default) means
    those are treated as separate slides, which is what you want for a dense,
    per-element deck. Raise merge_gap only if you want fewer, coarser
    slides."""
    if not events:
        return []
    events = sorted(events)
    merged = [list(events[0])]
    for s, e in events[1:]:
        if s - merged[-1][1] < merge_gap:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def thin_by_spacing(clusters, min_spacing):
    """Given clusters sorted by start time, drop any cluster whose start is
    within min_spacing of the previously KEPT cluster, unless it's
    meaningfully longer (then it replaces the kept one)."""
    if not clusters:
        return []
    clusters = sorted(clusters, key=lambda c: c[0])
    kept = [clusters[0]]
    for c in clusters[1:]:
        prev = kept[-1]
        if c[0] - prev[0] < min_spacing:
            if (c[1] - c[0]) > (prev[1] - prev[0]):
                kept[-1] = c
        else:
            kept.append(c)
    return kept


def extract_frame(path, timestamp, out_png):
    cmd = [
        "ffmpeg", "-y", "-ss", f"{timestamp:.2f}", "-i", path,
        "-frames:v", "1", "-q:v", "2", out_png,
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def _thumb(png_path):
    return Image.open(png_path).convert("L").resize((64, 40))


def mean_diff(png_a, png_b):
    """0-255 scale mean absolute pixel difference between two images,
    compared as small grayscale thumbnails (cheap, robust to tiny encoding
    noise, sensitive to any real visual change)."""
    ta, tb = _thumb(png_a), _thumb(png_b)
    return ImageStat.Stat(ImageChops.difference(ta, tb)).mean[0]


def stamp_label(png_path, text):
    img = Image.open(png_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    size = max(14, img.width // 90)
    try:
        font = ImageFont.truetype(FONT_PATH, size)
    except Exception:
        font = ImageFont.load_default()
    pad = size // 2
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = img.width - tw - pad * 3
    y = img.height - th - pad * 3
    draw.rectangle([x - pad, y - pad, x + tw + pad, y + th + pad],
                    fill=(255, 255, 255))
    draw.text((x, y), text, fill=(40, 40, 40), font=font)
    img.save(png_path)


def fmt_ts(t):
    m = int(t // 60)
    s = int(t % 60)
    return f"{m:02d}:{s:02d}"


def cmd_scan(args):
    events = run_freezedetect(args.input, args.freeze_db, args.start, args.dur)
    duration = ffprobe_duration(args.input)

    data = {"duration": duration, "events": []}
    if os.path.exists(args.events):
        with open(args.events) as f:
            data = json.load(f)
    data["duration"] = duration
    data["events"].extend(events)
    with open(args.events, "w") as f:
        json.dump(data, f)

    window = f"[{args.start or 0:.0f}s, {(args.start or 0) + (args.dur or duration):.0f}s)"
    print(f"scanned {window}: +{len(events)} events (total now {len(data['events'])})")


def build_pdf(input_path, events, duration, output_path, args, video_name):
    merged = merge_events(events, args.merge_gap)
    real_holds = [(s, e) for s, e in merged if (e - s) >= args.min_hold]
    slides = thin_by_spacing(real_holds, args.min_spacing)

    fallback = False
    if len(slides) < 2:
        fallback = True
        step = 45.0
        t = min(5.0, duration / 4)
        slides = []
        while t < duration - 2:
            slides.append((t, t))
            t += step

    if len(slides) > args.max_slides:
        slides = sorted(slides, key=lambda c: (c[1] - c[0]), reverse=True)[: args.max_slides]
        slides = sorted(slides, key=lambda c: c[0])

    with tempfile.TemporaryDirectory() as tmp:
        pngs = []
        dropped_transition = 0
        dropped_duplicate = 0
        prev_kept_png = None
        for i, (s, e) in enumerate(slides):
            offset = min(0.5, max((e - s) / 3, 0.1))
            capture_t = min(max(s + offset, 0.1), duration - 0.2)
            candidate_png = os.path.join(tmp, f"cand_{i:03d}.png")
            extract_frame(input_path, capture_t, candidate_png)

            is_stable = True
            if (e - s) < 2.5:
                check_t = min(capture_t + 0.3, e - 0.05, duration - 0.1)
                if check_t > capture_t + 0.05:
                    check_png = os.path.join(tmp, f"check_{i:03d}.png")
                    extract_frame(input_path, check_t, check_png)
                    if mean_diff(candidate_png, check_png) > 12.0:
                        is_stable = False
            if not is_stable:
                dropped_transition += 1
                continue

            if prev_kept_png is not None and mean_diff(candidate_png, prev_kept_png) < 3.0:
                dropped_duplicate += 1
                continue

            out_png = os.path.join(tmp, f"slide_{len(pngs):03d}.png")
            os.replace(candidate_png, out_png)
            prev_kept_png = os.path.join(tmp, f"rawcopy_{len(pngs):03d}.png")
            Image.open(out_png).save(prev_kept_png)
            if args.label:
                stamp_label(out_png, f"{video_name} — {fmt_ts(capture_t)}")
            pngs.append(out_png)

        if not pngs:
            print(f"WARNING: no slides extracted for {input_path}", file=sys.stderr)
            sys.exit(1)

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(pngs))

    mode = "fallback: evenly-spaced sampling (few/no holds detected)" if fallback else "hold-detection"
    print(f"{video_name}: {len(pngs)} slides kept, {dropped_transition} dropped "
          f"(mid-transition), {dropped_duplicate} dropped (near-duplicate) "
          f"({mode}) -> {output_path}")


def cmd_build(args):
    with open(args.events) as f:
        data = json.load(f)
    video_name = os.path.splitext(os.path.basename(args.input))[0]
    build_pdf(args.input, [tuple(e) for e in data["events"]], data["duration"],
              args.output, args, video_name)


def cmd_run(args):
    video_name = os.path.splitext(os.path.basename(args.input))[0]
    duration = ffprobe_duration(args.input)
    events = run_freezedetect(args.input, args.freeze_db)
    build_pdf(args.input, events, duration, args.output, args, video_name)


def add_build_options(ap):
    ap.add_argument("--min-hold", type=float, default=1.5)
    ap.add_argument("--merge-gap", type=float, default=0.0)
    ap.add_argument("--min-spacing", type=float, default=2.5)
    ap.add_argument("--max-slides", type=int, default=60)
    ap.add_argument("--label", dest="label", action="store_true", default=True)
    ap.add_argument("--no-label", dest="label", action="store_false")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("input")
    p_scan.add_argument("events")
    p_scan.add_argument("--start", type=float, default=None)
    p_scan.add_argument("--dur", type=float, default=None)
    p_scan.add_argument("--freeze-db", type=float, default=-30)
    p_scan.set_defaults(func=cmd_scan)

    p_build = sub.add_parser("build")
    p_build.add_argument("input")
    p_build.add_argument("events")
    p_build.add_argument("output")
    add_build_options(p_build)
    p_build.set_defaults(func=cmd_build)

    p_run = sub.add_parser("run")
    p_run.add_argument("input")
    p_run.add_argument("output")
    p_run.add_argument("--freeze-db", type=float, default=-30)
    add_build_options(p_run)
    p_run.set_defaults(func=cmd_run)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
