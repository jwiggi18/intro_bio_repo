# How to extract "slides" from a VideoScribe video

`scripts/extract_video_slides.py` turns one of your whiteboard-animation videos into a PDF of still images — one image per drawn element/pause, instead of a flood of near-duplicate frames from a generic converter. It works by finding the moments the video actually holds still (ffmpeg's freeze detection), not by watching for pixel changes.

This doc is the cheat sheet for running it later without having to re-derive the settings.

## Before you run it (one-time setup on your Mac)

You need `ffmpeg` and two Python packages. In Terminal:

```bash
brew install ffmpeg          # skip if you already have it (which ffmpeg to check)
pip3 install img2pdf pillow
```

## The two commands you'll actually use

### `run` — for a single short-to-medium video (up to ~10 min), all in one step

```bash
cd ~/repos/intro_bio_repo
python3 scripts/extract_video_slides.py run \
  "/path/to/videos/MyVideo.mp4" \
  "/path/to/video_slides/MyVideo.pdf"
```

This scans the whole video and builds the PDF in one go. Fine for anything you're running yourself in Terminal — there's no time limit when you run it directly (the two-step version below only exists because Claude's tool calls are capped at 45 seconds each; you don't have that problem).

### `scan` + `build` — split into two steps (useful for retuning without rescanning)

```bash
# Step 1: scan the video once, save the raw pause data to a small JSON file
python3 scripts/extract_video_slides.py scan \
  "/path/to/videos/MyVideo.mp4" \
  "/path/to/video_slides/.events_cache/MyVideo.json"

# Step 2: build the PDF from that cached scan
python3 scripts/extract_video_slides.py build \
  "/path/to/videos/MyVideo.mp4" \
  "/path/to/video_slides/.events_cache/MyVideo.json" \
  "/path/to/video_slides/MyVideo.pdf"
```

The scan is the slow part (reads the whole video). Once you have the `.json` file, you can re-run `build` again and again with different settings in a couple seconds — no need to rescan. **This is the one worth remembering:** if a PDF comes out too sparse or too dense, don't rescan — just re-run `build` on the existing `.json` with different numbers (examples below).

## The settings that actually change the output

| Flag | What it does | Default |
|---|---|---|
| `--min-hold` | How long a pause has to be to count as a real slide. **Lower = more slides.** | `1.5` (seconds) |
| `--min-spacing` | Minimum time between two kept slides. **Lower = more slides, allowed closer together.** | `2.5` (seconds) |
| `--max-slides` | Hard ceiling on slide count, in case a video produces too many. | `60` |
| `--no-label` | Turns off the small "`video name — timestamp`" stamp in the corner of each page. | on by default |

You almost never need to touch `--merge-gap` or `--freeze-db` — leave those alone.

### "This video has too many slides / too much clutter"

Raise `--min-hold` and `--min-spacing` — this keeps only the longer, more deliberate pauses (one slide per big idea instead of one per drawn element):

```bash
python3 scripts/extract_video_slides.py build \
  "videos/MyVideo.mp4" "video_slides/.events_cache/MyVideo.json" "video_slides/MyVideo.pdf" \
  --min-hold 4 --min-spacing 10 --max-slides 20
```

### "This video is missing detail / too sparse — I want more shots"

Lower `--min-hold` and `--min-spacing` — this catches more of the individual drawn elements, not just the major conceptual beats:

```bash
python3 scripts/extract_video_slides.py build \
  "videos/MyVideo.mp4" "video_slides/.events_cache/MyVideo.json" "video_slides/MyVideo.pdf" \
  --min-hold 1.0 --min-spacing 1.5 --max-slides 80
```

### "I just want the current default density" (what all 10 existing PDFs used)

```bash
python3 scripts/extract_video_slides.py build \
  "videos/MyVideo.mp4" "video_slides/.events_cache/MyVideo.json" "video_slides/MyVideo.pdf"
```
(no extra flags — this is just the built-in default: `--min-hold 1.5 --min-spacing 2.5 --max-slides 60`)

## Running it on a brand-new video for the first time

```bash
cd ~/repos/intro_bio_repo
python3 scripts/extract_video_slides.py run \
  "/Users/jwiggi/Library/Mobile Documents/com~apple~CloudDocs/1.courses_taught/1.Intro_Bio/1.2026/videos/NewVideo.mp4" \
  "/Users/jwiggi/Library/Mobile Documents/com~apple~CloudDocs/1.courses_taught/1.Intro_Bio/1.2026/video_slides/NewVideo.pdf"
```

If you want the ability to retune it later without rescanning, use `scan` then `build` instead (see above) so you get a cached `.json` file.

## What to expect / known quirks

- **Talking-head or live-action videos** (not whiteboard animation) don't have real "freeze" pauses, so the script automatically falls back to grabbing a frame every ~45 seconds instead. You'll see `fallback: evenly-spaced sampling` in the output when this happens.
- **A couple of frames per video may catch a bit of a scene-wipe transition** bleeding across otherwise-readable content. The script does try to catch these (a stability check on short pauses, plus a duplicate-frame check), but it's not perfect — usually 0-2 imperfect frames out of 20-40 in a video.
- **These PDFs are a visual/print supplement, not an accessibility replacement.** They have no machine-readable text, so they don't substitute for the video transcripts in `video_transcripts/` for screen-reader accessibility. Good for printing, note-taking, or reviewing diagrams.

## Where everything lives

- Script: `scripts/extract_video_slides.py` (in the repo)
- Source videos: `1.2026/videos/`
- Output PDFs: `1.2026/video_slides/`
- Cached scans (safe to delete — just means the next `build` needs a fresh `scan` first): `1.2026/video_slides/.events_cache/`
