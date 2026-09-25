---
name: embodied-paper-deep-read
description: "Deep-read an embodied-intelligence, robotics, vision-language-action, world-model, or related AI paper from a modern or legacy arXiv URL/ID or a local PDF, then produce a structured, figure-rich study note, usually in Chinese and published to the user's own Feishu document. Use for 具身论文研读、精读、论文解读、deep-read、研究笔记、飞书文档 or local Markdown. MinerU is required for body parsing after the privacy check; use the page-aware PDF index only to verify page citations and avoid loading the entire paper into context at once."
---

# Embodied Paper Deep Read

Run **acquire → MinerU → evidence pass → figures → write → publish**. Preserve
quality by covering the complete argument and relevant appendix evidence, not by placing the
complete raw text in context at once. Default to Chinese and Feishu. Use local Markdown only
when the user requests it or Feishu is unavailable. Creating or overwriting a Feishu document
is an external write: do it only when the user's request includes producing/publishing the
deep-read note, and never overwrite an existing document unless the user supplied that target
or explicitly approved replacement.

Create exactly one well-named top-level folder per paper in the current workspace, using the
paper title plus arXiv ID when available, for example
`World-R1_Reinforcing_3D_Constraints_for_Text-to-Video_Generation_2604.24764/`. Keep all durable
artifacts for that paper inside this folder. Do not create generic `work/`, scattered temp
folders, or nested paper-specific wrappers. Put MinerU output under `mineru/full.md` and
`mineru/images/`; keep evidence notes, page indexes, figure manifests, publisher source, state,
and previews alongside `mineru/`.

## Privacy and credentials

MinerU is a third-party service and `scripts/mineru_parse_pdf.sh` uploads the complete PDF.

- For a public arXiv paper, use MinerU unless the user requests a local-only workflow. A
  local-only request cannot complete this skill's deep-read workflow; stop and explain that
  MinerU uploads the complete PDF.
- For a user-supplied, unpublished, review-confidential, proprietary, or otherwise non-public
  PDF, obtain explicit consent before uploading it. If consent is denied or unavailable, stop
  the deep-read workflow and explain the upload requirement. Do not substitute local PDF text
  extraction for MinerU's body parsing.
- Accept MinerU credentials only from the `MINERU_TOKEN` environment variable or the user's
  own `~/.mineru_token` file (mode 600). If neither exists, stop with setup instructions;
  the local page index is not a substitute for the required MinerU body parse.
  Never ask the user to paste a token into chat, read a token from a repository file, or embed
  one in commands, logs, skill source, or generated notes.
- Never disable TLS verification. Respect the user's standard proxy and CA configuration.

## Preflight before reading

Run `bash <skill-dir>/scripts/check_setup.sh` before downloading or indexing. It is the
single source of truth for Skill files, Python dependencies, MinerU token configuration, and
Feishu publishing readiness. Its exit status covers paper-reading requirements only; Feishu
status is reported separately. Add `--skip-feishu` when the user requested local Markdown.

Stop before reading only when a paper-reading requirement is missing. Feishu CLI, guidance, or
authorization problems do not block acquisition, MinerU parsing, or drafting. Resolve any part
of the Feishu setup that does not need the user before the publish step. If a user action remains,
continue the deep read: use local Markdown when Feishu was only the default destination, and
defer only the Feishu publication when the user explicitly requested it. Never upload a
non-public PDF to MinerU without explicit consent.

## Quick start

Resolve `<skill-dir>` to the directory containing this `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/fetch_arxiv.py "<arxiv-link-or-id>" \
  --dir "<paper-folder>" --slug "<slug>" --no-text

bash <skill-dir>/scripts/mineru_parse_pdf.sh \
  "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru"
```

For a user-supplied PDF, first copy it into the paper folder without extracting body text or
uploading it:

```bash
python3 <skill-dir>/scripts/index_pdf.py "/path/to/paper.pdf" \
  --dir "<paper-folder>" --slug "<slug>" --no-text
```

