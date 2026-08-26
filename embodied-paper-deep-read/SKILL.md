---
name: embodied-paper-deep-read
description: "Deep-read an embodied-intelligence, robotics, vision-language-action, world-model, or related AI paper from a modern or legacy arXiv URL/ID or a local PDF, then produce a structured, figure-rich study note, usually in Chinese and published to the user's own Feishu document. Use for 具身论文研读、精读、论文解读、deep-read、研究笔记、飞书文档 or local Markdown. Use MinerU only after the required privacy check, verify key evidence against page-aware PDF text, and avoid loading the entire paper into context at once."
---

# Embodied Paper Deep Read

Run **acquire → MinerU or local index → evidence pass → figures → write → publish**. Preserve
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

- For a public arXiv paper, MinerU may be used unless the user requests a local-only workflow.
- For a user-supplied, unpublished, review-confidential, proprietary, or otherwise non-public
  PDF, obtain explicit consent before uploading it. Without consent, use the local page-aware
  index and PDF inspection only.
- Accept MinerU credentials only from the `MINERU_TOKEN` environment variable or the user's
  own `~/.mineru_token` file (mode 600). If neither exists, stop with setup instructions.
  Never ask the user to paste a token into chat, read a token from a repository file, or embed
  one in commands, logs, skill source, or generated notes.
- Never disable TLS verification. Respect the user's standard proxy and CA configuration.

## Quick start

Resolve `<skill-dir>` to the directory containing this `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/fetch_arxiv.py "<arxiv-link-or-id>" \
  --dir "<paper-folder>" --slug "<slug>"

MINERU_LANGUAGE=en bash <skill-dir>/scripts/mineru_parse_pdf.sh \
  "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru"
```

For a user-supplied PDF, first create the local page-aware index without uploading it:

```bash
python3 <skill-dir>/scripts/index_pdf.py "/path/to/paper.pdf" \
  --dir "<paper-folder>" --slug "<slug>"
```

The preferred MinerU path writes:

- `<paper-folder>/mineru/full.md`
- `<paper-folder>/mineru/images/`

The fetcher remains the stable PDF/cache fallback. Keep its durable outputs inside the same paper folder when they are needed:

- `<paper-folder>/<slug>.pdf`
- `<paper-folder>/<slug>_meta.json`
- `<paper-folder>/<slug>_full.txt`, with explicit page separators
- `<paper-folder>/<slug>_pages.jsonl`, one UTF-8 JSON record per page

Use `--refresh` only when the source changed or the cache is invalid. Use the page-aware PDF
fallback when MinerU is unavailable, disallowed by the privacy rule, malformed, or missing
page-cited evidence.

## Pipeline

### 1. Acquire, index, and build evidence notes

Create the paper folder first, then acquire/index the source so PDF/cache artifacts stay in
that folder. After the privacy check, run MinerU once when allowed. Read
`references/reading-scope.md`, inspect MinerU Markdown by section in bounded batches, and reopen
`_pages.jsonl`/PDF only to verify page numbers, equations, tables, and ambiguous claims. Build a
compact `<slug>_evidence.md` containing page-cited facts for motivation, method, data,
experiments, limitations, relevant appendix evidence, figures, and unresolved questions.

### 2. Inventory and extract figures

Read `references/figure-extraction.md`. Use MinerU's `images/` and Markdown image references to
**select** figures and build the manifest. If the MinerU task is still pending, wait for the
MinerU result instead of independently rendering or cropping paper figures.

**Then re-render the selected figures before publishing** — MinerU caps its own images near
~1100px wide, too soft at 2x/Retina, and a display width above the file's pixel width upscales
it visibly:

```bash
python3 <skill-dir>/scripts/render_figures.py \
    <paper.pdf> <paper-folder>/mineru --out figs_hires --pick <prefix>=<label>:<width>
```

This keeps MinerU's own bboxes (from `mineru/layout.json`) and redoes only the rasterization.
Never derive figure boundaries yourself, map by image filename rather than figure number, and
check the printed aspect-ratio table — the reasons for all three are in
`references/figure-extraction.md` "Resolution".

Use manual PDF cropping only after MinerU output is available and demonstrably
misses a needed figure, splits a composite badly, or produces an unusable image; for ambiguous
fallbacks, ask the user before substituting manual crops. Keep related-work external figures
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

Before publishing a chapter, run the layout self-check in `writing-style.md`.

### 4. Publish through one backend

Load only the selected publisher:

- Feishu: `publishers/feishu.md`
- Local Markdown: `publishers/local-md.md`

Publish text first and images second. Treat the figure manifest line
`file | anchor | width | caption` as the durable write/publish contract.

Write Chinese punctuation full-width from the start (see `references/writing-style.md`
"Chinese punctuation and mixed-language typography"). To normalize or audit a block's XML,
pipe it through `scripts/normalize_cjk_punct.py` (stdin → stdout); it preserves half-width in
ratios, latex, URLs, and version strings.

## Completion checks

- Cover the paper's argument, main method, decisive experiments, limitations, and relevant
  appendix material.
- Cite page numbers in evidence notes so any claim can be reopened without rereading the PDF.
- Do not invent dimensions, data ratios, stages, or claims absent from the paper.
- Preserve every material technical claim, decisive metric, assumption, caveat, failure case,
  and causal link needed to reconstruct the paper's argument. Remove duplication, filler, and
  unsupported material.
- **Chinese prose uses Chinese punctuation.** In Chinese sentences, use `，`、`。`、`：`、`；`、`（ ）`、`“ ”`; reserve ASCII punctuation for code, commands, URLs, file paths, XML/HTML, LaTeX, JSON, exact titles, model/package names, and quoted source text. See `writing-style.md`.
- Use real hierarchy rather than text walls; follow `writing-style.md`.
- On Feishu, use native heading sequences; never embed chapter numbers in H1/H2/H3 text.
- Center all figures/whiteboards and make every table full-width with centered cells. Render
  loss functions and long equations as standalone centered display blocks.
- **Publish figures at ~2× their display width, never above their pixel width.** Re-render the
  selected figures from the PDF at MinerU's own `layout.json` bboxes (`render_figures.py`)
  instead of publishing MinerU's ~1100px-capped JPEGs; confirm the ratio-check table passes and
  eyeball the teaser plus any figure whose caption cites specific numbers.
- Do not reload an unchanged PDF, regenerate an unchanged index, or refetch Feishu after every
  image operation.
