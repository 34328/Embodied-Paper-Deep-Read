# Reading scope (phase 1)

Cover the whole argument and relevant appendix evidence without loading the whole raw text at
once. Prefer the MinerU Markdown package as the navigation layer; use the page-aware PDF
index as verification and fallback. The evidence note is the durable memory.

## Acquire once

```bash
python3 <skill-dir>/scripts/fetch_arxiv.py "<link-or-id>" \
  --dir "<paper-folder>" --slug "<slug>"
MINERU_LANGUAGE=en bash <skill-dir>/scripts/mineru_parse_pdf.sh \
  "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru"
```

Reuse cached PDF, metadata, text, JSONL, and MinerU output. Pass `--refresh` only for an
invalid cache or a new paper version. For a user PDF, always create the local page-aware index
first:

```bash
python3 <skill-dir>/scripts/index_pdf.py "/path/to/paper.pdf" \
  --dir "<paper-folder>" --slug "<slug>"
```

Run MinerU on a user PDF only after applying the privacy-and-consent rule in `SKILL.md`.

MinerU's expected contract is:

```text
<paper-folder>/mineru/
  full.md
  images/
```

If `full.md` is missing, badly ordered, or formula/table extraction is unreliable for the
paper, fall back to `_pages.jsonl` and the PDF.

## Two-pass reading

1. **Map the paper.** Read metadata/abstract, Markdown heading outline, introduction,
   conclusion, limitation statements, and appendix headings. Record the section ranges and,
   where possible, corresponding PDF pages.
2. **Collect evidence by topic.** Read relevant Markdown sections for method, datasets,
   training, experiments, failure cases, and appendix details. Use bounded slices of roughly
   8–12k extracted characters. Summarize each slice before opening the next.

Do not issue a single command/tool call that returns the complete `full.md` or `_full.txt`.
Skip the final bibliography list, but read the Related Work prose and any references discussed
substantively in the paper's argument.

Use `_pages.jsonl` or the PDF to verify:

- numbers, dimensions, datasets, and hyperparameters;
- equations that MinerU may have linearized incorrectly;
- tables whose columns may have shifted;
- any claim where page citation matters.

## Evidence note

Maintain `<slug>_evidence.md` with compact entries:

```text
METHOD — factorized decoder — PDF pp. 5–6 (printed pp. 3–4)
- input/output shapes: ...
- mechanism and why it matters: ...
- unresolved: exact head count; check Appendix B
```

Distinguish zero-based tool indexes, one-based PDF pages, and printed paper pages. Use `PDF p.`
as the required locator and add `printed p.` when it differs.

Include motivation, contributions, related-work groups, method, tensors/hyperparameters,
datasets, training, decisive results, ablations, limitations, appendix evidence, and figure/
table candidates. Attach page numbers to every numerical or architecture claim; when only
MinerU Markdown evidence is available, mark it as `md section: ...` and verify before final
publishing.

Related work means the methods or families the authors actually discuss in Related Work or
use as meaningful baselines. Group them by topic; do not enumerate every bibliography entry.

## Stop condition

Finish the evidence pass when every planned document section has page-cited support and no
unresolved item affects the interpretation. Reopen targeted Markdown sections or PDF pages
for gaps instead of rereading the paper end to end.
