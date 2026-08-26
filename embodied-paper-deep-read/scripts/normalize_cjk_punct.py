#!/usr/bin/env python3
"""Normalize CJK punctuation in publisher text nodes.

Usage: pipe an XML fragment (a block's inner HTML, or a whole doc's content) on stdin;
normalized XML comes out on stdout. Best used to (a) normalize each chapter's XML BEFORE
inserting it, or (b) audit an already-published doc by diffing normalized vs current.

Rules (only inside Chinese context):
- , -> ，   : -> ：   ; -> ；   ! -> ！   ? -> ？
- straight "..." -> curly “...”
- ( ) wrapping content that touches CJK -> （ ）
Preserve half-width in: numbers/ratios (1:15), latex, code, urls, ascii-only tokens,
version strings, decimals.

Known limitation: quotes/parens that span a <b>/<latex> tag boundary are split across
segments and may be mis-paired — verify paired direction after emphasis/inline math.

Strategy: operate ONLY on visible text segments between tags, and NEVER inside
<latex>...</latex>, <pre>/<code>, <whiteboard>, <bookmark href>, or attribute values.
A punctuation char is converted only when it is adjacent to (or between) CJK context.
"""
import re
import sys

CJK = r'一-鿿　-〿＀-￯'
cjk_re = re.compile('[' + CJK + ']')
# Full-width CJK punctuation also signals Chinese context for neighbor checks.
CJK_PUNCT = set('，。：；！？“”（）、《》「」…—')


def is_cjk(ch):
    return bool(ch) and (bool(cjk_re.match(ch)) or ch in CJK_PUNCT)


def near_cjk(s, i):
    """Is there a CJK char immediately before or after position i (skipping the punct)?"""
    j = i - 1
    while j >= 0 and s[j] in ' \t':
        j -= 1
    left = s[j] if j >= 0 else ''
    k = i + 1
    while k < len(s) and s[k] in ' \t':
        k += 1
    right = s[k] if k < len(s) else ''
    return is_cjk(left) or is_cjk(right)


MAP = {',': '，', ':': '：', ';': '；', '!': '！', '?': '？'}


def convert_commas(seg):
    seg_has_cjk = bool(cjk_re.search(seg))
    out = []
    for i, ch in enumerate(seg):
        if ch in MAP:
            # ratio / time like 1:15 -> keep colon if both neighbors are digits
            if ch == ':' and 0 < i < len(seg) - 1 and seg[i - 1].isdigit() and seg[i + 1].isdigit():
                out.append(ch)
                continue
            # decimal / thousand like 1,000 -> keep comma between digits
            if ch == ',' and 0 < i < len(seg) - 1 and seg[i - 1].isdigit() and seg[i + 1].isdigit():
                out.append(ch)
                continue
            # ; ! ? almost never occur inside code/math inline; convert whenever the
            # surrounding segment is Chinese, even if the immediate neighbor is latin/digit.
            if ch in ';!?' and seg_has_cjk:
                out.append(MAP[ch])
                continue
            if near_cjk(seg, i):
                out.append(MAP[ch])
                continue
        out.append(ch)
    return ''.join(out)


def convert_quotes(seg):
    """Straight double quotes -> curly, alternating direction, only when touching CJK."""
    result = []
    quote_toggle = 0
    for pos, ch in enumerate(seg):
        if ch == '"' and near_cjk(seg, pos):
            result.append('“' if quote_toggle % 2 == 0 else '”')
            quote_toggle += 1
        else:
            result.append(ch)
    return ''.join(result)


def convert_parens(seg):
    """Convert ( ) to full-width when the span or its neighbor involves CJK."""
    out = list(seg)
    stack = []
    pairs = []
    for i, ch in enumerate(out):
        if ch == '(':
            stack.append(i)
        elif ch == ')' and stack:
            pairs.append((stack.pop(), i))
    for o, c in pairs:
        inner = seg[o + 1:c]
        left = seg[o - 1] if o > 0 else ''
        right = seg[c + 1] if c + 1 < len(seg) else ''
        if cjk_re.search(inner) or is_cjk(left) or is_cjk(right):
            out[o] = '（'
            out[c] = '）'
    return ''.join(out)


def normalize_text(seg):
    # Parens first: converting () -> （） so that following comma/semicolon checks see
    # a full-width bracket (CJK context) as neighbor. Then quotes, then commas/colons.
    seg = convert_parens(seg)
    seg = convert_quotes(seg)
    seg = convert_commas(seg)
    return seg


# --- segment the XML: skip tags and protected elements ---
PROTECT = re.compile(r'(<latex>.*?</latex>|<pre.*?</pre>|<whiteboard.*?</whiteboard>|<[^>]+>)', re.S)


def process(xml):
    parts = PROTECT.split(xml)
    for i, p in enumerate(parts):
        if not p:
            continue
        if p.startswith('<'):  # tag or protected block
            continue
        # this is visible text between tags
        parts[i] = normalize_text(p)
    return ''.join(parts)


if __name__ == '__main__':
    sys.stdout.write(process(sys.stdin.read()))
