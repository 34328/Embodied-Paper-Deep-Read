#!/usr/bin/env python3
"""Inventory and crop paper figures with low-cost previews and batch support."""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pymupdf import ensure_pymupdf

ensure_pymupdf()

import fitz


CAPTION_RE = re.compile(r"^\s*(fig(?:ure)?\.?|table)\s*[A-Z]?\.?\d+", re.IGNORECASE)


def parse_rect(value):
    parts = [float(item) for item in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--rect must be x0,y0,x1,y1")
    return fitz.Rect(*parts)


def open_page(pdf, page_number):
    document = fitz.open(pdf)
    index = page_number - 1
    if not 0 <= index < document.page_count:
        document.close()
        sys.exit(f"page {page_number} out of range (1..{document.page_count})")
    return document, document[index]


def caption_lines(page):
    return [line.strip() for line in page.get_text().splitlines() if CAPTION_RE.match(line)]


def image_records(page):
    records = []
    page_area = max(page.rect.width * page.rect.height, 1)
    for index, image in enumerate(page.get_image_info()):
        rect = fitz.Rect(image["bbox"])
        records.append(
            {
                "index": index,
                "rect": [round(value, 2) for value in rect],
                "width_pt": round(rect.width, 2),
                "height_pt": round(rect.height, 2),
                "page_area_ratio": round((rect.width * rect.height) / page_area, 4),
            }
        )
    return records


def crop(page, rect, out, zoom):
    if zoom <= 0:
        raise ValueError("zoom must be greater than zero")
    clipped = rect & page.rect
    if clipped.is_empty:
        raise ValueError(f"rectangle {rect} does not intersect page box {page.rect}")
    parent = os.path.dirname(os.path.abspath(out))
    os.makedirs(parent, exist_ok=True)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clipped)
    pixmap.save(out)
    return pixmap, clipped


def cmd_render(pdf, page_number, out, zoom):
    document, page = open_page(pdf, page_number)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if zoom <= 0:
        document.close()
        sys.exit("zoom must be greater than zero")
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pixmap.save(out)
    print(f"rendered page {page_number} -> {out} ({pixmap.width}x{pixmap.height}px, zoom {zoom})")
    document.close()


def cmd_list(pdf, page_number):
    document, page = open_page(pdf, page_number)
    images = image_records(page)
    print(f"page {page_number}: {len(images)} raster image block(s)")
    for item in images:
        rect = ",".join(str(value) for value in item["rect"])
        print(f"  [{item['index']}] rect={rect} area={item['page_area_ratio']:.1%}")
    for caption in caption_lines(page):
        print(f"  caption: {caption}")
    if page.get_drawings():
        print("  vector drawings present — render only if no raster bbox covers the figure")
    document.close()


def cmd_crop(pdf, page_number, out, zoom, rect=None, auto=None):
    document, page = open_page(pdf, page_number)
    if auto is not None:
        images = page.get_image_info()
        if not 0 <= auto < len(images):
            document.close()
            sys.exit(f"--auto {auto} out of range (page has {len(images)} blocks)")
        rect = fitz.Rect(images[auto]["bbox"])
    try:
        pixmap, clipped = crop(page, rect, out, zoom)
    except ValueError as error:
        document.close()
        sys.exit(str(error))
    print(f"cropped page {page_number} rect={clipped} -> {out} ({pixmap.width}x{pixmap.height}px)")
    document.close()


