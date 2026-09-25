#!/usr/bin/env python3
"""Report long CJK blocks and multi-paragraph text walls.

The rhythm check looks only at top-level prose under the same heading. Lists, tables,
callouts, formulas, figures, diagrams, and headings break a prose run, so structured
content is not mistaken for a wall.
"""

import argparse
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys


THRESHOLD = 220
RUN_LENGTH = 3
RUN_AVERAGE = 110
RUN_MIN_BLOCK = 80
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323AF]")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
LIST = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+(.*)$")
LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"</?[^>]+>")
SKIP_HTML = re.compile(r"<(pre|code|script|style)\b[^>]*>.*?</\1\s*>", re.I | re.S)
BLOCK_TAGS = ("p", "li", "td", "th", "blockquote", "callout")
HEADINGS = {f"h{level}" for level in range(1, 7)}
RHYTHM_BREAK_TAGS = HEADINGS | {
    "table", "ul", "ol", "blockquote", "callout", "img", "image", "whiteboard",
    "diagram", "svg", "fig", "figure", "figcaption", "hr", "pre", "code",
    "title", "bookmark", "attachment", "file",
}
NON_PROSE_PARENTS = {
    "table", "thead", "tbody", "tfoot", "tr", "td", "th", "ul", "ol", "li",
    "blockquote", "callout", "pre", "code", "whiteboard", "diagram", "svg",
    "fig", "figure", "figcaption",
}
MATH_TAGS = {"latex", "math"}


def clean(text):
    text = LINK.sub(r"\1", text)
    text = re.sub(r"`+[^`]*`+", "", text)
    return re.sub(r"[*_~]", "", HTML_TAG.sub("", html.unescape(text))).strip()


def make_block(source, line, kind, text):
    return source, line, kind, clean(text)


def cjk_count(text):
    return len(CJK.findall(text))


def layout_item(source, line, kind, text="", section="front matter", bold_lead=False):
    return {
        "source": source,
        "line": line,
        "kind": kind,
        "text": clean(text),
        "section": section or "front matter",
        "bold_lead": bold_lead,
    }


class RhythmHTMLParser(HTMLParser):
    """Collect top-level prose and structural boundaries from an XML/HTML fragment."""

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.stack = []
        self.items = []
        self.paragraphs = []
        self.heading = None
        self.section = "front matter"

    def _boundary(self, line):
        self.items.append(layout_item(self.source, line, "boundary", section=self.section))

    def _current_paragraph(self):
        return self.paragraphs[-1] if self.paragraphs else None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        line = self.getpos()[0]
        ancestors = set(self.stack)
        paragraph = self._current_paragraph()

        if tag in {"b", "strong"} and paragraph and paragraph["capture"]:
            if not clean("".join(paragraph["parts"])):
                paragraph["bold_lead"] = True

        if tag in HEADINGS and not ancestors.intersection(NON_PROSE_PARENTS):
            self._boundary(line)
            self.heading = {"tag": tag, "parts": [], "line": line}
        elif tag == "p":
            self.paragraphs.append({
                "capture": not ancestors.intersection(NON_PROSE_PARENTS),
                "parts": [],
                "line": line,
                "bold_lead": False,
                "structural": False,
            })
        elif tag in RHYTHM_BREAK_TAGS and tag not in HEADINGS:
            if paragraph and paragraph["capture"]:
                paragraph["structural"] = True
            self._boundary(line)
        elif tag in MATH_TAGS and paragraph is None:
            # Standalone formula components break a run; inline math does not.
            self._boundary(line)

        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        if self.heading is not None:
            self.heading["parts"].append(data)
        paragraph = self._current_paragraph()
        if paragraph and paragraph["capture"] and not MATH_TAGS.intersection(self.stack):
            paragraph["parts"].append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "p" and self.paragraphs:
            paragraph = self.paragraphs.pop()
            if paragraph["capture"]:
                text = clean("".join(paragraph["parts"]))
                if text and cjk_count(text) and not paragraph["structural"]:
                    self.items.append(layout_item(
                        self.source,
                        paragraph["line"],
                        "paragraph",
                        text,
                        self.section,
                        paragraph["bold_lead"],
                    ))
                else:
                    self._boundary(paragraph["line"])
        elif tag in HEADINGS and self.heading and self.heading["tag"] == tag:
            heading_text = clean("".join(self.heading["parts"]))
            if heading_text:
                self.section = heading_text
            self.heading = None

        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == tag:
                del self.stack[index:]
                break


def html_layout_items(text, source):
    parser = RhythmHTMLParser(source)
    parser.feed(text)
    parser.close()
    return parser.items


MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.*)$")
MARKDOWN_BOLD_LEAD = re.compile(r"^\s*(?:\*\*|__)[^\n]+?(?:\*\*|__)")
MARKDOWN_BREAK = re.compile(
    r"^(?:---+$|\*\*\*+$|___+$|!\[|\$\$|\\\[|\\\]|"
    r"<(?:h[1-6]|table|ul|ol|blockquote|callout|img|image|whiteboard|diagram|svg|"
    r"fig|figure|figcaption|latex|math|hr|pre|code|bookmark)\b)",
    re.I,
)
MARKDOWN_FIGURE_HTML = re.compile(
    r"^<p\b[^>]*>\s*(?:<img\b[^>]*?/?>|<sub\b[^>]*>.*?</sub>)\s*</p\s*>$",
    re.I,
)


def markdown_table_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_markdown_table_separator(line):
    if "|" not in line:
        return False
    cells = markdown_table_cells(line)
    return len(cells) >= 2 and all(
        re.fullmatch(r":?-{3,}:?", re.sub(r"\s", "", cell)) for cell in cells
    )


def markdown_table_line_numbers(lines):
    """Return 1-based lines belonging to GFM tables, with or without outer pipes."""
    result = set()
    for index, raw in enumerate(lines):
        if not is_markdown_table_separator(raw.strip()):
            continue
        header = index - 1
        if header < 0 or not lines[header].strip() or "|" not in lines[header]:
            continue
        result.update({header + 1, index + 1})
        row = index + 1
        while row < len(lines) and lines[row].strip() and "|" in lines[row]:
            result.add(row + 1)
            row += 1
    return result


def markdown_layout_items(text, source):
    items, current = [], []
    line_start, section, fence, math_fence = 1, "front matter", None, None
    front_matter = text.startswith("---\n") or text == "---"
    in_container = False
    lines = text.splitlines()
    table_lines = markdown_table_line_numbers(lines)

    def boundary(line):
        items.append(layout_item(source, line, "boundary", section=section))

    def flush():
        nonlocal current
        if current:
            raw = " ".join(current)
            cleaned = clean(raw)
            if cleaned and cjk_count(cleaned):
                items.append(layout_item(
                    source,
                    line_start,
                    "paragraph",
                    cleaned,
                    section,
                    bool(MARKDOWN_BOLD_LEAD.match(raw)),
                ))
            elif cleaned:
                boundary(line_start)
        current = []

    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if front_matter:
            if number > 1 and line == "---":
                front_matter = False
                boundary(number)
            continue

        match = FENCE.match(line)
        if match:
            flush()
            boundary(number)
            marker = match.group(1)[0]
            fence = None if fence == marker else marker
            in_container = False
            continue
        if fence:
            continue
        if math_fence:
            if (math_fence == "$$" and "$$" in line) or (math_fence == "\\]" and line.startswith("\\]")):
                boundary(number)
                math_fence = None
            continue
        if not line:
            flush()
            in_container = False
            continue

        if line.startswith("$$"):
            flush()
            boundary(number)
            if line.count("$$") == 1:
                math_fence = "$$"
            continue
        if line.startswith("\\["):
            flush()
            boundary(number)
            if "\\]" not in line[2:]:
                math_fence = "\\]"
            continue

        heading = MARKDOWN_HEADING.match(line)
        if heading:
            flush()
            boundary(number)
            section = clean(heading.group(1)) or section
            in_container = False
            continue

        if number in table_lines or line.startswith("|") or LIST.match(line) or line.startswith(">"):
            flush()
            boundary(number)
            in_container = True
            continue
        if in_container:
            continue

        if MARKDOWN_FIGURE_HTML.match(line) or MARKDOWN_BREAK.match(line):
            flush()
            boundary(number)
            continue

        if not current:
            line_start = number
        current.append(line)

    flush()
    return items


def prose_wall_runs(items, run_length=RUN_LENGTH, run_average=RUN_AVERAGE,
                     run_min_block=RUN_MIN_BLOCK):
    """Return merged prose-wall candidates from structural layout items."""
    flagged = []
    current = []

    def review_run(run):
        if len(run) < run_length:
            return
        intervals = []
        required_substantial = min(2, run_length)
        for start in range(len(run) - run_length + 1):
            window = run[start:start + run_length]
            counts = [cjk_count(item["text"]) for item in window]
            reasons = set()
            if (sum(counts) >= run_average * run_length and
                    sum(count >= run_min_block for count in counts) >= required_substantial):
                reasons.add("dense prose")
            if all(item["bold_lead"] for item in window):
                reasons.add("bold-lead rhythm")
            if reasons:
                intervals.append([start, start + run_length - 1, reasons])

        merged = []
        for start, end, reasons in intervals:
            if merged and start <= merged[-1][1] + 1:
                merged[-1][1] = max(merged[-1][1], end)
                merged[-1][2].update(reasons)
            else:
                merged.append([start, end, set(reasons)])
        for start, end, reasons in merged:
            span = run[start:end + 1]
            flagged.append({
                "source": span[0]["source"],
                "start_line": span[0]["line"],
                "end_line": span[-1]["line"],
                "section": span[0]["section"],
                "items": span,
                "reasons": sorted(reasons),
            })

    for item in items:
        if item["kind"] == "paragraph":
            current.append(item)
        else:
            review_run(current)
            current = []
    review_run(current)
    return flagged


