#!/usr/bin/env python3
"""Print a PDF's page count for the MinerU upload preflight."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pymupdf import ensure_pymupdf

ensure_pymupdf()

import fitz


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: pdf_page_count.py paper.pdf")
    try:
        with fitz.open(sys.argv[1]) as document:
            print(document.page_count)
    except Exception as error:
        sys.exit(f"cannot read PDF page count: {error}")


if __name__ == "__main__":
    main()