def cmd_scan_all(pdf, out):
    document = fitz.open(pdf)
    inventory = {
        "pdf": os.path.abspath(pdf),
        "page_count": document.page_count,
        "pages": [],
    }
    for page_number, page in enumerate(document, start=1):
        captions = caption_lines(page)
        images = image_records(page)
        if captions or images:
            inventory["pages"].append(
                {"page": page_number, "captions": captions, "images": images}
            )
    document.close()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(inventory, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    image_count = sum(len(page["images"]) for page in inventory["pages"])
    caption_count = sum(len(page["captions"]) for page in inventory["pages"])
    print(f"scanned {inventory['page_count']} pages -> {out} ({image_count} images, {caption_count} captions)")


def cmd_batch(pdf, spec_path, manifest_path, default_zoom):
    with open(spec_path, encoding="utf-8") as handle:
        spec = json.load(handle)
    figures = spec.get("figures", spec) if isinstance(spec, dict) else spec
    if not isinstance(figures, list):
        sys.exit("batch spec must be a list or an object with a 'figures' list")

    document = fitz.open(pdf)
    manifest = []
    for position, item in enumerate(figures, start=1):
        page_number = int(item["page"])
        if not 1 <= page_number <= document.page_count:
            document.close()
            sys.exit(f"batch item {position}: page {page_number} out of range")
        page = document[page_number - 1]
        if "rect" in item:
            rect_value = item["rect"]
            rect = fitz.Rect(*rect_value) if isinstance(rect_value, list) else parse_rect(rect_value)
        elif "auto" in item:
            images = page.get_image_info()
            index = int(item["auto"])
            if not 0 <= index < len(images):
                document.close()
                sys.exit(f"batch item {position}: auto index {index} out of range")
            rect = fitz.Rect(images[index]["bbox"])
        else:
            document.close()
            sys.exit(f"batch item {position}: provide 'rect' or 'auto'")
        out = item["out"]
        zoom = float(item.get("zoom", default_zoom))
        try:
            crop(page, rect, out, zoom)
        except ValueError as error:
            document.close()
            sys.exit(f"batch item {position}: {error}")
        anchor = item.get("anchor")
        width = int(item.get("width", 720))
        caption = item.get("caption")
        if width <= 0:
            document.close()
            sys.exit(f"batch item {position}: width must be greater than zero")
        if manifest_path and (not anchor or not caption):
            document.close()
            sys.exit(f"batch item {position}: anchor and caption are required with --manifest")
        if manifest_path:
            manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
            manifest_file = item.get("file") or os.path.relpath(os.path.abspath(out), manifest_dir)
            manifest_file = manifest_file.replace(os.sep, "/")
            manifest.append(
                f"<!-- FIG {manifest_file} | anchor:{anchor} | w={width} | cap:{caption} -->"
            )
        print(f"[{position}/{len(figures)}] page {page_number} -> {out}")
    document.close()
    if manifest_path:
        os.makedirs(os.path.dirname(os.path.abspath(manifest_path)), exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(manifest) + ("\n" if manifest else ""))
        print(f"manifest -> {manifest_path}")


def main():
    parser = argparse.ArgumentParser(description="Inventory or crop figures from a paper PDF.")
    parser.add_argument("pdf", help="path to the PDF")
    parser.add_argument("page", nargs="?", type=int, help="1-indexed page for page modes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--render", metavar="OUT.png", help="render one page for manual inspection")
    group.add_argument("--list", action="store_true", help="list bboxes/captions on one page")
    group.add_argument("--auto", type=int, metavar="N", help="crop the Nth raster image block")
    group.add_argument("--rect", type=parse_rect, metavar="x0,y0,x1,y1", help="crop a rectangle")
    group.add_argument("--scan-all", metavar="OUT.json", help="inventory image bboxes/captions once")
    group.add_argument("--batch", metavar="SPEC.json", help="crop all entries in a JSON spec")
    parser.add_argument("--out", help="output PNG required with --auto/--rect")
    parser.add_argument("--manifest", help="manifest output used with --batch")
    parser.add_argument(
        "--zoom",
        type=float,
        help="override zoom (render defaults 1.0; crops/batch default 3.0)",
    )
    args = parser.parse_args()

    page_mode = args.render or args.list or args.auto is not None or args.rect is not None
    if page_mode and args.page is None:
        parser.error("page is required with --render/--list/--auto/--rect")
    if (args.auto is not None or args.rect is not None) and not args.out:
        parser.error("--auto/--rect requires --out")
    if args.render:
        cmd_render(args.pdf, args.page, args.render, args.zoom or 1.0)
    elif args.list:
        cmd_list(args.pdf, args.page)
    elif args.auto is not None:
        cmd_crop(args.pdf, args.page, args.out, args.zoom or 3.0, auto=args.auto)
    elif args.rect is not None:
        cmd_crop(args.pdf, args.page, args.out, args.zoom or 3.0, rect=args.rect)
    elif args.scan_all:
        cmd_scan_all(args.pdf, args.scan_all)
    elif args.batch:
        cmd_batch(args.pdf, args.batch, args.manifest, args.zoom or 3.0)


if __name__ == "__main__":
    main()