Apply the privacy and credential checks above. Only after upload is authorized, run:

```bash
bash <skill-dir>/scripts/mineru_parse_pdf.sh \
  "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru"
```

The MinerU script detects document language unless explicitly overridden with
`MINERU_LANGUAGE`; set it only when automatic detection is wrong.

MinerU writes:

- `<paper-folder>/mineru/full.md`
- `<paper-folder>/mineru/images/`
- `<paper-folder>/mineru/layout.json` when that model version supplies figure boxes

The fetcher and indexer keep the source and metadata in the same paper folder:

- `<paper-folder>/<slug>.pdf`
- `<paper-folder>/<slug>_meta.json`

If targeted page verification needs extracted page text, rerun the corresponding acquisition
command without `--no-text`. That optionally creates `<slug>_full.txt` and
`<slug>_pages.jsonl`; neither is a body-parsing fallback.

Use `--refresh` only when the source changed or the cache is invalid. If MinerU is unavailable,
disallowed by the privacy rule, or its body extraction is unusable, stop and report the cause.
If the source exceeds MinerU's current per-file page limit, do not silently omit pages or use
PyMuPDF body text instead. Explain the limit and request a shorter complete source or volumes
that can each be parsed by MinerU with their original page ranges preserved; if that is not
possible, report that this deep-read cannot be completed.
Use the PDF or optional `_pages.jsonl` only to verify page numbers, equations, tables, and ambiguous
claims in an otherwise usable MinerU extraction; never build the note's missing body content
from the PyMuPDF index.

## Pipeline

### 1. Acquire, parse, and build evidence notes

Create the paper folder first, then acquire the source so PDF/cache artifacts stay in
that folder. After the privacy and credential checks, run MinerU once. Read
`references/reading-scope.md`, inspect MinerU Markdown by section in bounded batches, and reopen
the PDF or optional `_pages.jsonl` only to verify page numbers, equations, tables, and ambiguous claims. Build a
compact `<slug>_evidence.md` containing a source-wide coverage inventory and page-cited facts
for the argument and every material technical contribution, including supporting contributions
and relevant appendix evidence. Map each to a final document chapter; use
`references/reading-scope.md`, `references/doc-structure.md`, and `references/content-depth.md`
to inventory, classify, and assess the source without dropping secondary technical content.

### 2. Inventory and extract figures

Read `references/figure-extraction.md`. Use MinerU's `images/` and Markdown image references to
**select** figures and make a provisional `<paper-folder>/figures.manifest`. If the MinerU task
is still pending, wait for the result before finalizing the figure selection. The final
manifest must point to the high-resolution files actually published, not MinerU's
low-resolution selection images.

**Then produce high-resolution versions before publishing** — MinerU caps its own images near
~1100px wide, too soft at 2x/Retina, and a display width above the file's pixel width upscales
it visibly. When `layout.json` has a usable box, re-render it:

```bash
python3 <skill-dir>/scripts/render_figures.py \
    "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru" \
    --out "<paper-folder>/figs_hires" \
    --manifest "<paper-folder>/figures.manifest" \
    --pick <prefix>=<label>:<width>
```

When `mineru/layout.json` supplies a usable box, this keeps MinerU's boundary and redoes only
the rasterization and replaces the corresponding manifest paths with the high-resolution
outputs after successful checks. Map by image filename rather than figure number. Check the
printed aspect-ratio table and inspect the selected figure against its PDF page and caption; a
matching ratio alone does not prove the boundary is correct. If rendering fails, do not publish
from the unchanged provisional manifest.

If a new MinerU result has no `layout.json`, or a needed box is missing, split, or unusable,
crop that figure from the source PDF with `extract_figures.py`. Do not re-upload solely to seek
`layout.json`. Store the crop and its manifest in `<paper-folder>`. Resolve ambiguous figure
identity from the PDF and caption before publishing. Keep related-work external figures
**off by default**. Search other papers for 1–2 architecture figures only when the user
explicitly requests comparative/related-work visuals.

