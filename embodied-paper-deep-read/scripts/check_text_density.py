#!/usr/bin/env python3
"""Report long CJK text blocks in Markdown, Feishu XML, or fetch JSON."""

import argparse
import html
import json
from pathlib import Path
import re
import sys


THRESHOLD = 220
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323AF]")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
LIST = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")
LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"</?[^>]+>")
SKIP_HTML = re.compile(r"<(pre|code|script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)
BLOCK_TAGS = ("p", "li", "td", "th", "blockquote", "callout")


def clean(text):
    text = LINK.sub(r"\1", text)
    text = re.sub(r"`+[^`]*`+", "", text)
    return re.sub(r"[*_~]", "", HTML_TAG.sub("", html.unescape(text))).strip()


def make_block(source, line, kind, text):
    return source, line, kind, clean(text)


def html_blocks(text, source):
    text = SKIP_HTML.sub("", text)
    found = []
    for tag in BLOCK_TAGS:
        pattern = re.compile(rf"<{tag}\b[^>]*>(.*?)</{tag}\s*>", re.I | re.S)
        for match in pattern.finditer(text):
            body = match.group(1)
            # A container with child blocks is represented by those child paragraphs.
            if tag != "p" and re.search(r"<(?:p|li|td|th)\b", body, re.I):
                continue
            line = text.count("\n", 0, match.start()) + 1
            block = make_block(source, line, f"<{tag}>", body)
            if block[3]:
                found.append((match.start(), block))
    return [block for _, block in sorted(found)]


def markdown_blocks(text, source):
    blocks, current = [], []
    line_start, kind, fence = 1, "paragraph", None
    front_matter = text.startswith("---\n") or text == "---"

    def flush():
        nonlocal current
        if current:
            block = make_block(source, line_start, kind, " ".join(current))
            if block[3]:
                blocks.append(block)
        current = []

    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if front_matter:
            if number > 1 and line == "---":
                front_matter = False
            continue
        match = FENCE.match(line)
        if match:
            flush()
            marker = match.group(1)[0]
            fence = None if fence == marker else marker
            continue
        if fence:
            continue
        if not line or re.match(r"^(#{1,6}\s|---+$|\*\*\*+$|___+$)", line):
            flush()
            continue
        if line.startswith("|"):
            flush()
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells):
                continue
            for index, cell in enumerate(cells, 1):
                block = make_block(source, number, f"table cell {index}", cell)
                if block[3]:
                    blocks.append(block)
            continue
        match = LIST.match(line)
        if match:
            flush()
            kind, line_start, current = "list item", number, [match.group(1)]
            continue
        if line.startswith(">"):
            if current and kind != "blockquote":
                flush()
            if not current:
                kind, line_start = "blockquote", number
            current.append(re.sub(r"^>\s?", "", line))
            continue
        if current and kind == "list item":
            current.append(line)  # Markdown soft-wrapped list-item text.
        else:
            if current and kind != "paragraph":
                flush()
            if not current:
                kind, line_start = "paragraph", number
            current.append(line)
    flush()
    return blocks


def document_content(value):
    if isinstance(value, dict):
        data = value.get("data")
        if isinstance(data, dict):
            document = data.get("document")
            if isinstance(document, dict) and isinstance(document.get("content"), str):
                return document["content"]
        if isinstance(value.get("content"), str):
            return value["content"]
        for key in ("data", "document", "result"):
            content = document_content(value.get(key))
            if content is not None:
                return content
    elif isinstance(value, list):
        for item in value:
            content = document_content(item)
            if content is not None:
                return content
    return None


def scan(text, source, mode):
    if mode == "json":
        content = document_content(json.loads(text))
        if content is None:
            raise ValueError("JSON has no document content string")
        mode = "html" if re.search(r"<(?:p|li|td|th|callout)\b", content, re.I) else "markdown"
        text = content
    return html_blocks(text, source) if mode == "html" else markdown_blocks(text, source)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Markdown/XML/JSON draft files; use - for stdin")
    parser.add_argument("--threshold", type=int, default=THRESHOLD, help="CJK review threshold (default: 220)")
    parser.add_argument("--format", choices=("auto", "markdown", "html", "json"), default="auto")
    args = parser.parse_args()
    if args.threshold < 1:
        parser.error("--threshold must be positive")

    flagged, checked = [], 0
    for name in args.files:
        try:
            text = sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8")
            mode = args.format
            if mode == "auto":
                suffix = Path(name).suffix.lower()
                mode = "json" if suffix == ".json" else "html" if suffix in {".xml", ".html", ".htm"} else "markdown"
            blocks = scan(text, name, mode)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"error: cannot scan {name}: {error}", file=sys.stderr)
            return 2
        checked += len(blocks)
        flagged.extend(block for block in blocks if len(CJK.findall(block[3])) > args.threshold)

    if flagged:
        print(f"REVIEW: {len(flagged)} of {checked} text blocks exceed {args.threshold} CJK characters.")
        for name, line, kind, text in flagged:
            excerpt = " ".join(text.split())[:96]
            print(f"- {name}:{line} {kind}: {len(CJK.findall(text))} CJK characters — {excerpt}")
        return 1
    print(f"OK: checked {checked} blocks; none exceed {args.threshold} CJK characters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
