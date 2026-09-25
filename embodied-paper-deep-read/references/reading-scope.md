# Reading scope (phase 1)

Cover the whole argument and relevant appendix evidence without loading the whole raw text at
once. MinerU Markdown is the required source for parsing and navigating the paper's body. Use
the source PDF or a page-aware PDF index only to verify page locations and ambiguous details;
neither replaces an unusable MinerU body parse. The evidence note is the durable memory.

## Acquire once

```bash
python3 <skill-dir>/scripts/fetch_arxiv.py "<link-or-id>" \
  --dir "<paper-folder>" --slug "<slug>" --no-text
bash <skill-dir>/scripts/mineru_parse_pdf.sh \
  "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru"
```

Reuse cached PDF, metadata, and MinerU output. Pass `--refresh` only for an invalid cache or a
new paper version. For a user PDF, copy it into the paper folder without extracting body text
first:

```bash
python3 <skill-dir>/scripts/index_pdf.py "/path/to/paper.pdf" \
  --dir "<paper-folder>" --slug "<slug>" --no-text
```

Run MinerU on a user PDF only after applying the privacy-and-consent rule in `SKILL.md`. If the
token is missing, upload is declined, or MinerU fails, stop the deep-read and state the next
action. Do not continue by reading `_full.txt`, `_pages.jsonl`, or locally extracted PDF text
as a substitute for MinerU.
The MinerU script checks the service's per-file page limit before upload. If the PDF exceeds
that limit, stop rather than dropping appendix pages or reading them through PyMuPDF. Ask for a
shorter complete source or separately supplied volumes that MinerU can parse, preserve each
volume's original page-range mapping, and resume only when the full argument can be covered.

MinerU's expected contract is:

```text
<paper-folder>/mineru/
  full.md
  images/
  layout.json  (optional; some model versions do not emit it)
```

If `full.md` is missing, badly ordered, or too unreliable in crucial formulas/tables to
reconstruct the argument, stop and report the extraction problem. Targeted PDF inspection can
verify an otherwise usable MinerU passage but cannot replace a missing or unusable section.

## Two-pass reading

1. **Map the source.** Read metadata/abstract, stated contributions, Markdown heading outline,
   introduction, conclusion, limitation statements, and appendix headings. Identify whether the
   central focus is model类 or data类, then inventory every reported technical area: model/system
   design, data sources and processing, training, evaluation/benchmark protocol, real-world or
   system tests, safety/deployment, failures, and limitations. Record section ranges and, where
   possible, corresponding PDF pages. Treat “technical report” and “survey/review” as document
   formats; use the latter to map taxonomy and cited studies without narrowing coverage.
2. **Collect evidence by topic.** Read relevant Markdown sections for each inventoried area,
   including supporting contributions outside the selected category, plus relevant appendix
   details. Use bounded slices of roughly 8–12k extracted characters. Summarize each slice
   before opening the next, and map every material item to the final chapter where it will be
   explained.

Do not issue a single command/tool call that returns the complete `full.md`.
Skip the final bibliography list, but read the Related Work prose and any references discussed
substantively in the paper's argument.

Use the source PDF to verify the following. If searchable page text would help, rerun the
corresponding `fetch_arxiv.py` or `index_pdf.py` command without `--no-text` to create
`_pages.jsonl` and `_full.txt`; use those files only for targeted page verification:

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

Include motivation, contributions, related-work groups, limitations, appendix evidence, and
figure/table candidates. For an original study, capture its reported method, dimensions,
datasets, training, decisive results, and ablations. For a survey, capture its classification
axes, representative named mechanisms and protocols, comparison dimensions, cited evidence,
and gaps in comparability; do not imply that cited results are the survey authors' experiments.
Attach page numbers to every numerical or architecture claim; when only MinerU Markdown
evidence is available, mark it as `md section: ...` and verify before final publishing.

Related work means the methods or families the authors actually discuss in Related Work or
use as meaningful baselines. Group them by topic; do not enumerate every bibliography entry.

## Stop condition

Finish the evidence pass when every planned document section has page-cited support and no
unresolved item affects the interpretation. Reopen targeted Markdown sections or PDF pages
for gaps instead of rereading the paper end to end.
