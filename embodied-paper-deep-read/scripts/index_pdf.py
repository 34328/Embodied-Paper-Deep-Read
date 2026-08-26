#!/usr/bin/env python3
"""Copy and index a local PDF without uploading it to a third-party service."""

import argparse
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_arxiv import dump_page_text, load_metadata, valid_pdf, validate_slug, write_json


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return digest.hexdigest()
            digest.update(chunk)


def atomic_copy(source, destination):
    part = destination + ".part"
    try:
        shutil.copy2(source, part)
        os.replace(part, destination)
    except Exception:
        try:
            os.remove(part)
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Copy a local PDF into a paper folder and build page-aware text."
    )
    parser.add_argument("pdf", help="path to the source PDF")
    parser.add_argument("--dir", required=True, help="paper output directory")
    parser.add_argument("--slug", help="filename stem (default: source filename)")
    parser.add_argument("--title", help="optional paper title for metadata")
    parser.add_argument("--refresh", action="store_true", help="rebuild the cached copy and index")
    args = parser.parse_args()

    source = os.path.abspath(args.pdf)
    if not valid_pdf(source):
        sys.exit(f"not a readable PDF: {source}")
    slug = validate_slug(args.slug or os.path.splitext(os.path.basename(source))[0])
    os.makedirs(args.dir, exist_ok=True)
    destination = os.path.abspath(os.path.join(args.dir, f"{slug}.pdf"))
    txt_path = os.path.join(args.dir, f"{slug}_full.txt")
    jsonl_path = os.path.join(args.dir, f"{slug}_pages.jsonl")
    meta_path = os.path.join(args.dir, f"{slug}_meta.json")

    source_hash = sha256(source)
    metadata = load_metadata(meta_path) or {}
    cache_matches = (
        not args.refresh
        and metadata.get("source_type") == "local-pdf"
        and metadata.get("sha256") == source_hash
        and valid_pdf(destination)
    )
    if not cache_matches and source != destination:
        atomic_copy(source, destination)
    elif source == destination:
        destination = source

    needs_index = args.refresh or not cache_matches or not (
        os.path.exists(txt_path) and os.path.exists(jsonl_path)
    )
    if needs_index:
        pages, empty_pages = dump_page_text(destination, txt_path, jsonl_path)
    else:
        with open(jsonl_path, encoding="utf-8") as handle:
            pages = sum(1 for _ in handle)
        empty_pages = 0

    write_json(
        meta_path,
        {
            "source_type": "local-pdf",
            "sha256": source_hash,
            "title": args.title or metadata.get("title", ""),
            "pages": pages,
        },
    )
    print(f"PDF        : {destination}  ({'cache' if cache_matches else 'copied'})")
    print(f"full text  : {txt_path}  ({pages} pages)")
    print(f"page index : {jsonl_path}")
    print(f"metadata   : {meta_path}")
    if empty_pages:
        print(f"warning    : {empty_pages}/{pages} pages have no extractable text; OCR may be needed")


if __name__ == "__main__":
    main()