### 3. Write from evidence, not raw pages

Read all four phase-3 references before drafting:

- `references/doc-structure.md`
- `references/content-depth.md`
- `references/writing-style.md`
- `references/beautify.md`

Draft one chapter at a time from `<slug>_evidence.md`. Reopen only the Markdown section,
cited page, or PDF view needed to verify numbers, dimensions, or ambiguous claims. Keep the
evidence notes and figure manifest as restartable checkpoints; do not retain all raw page text
in the working context.

Use the source reference described in `references/doc-structure.md`: arXiv when available,
otherwise an available DOI, publisher, or official project link. When no public URL exists,
identify the source PDF without inventing a link.

Before publishing, run the prose self-check in `writing-style.md` and the page-density check in
`beautify.md` on the complete draft. Restructure dense passages before creating or overwriting
the Feishu body, so later text edits do not force another image insertion pass.

### 4. Publish through one backend

Load only the selected publisher:

- Feishu: `publishers/feishu.md`
- Local Markdown: `publishers/local-md.md`

For Feishu, write or overwrite the text body before inserting images because an overwrite
removes previously inserted raster figures. For Local Markdown, write one complete `.md` file
with its figures at their anchors. Treat the figure manifest line
`file | anchor | width | caption` as the durable output contract for both backends. Its file
path must resolve to the final high-resolution render or PDF crop inside `<paper-folder>`.

Write Chinese punctuation full-width from the start (see `references/writing-style.md`
"Chinese punctuation and mixed-language typography"). To normalize or audit a block's XML,
pipe it through `scripts/normalize_cjk_punct.py` (stdin → stdout); it preserves half-width in
ratios, latex, URLs, and version strings.

## Completion checks

- Cover the paper's argument, main method, decisive experiments, limitations, and relevant
  appendix material.
- Use one of the two categories in `references/doc-structure.md` as the organizing path, and
  include every material model, data, evaluation, system, safety, or deployment contribution
  reported in the source, whether primary or secondary.
- Cite page numbers in evidence notes so any claim can be reopened without rereading the PDF.
  Carry the page or figure/table locator into the final note for pivotal technical and
  quantitative claims.
- Do not invent dimensions, data ratios, stages, or claims absent from the paper.
- Preserve every material technical claim, decisive metric, assumption, caveat, failure case,
  and causal link needed to reconstruct the paper's argument. Remove duplication, filler, and
  unsupported material.
- **Chinese prose uses Chinese punctuation.** In Chinese sentences, use `，`、`。`、`：`、`；`、`（ ）`、`“ ”`; reserve ASCII punctuation for code, commands, URLs, file paths, XML/HTML, LaTeX, JSON, exact titles, model/package names, and quoted source text. See `writing-style.md`.
- Use real hierarchy rather than text walls; follow `writing-style.md`.
- Review paragraphs over 220 Chinese characters and runs of three dense paragraphs using
  `references/beautify.md`; restructure where the topic changes while preserving technical
  claims, citations, conditions, and caveats.
- On Feishu, use native heading sequences; never embed chapter numbers in H1/H2/H3 text.
- Center all figures/whiteboards and make every table full-width with centered cells. Render
  loss functions and long equations as standalone centered display blocks.
- **Publish figures at ~2× their display width, never above their pixel width.** Use
  `render_figures.py` when MinerU supplies a usable `layout.json` box; otherwise use a
  high-resolution PDF crop from `extract_figures.py`. Inspect the figure against the source PDF,
  especially the teaser and any figure whose caption cites specific numbers. Resolve any
  reported ratio mismatch before publishing and verify the manifest points to the final file.
- Do not reload an unchanged PDF, regenerate an unchanged index, or refetch Feishu after every
  image operation.
