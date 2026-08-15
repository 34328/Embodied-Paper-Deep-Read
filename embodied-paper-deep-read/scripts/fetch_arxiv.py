#!/usr/bin/env python3
"""Acquire an arXiv paper with cacheable PDF, metadata, and page-aware text."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


MODERN_ARXIV_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.IGNORECASE)
LEGACY_ARXIV_ID_RE = re.compile(
    r"([A-Za-z][A-Za-z0-9.-]*/\d{7})(v\d+)?", re.IGNORECASE
)


def normalize_id(value):
    """Extract a modern or legacy arXiv id, optionally versioned."""
    cleaned = value.strip()
    for pattern in (MODERN_ARXIV_ID_RE, LEGACY_ARXIV_ID_RE):
        match = pattern.search(cleaned)
        if match:
            return match.group(1) + (match.group(2) or "")
    sys.exit(
        f"could not find an arXiv id in: {cleaned!r}\n"
        "expected 2512.10935, hep-th/9901001, or an arxiv.org URL"
    )


def unversioned_id(arxiv_id):
    return re.sub(r"v\d+$", "", arxiv_id, flags=re.IGNORECASE)


def validate_slug(value):
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        sys.exit("--slug must contain only letters, digits, dot, underscore, or hyphen")
    return value


def default_slug(arxiv_id):
    return re.sub(r"[/.]", "_", arxiv_id)


def valid_pdf(path):
    try:
        with open(path, "rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def download_pdf(arxiv_id, out_pdf):
    quoted_id = urllib.parse.quote(arxiv_id, safe="/")
    url = f"https://arxiv.org/pdf/{quoted_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-paper-deep-read/3.0"})
    part = out_pdf + ".part"
    size = 0
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(part, "wb") as handle:
            first = response.read(64 * 1024)
            if not first.startswith(b"%PDF-"):
                raise RuntimeError(f"downloaded content from {url} is not a PDF")
            handle.write(first)
            size += len(first)
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                size += len(chunk)
        os.replace(part, out_pdf)
    except Exception:
        try:
            os.remove(part)
        except OSError:
            pass
        raise
    return size


def fetch_metadata(arxiv_id):
    """Query the HTTPS arXiv API for title/authors/date/categories/abstract."""
    query_id = urllib.parse.quote(arxiv_id, safe="")
    url = f"https://export.arxiv.org/api/query?id_list={query_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "embodied-paper-deep-read/3.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        xml = response.read()
    namespace = {"a": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(xml).find("a:entry", namespace)
    if entry is None:
        raise RuntimeError("no metadata entry returned")

    def text(tag):
        element = entry.find(f"a:{tag}", namespace)
        return " ".join(element.text.split()) if element is not None and element.text else ""

    authors = []
    for author in entry.findall("a:author", namespace):
        name = author.find("a:name", namespace)
        if name is not None and name.text:
            authors.append(name.text)
    quoted_id = urllib.parse.quote(arxiv_id, safe="/")
    return {
        "requested_id": arxiv_id,
        "id": unversioned_id(arxiv_id),
        "title": text("title"),
        "authors": authors,
        "published": text("published")[:10],
        "updated": text("updated")[:10],
        "categories": [item.get("term") for item in entry.findall("a:category", namespace)],
        "abstract": text("summary"),
        "abs_url": f"https://arxiv.org/abs/{quoted_id}",
        "pdf_url": f"https://arxiv.org/pdf/{quoted_id}",
    }


def write_json(path, value):
    part = path + ".part"
    with open(part, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(part, path)


def dump_page_text(pdf_path, out_txt, out_jsonl):
    try:
        import fitz
    except ImportError:
        sys.exit("PyMuPDF not installed. Try: python3 -m pip install pymupdf")

    pdf_path = os.fspath(pdf_path)
    out_txt = os.fspath(out_txt)
    out_jsonl = os.fspath(out_jsonl)
    txt_part = out_txt + ".part"
    jsonl_part = out_jsonl + ".part"
    empty_pages = 0
    try:
        with fitz.open(pdf_path) as document, open(
            txt_part, "w", encoding="utf-8", newline="\n"
        ) as text_handle, open(jsonl_part, "w", encoding="utf-8", newline="\n") as jsonl_handle:
            pages = document.page_count
            for page_number, page in enumerate(document, start=1):
                page_text = page.get_text()
                if not page_text.strip():
                    empty_pages += 1
                text_handle.write(f"\n===== PDF PAGE {page_number}/{pages} =====\n\n")
                text_handle.write(page_text)
                if not page_text.endswith("\n"):
                    text_handle.write("\n")
                jsonl_handle.write(
                    json.dumps({"pdf_page": page_number, "text": page_text}, ensure_ascii=False)
                    + "\n"
                )
        os.replace(txt_part, out_txt)
        os.replace(jsonl_part, out_jsonl)
    except Exception:
        for part in (txt_part, jsonl_part):
            try:
                os.remove(part)
            except OSError:
                pass
        raise
    return pages, empty_pages


def load_metadata(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def needs_text_refresh(pdf_path, txt_path, jsonl_path, refresh):
    if refresh or not os.path.exists(txt_path) or not os.path.exists(jsonl_path):
        return True
    pdf_mtime = os.path.getmtime(pdf_path)
    return min(os.path.getmtime(txt_path), os.path.getmtime(jsonl_path)) < pdf_mtime


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Fetch an arXiv paper with cached PDF, metadata, and page-aware text."
    )
    parser.add_argument("link", help="arXiv URL or bare modern/legacy id")
    parser.add_argument("--dir", required=True, help="paper output directory")
    parser.add_argument("--slug", help="filename stem (default: normalized arXiv id)")
    parser.add_argument("--no-text", action="store_true", help="skip text/index extraction")
    parser.add_argument("--refresh", action="store_true", help="ignore cache and fetch again")
    args = parser.parse_args()

    arxiv_id = normalize_id(args.link)
    slug = validate_slug(args.slug or default_slug(arxiv_id))
    os.makedirs(args.dir, exist_ok=True)
    pdf_path = os.path.join(args.dir, f"{slug}.pdf")
    txt_path = os.path.join(args.dir, f"{slug}_full.txt")
    jsonl_path = os.path.join(args.dir, f"{slug}_pages.jsonl")
    meta_path = os.path.join(args.dir, f"{slug}_meta.json")

    metadata = None if args.refresh else load_metadata(meta_path)
    source_matches = bool(metadata and metadata.get("requested_id") == arxiv_id)
    pdf_cached = valid_pdf(pdf_path) and source_matches and not args.refresh
    metadata_cached = bool(source_matches and metadata.get("title") and not metadata.get("warning"))

    with ThreadPoolExecutor(max_workers=2) as executor:
        pdf_future = None if pdf_cached else executor.submit(download_pdf, arxiv_id, pdf_path)
        meta_future = None if metadata_cached else executor.submit(fetch_metadata, arxiv_id)
        if pdf_future is not None:
            try:
                pdf_bytes = pdf_future.result()
            except Exception as error:
                sys.exit(f"PDF download failed: {error}")
        else:
            pdf_bytes = os.path.getsize(pdf_path)
        if meta_future is not None:
            try:
                metadata = meta_future.result()
            except Exception as error:
                metadata = {"requested_id": arxiv_id, "warning": f"metadata fetch failed: {error}"}
            write_json(meta_path, metadata)

    pages = None
    empty_pages = 0
    text_cached = False
    if not args.no_text:
        if needs_text_refresh(pdf_path, txt_path, jsonl_path, args.refresh or not pdf_cached):
            pages, empty_pages = dump_page_text(pdf_path, txt_path, jsonl_path)
        else:
            text_cached = True
            with open(jsonl_path, encoding="utf-8") as handle:
                pages = sum(1 for _ in handle)

    print(f"arXiv id   : {arxiv_id}")
    print(f"PDF        : {pdf_path}  ({pdf_bytes // 1024} KB, {'cache' if pdf_cached else 'fetched'})")
    if pages is not None:
        state = "cache" if text_cached else "generated"
        print(f"full text  : {txt_path}  ({pages} pages, {state})")
        print(f"page index : {jsonl_path}")
        if empty_pages:
            print(f"warning    : {empty_pages}/{pages} pages have no extractable text; OCR may be needed")
    print(f"metadata   : {meta_path}  ({'cache' if meta_future is None else 'fetched'})")
    if metadata.get("title"):
        print(f"title      : {metadata['title']}")
        print(f"authors    : {', '.join(metadata.get('authors', []))}")
        print(f"published  : {metadata.get('published', '')}")
    elif metadata.get("warning"):
        print(f"[metadata] {metadata['warning']} — fill metadata from the PDF")


if __name__ == "__main__":
    main()
