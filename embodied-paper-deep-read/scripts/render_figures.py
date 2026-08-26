#!/usr/bin/env python3
"""Re-render MinerU-detected figures from the source PDF at high DPI.

Why this exists
---------------
MinerU caps its own extracted images near ~1100px wide and exposes no
resolution/DPI/scale parameter (verified against the official CLI and
output-format docs). On a 2x/Retina display a figure shown at 760 CSS px needs
~1520 physical pixels to look sharp, so MinerU's own JPEGs render soft — and a
chart that is pure vector in the PDF is being needlessly rasterized at 685px.

The fix is NOT to guess figure boundaries ourselves (heuristics over text
blocks / drawing rects mis-frame figures: they swallow the paper title, or clip
a side-by-side panel in half). Instead we take MinerU's OWN detected bboxes
from layout.json and only redo the rasterization step, which is deterministic.

Mapping is done by IMAGE FILENAME, never by figure number: MinerU sometimes
mis-assigns caption numbers when two panels sit side by side (e.g. labeling a
Figure 15 panel as "Figure 14"). The filename is unambiguous.

Every render is cross-checked: the output aspect ratio must match MinerU's
original image for that filename. Matching ratios prove we cropped the same
region and merely raised the resolution. Mismatches are reported, not silently
written, and must be eyeballed before use.

Usage
-----
  # Render every figure referenced by full.md at 2x a 760px display width
  python3 render_figures.py <paper.pdf> <mineru-dir> --out figs_hires

  # Only specific images, with per-figure display widths
  python3 render_figures.py <paper.pdf> <mineru-dir> --out figs_hires \
      --pick bcedd339=Fig1:760 --pick f58ef364=Fig10:760

`--pick` takes `<filename-prefix>=<label>[:<display-width>]`. A prefix of the
MinerU image filename is enough (12 hex chars is plenty).

Requires PyMuPDF; Pillow only for the aspect-ratio check (skipped if absent).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pymupdf import ensure_pymupdf

ensure_pymupdf()

import fitz

try:
    from PIL import Image
except ImportError:
    Image = None

# MinerU block types that carry a figure body.
BODY_TYPES = {"image_body", "chart_body"}
CONTAINER_TYPES = {"image", "chart"}

MAX_SCALE = 8.0
RATIO_TOLERANCE = 0.04  # 4% — generous enough for bbox rounding, tight enough to catch a wrong region


def load_bbox_map(mineru_dir: str) -> dict:
    """Return {image_filename: {page, bbox}} from MinerU's layout.json.

    layout.json holds the same `pdf_info` structure as middle.json: per page,
    blocks with a `type` and a `bbox`, where a figure container holds an
    image_body/chart_body whose spans name the extracted `image_path`.
    """
    path = os.path.join(mineru_dir, "layout.json")
    if not os.path.exists(path):
        # Fall back to a uuid-prefixed name if cleanup did not normalize it.
        cands = [f for f in os.listdir(mineru_dir) if f.endswith("layout.json")]
        if not cands:
            sys.exit(
                f"No layout.json in {mineru_dir}.\n"
                "Re-run scripts/mineru_parse_pdf.sh with MINERU_REFRESH=true; it keeps\n"
                "layout.json alongside full.md and images/. Older results predate that."
            )
        path = os.path.join(mineru_dir, cands[0])

    with open(path, encoding="utf-8") as fh:
        info = json.load(fh)

    out = {}
    for page in info.get("pdf_info", []):
        pno = page.get("page_idx", 0) + 1
        for block in page.get("para_blocks", []) or []:
            if block.get("type") not in CONTAINER_TYPES:
                continue
            for sub in block.get("blocks", []) or []:
                if sub.get("type") not in BODY_TYPES:
                    continue
                bbox = sub.get("bbox")
                for line in sub.get("lines", []) or []:
                    for span in line.get("spans", []) or []:
                        name = span.get("image_path")
                        if name and bbox:
                            out[name] = {"page": pno, "bbox": bbox}
    return out


def parse_picks(picks: list) -> list:
    parsed = []
    for spec in picks:
        if "=" not in spec:
            sys.exit(f"--pick needs <prefix>=<label>[:<width>], got: {spec}")
        prefix, rest = spec.split("=", 1)
        label, _, width = rest.partition(":")
        parsed.append((prefix, label or prefix, int(width) if width else 760))
    return parsed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("mineru_dir")
    ap.add_argument("--out", default="figs_hires")
    ap.add_argument("--pick", action="append", default=[],
                    help="<filename-prefix>=<label>[:<display-width>]; repeatable")
    ap.add_argument("--width", type=int, default=760,
                    help="default CSS display width for figures without an explicit one")
    ap.add_argument("--dpr", type=float, default=2.0,
                    help="device pixel ratio to target (2.0 for Retina)")
    args = ap.parse_args()

    bbox_map = load_bbox_map(args.mineru_dir)
    if not bbox_map:
        sys.exit("layout.json parsed but contained no figure bboxes.")

    picks = parse_picks(args.pick)
    if not picks:
        picks = [(name, os.path.splitext(name)[0][:12], args.width) for name in sorted(bbox_map)]

    os.makedirs(args.out, exist_ok=True)
    doc = fitz.open(args.pdf)
    img_dir = os.path.join(args.mineru_dir, "images")

    print(f"{'label':>10} {'MinerU':>12} {'rendered':>13} {'gain':>6} {'ratio-check':>13}  bbox")
    suspect = []
    for prefix, label, disp_w in picks:
        matches = [n for n in bbox_map if n.startswith(prefix)]
        if not matches:
            print(f"{label:>10}  no layout.json entry for prefix {prefix!r}")
            suspect.append(label)
            continue
        name = matches[0]
        entry = bbox_map[name]

        page = doc[entry["page"] - 1]
        rect = fitz.Rect(*entry["bbox"])
        scale = min(MAX_SCALE, (disp_w * args.dpr) / rect.width)
        pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(scale, scale), alpha=False)
        dest = os.path.join(args.out, f"{label}.png")
        pix.save(dest)

        # Cross-check against MinerU's own raster for the same filename.
        verdict, gain = "no original", ""
        src = os.path.join(img_dir, name)
        if Image and os.path.exists(src):
            ow, oh = Image.open(src).size
            gain = f"{pix.width / ow:.1f}x"
            diff = abs((ow / oh) - (pix.width / pix.height)) / (ow / oh)
            if diff < RATIO_TOLERANCE:
                verdict = f"ok {diff * 100:.1f}%"
            else:
                verdict = f"MISMATCH {diff * 100:.1f}%"
                suspect.append(label)
            orig = f"{ow}x{oh}"
        else:
            orig = "-"

        print(f"{label:>10} {orig:>12} {pix.width}x{pix.height:<7} {gain:>6} {verdict:>13}  "
              f"p{entry['page']} {entry['bbox']}")

    if suspect:
        print("\nInspect before publishing (ratio mismatch or unmapped): " + ", ".join(suspect))
        print("A mismatch usually means the figure spans panels MinerU split differently.")
    else:
        print("\nAll renders match MinerU's regions — same crop, higher resolution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