def html_blocks(text, source):
    # Suppress non-prose regions without changing later source line numbers.
    text = SKIP_HTML.sub(lambda match: re.sub(r"[^\n]", " ", match.group(0)), text)
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
    lines = text.splitlines()
    table_lines = markdown_table_line_numbers(lines)

    def flush():
        nonlocal current
        if current:
            block = make_block(source, line_start, kind, " ".join(current))
            if block[3]:
                blocks.append(block)
        current = []

    for number, raw in enumerate(lines, 1):
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
        if number in table_lines or line.startswith("|"):
            flush()
            cells = markdown_table_cells(line)
            if is_markdown_table_separator(line):
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


def scan_with_layout(text, source, mode):
    if mode == "json":
        content = document_content(json.loads(text))
        if content is None:
            raise ValueError("JSON has no document content string")
        mode = "html" if re.search(
            r"<(?:p|li|td|th|callout|h[1-6]|table|figure|fig|diagram|svg|whiteboard)\b",
            content,
            re.I,
        ) else "markdown"
        text = content
    if mode == "html":
        return html_blocks(text, source), html_layout_items(text, source)
    return markdown_blocks(text, source), markdown_layout_items(text, source)


def scan(text, source, mode):
    return scan_with_layout(text, source, mode)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="Markdown/XML/JSON draft files; use - for stdin")
    parser.add_argument("--threshold", type=int, default=THRESHOLD, help="CJK review threshold (default: 220)")
    parser.add_argument(
        "--run-length",
        type=int,
        default=RUN_LENGTH,
        help="consecutive prose paragraphs per rhythm window (default: 3)",
    )
    parser.add_argument(
        "--run-average",
        type=int,
        default=RUN_AVERAGE,
        help="minimum average CJK characters in a rhythm window (default: 110)",
    )
    parser.add_argument(
        "--run-min-block",
        type=int,
        default=RUN_MIN_BLOCK,
        help="minimum CJK characters in at least two paragraphs of a rhythm window (default: 80)",
    )
    parser.add_argument("--format", choices=("auto", "markdown", "html", "json"), default="auto")
    args = parser.parse_args()
    if args.threshold < 1:
        parser.error("--threshold must be positive")
    if args.run_length < 2:
        parser.error("--run-length must be at least 2")
    if args.run_average < 1 or args.run_min_block < 1:
        parser.error("--run-average and --run-min-block must be positive")

    flagged, wall_flagged, checked = [], [], 0
    for name in args.files:
        try:
            text = sys.stdin.read() if name == "-" else Path(name).read_text(encoding="utf-8")
            mode = args.format
            if mode == "auto":
                suffix = Path(name).suffix.lower()
                mode = "json" if suffix == ".json" else "html" if suffix in {".xml", ".html", ".htm"} else "markdown"
            blocks, layout = scan_with_layout(text, name, mode)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"error: cannot scan {name}: {error}", file=sys.stderr)
            return 2
        checked += len(blocks)
        flagged.extend(block for block in blocks if cjk_count(block[3]) > args.threshold)
        wall_flagged.extend(prose_wall_runs(
            layout,
            run_length=args.run_length,
            run_average=args.run_average,
            run_min_block=args.run_min_block,
        ))

    if flagged or wall_flagged:
        print(
            f"REVIEW: checked {checked} text blocks; {len(flagged)} long block(s) and "
            f"{len(wall_flagged)} prose-wall run(s) need review."
        )
        for name, line, kind, text in flagged:
            excerpt = " ".join(text.split())[:96]
            print(f"- LONG {name}:{line} {kind}: {cjk_count(text)} CJK characters — {excerpt}")
        for run in wall_flagged:
            counts = [cjk_count(item["text"]) for item in run["items"]]
            excerpt = " | ".join(" ".join(item["text"].split())[:42] for item in run["items"])
            lines = str(run["start_line"])
            if run["end_line"] != run["start_line"]:
                lines += f"-{run['end_line']}"
            reasons = ", ".join(run["reasons"])
            print(
                f"- WALL {run['source']}:{lines} under {run['section']!r}: "
                f"{len(run['items'])} consecutive paragraphs, {sum(counts)} CJK total "
                f"({', '.join(map(str, counts))}); {reasons} — {excerpt}"
            )
        return 1
    print(
        f"OK: checked {checked} text blocks; none exceed {args.threshold} CJK characters, "
        f"and no prose-wall run met the {args.run_length}-paragraph rhythm gate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
