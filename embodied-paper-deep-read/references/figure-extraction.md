# Figure extraction (phase 2)

Prefer figures already extracted by MinerU into `images/` — but **select** from them, do not
publish them as-is: MinerU caps its own images near ~1100px wide, which renders soft at 2x
(see "Resolution" below). Re-render the selected figures from the PDF at MinerU's own bboxes
instead. Crop by hand with PyMuPDF only when MinerU output is missing, split incorrectly, low
quality, or mismatched with the caption. Avoid web screenshots and repeated full-page renders.

## Inventory once

```bash
rg -n '!\[|<img' <paper-folder>/mineru/full.md
find <paper-folder>/mineru/images -maxdepth 1 -type f | sort
```

Use Markdown image references as the primary inventory. Match each image to nearby caption
or section text. Select overview, architecture, decisive qualitative comparison, useful
ablation, and failure cases. Usually 3–6 figures are enough; each must add information.

If the MinerU task is still pending, wait for it to finish before producing the figure
manifest. Do not independently render pages or crop paper figures while MinerU is pending.
Only consider PDF cropping after MinerU output is available and a selected figure is missing,
badly split, or unusable; when the fallback is not obvious, ask the user before replacing the
MinerU asset with a manual crop.

If MinerU does not provide usable figures, fall back to PDF inventory:

```bash
python3 <skill-dir>/scripts/extract_figures.py paper.pdf \
  --scan-all figures.json
```

The fallback inventory records per-page caption lines and raster bboxes.

## Resolution: re-render at MinerU's own bboxes

MinerU exposes **no** resolution / DPI / scale parameter — verified against the official CLI
and output-format docs, and absent from the API request body. It caps extracted images near
**~1100px wide**, and rasterizes vector charts far below that (panels land around 685px).

That is too soft for a Retina reader. A figure displayed at 760 CSS px needs
`760 × 2 ≈ 1520` physical pixels; 1050px is only 0.69× of that and reads blurry. **Also never
set a display width above the asset's pixel width** — publishing a 685px image at 760px
upscales it and is the most visible failure.

The fix is to keep MinerU's *boundaries* and redo only the *rasterization*:

```bash
python3 <skill-dir>/scripts/render_figures.py \
    <paper.pdf> <paper-folder>/mineru --out figs_hires \
    --pick bcedd339=Fig1:760 --pick f58ef364=Fig10:760
```

`--pick <filename-prefix>=<label>[:<display-width>]`; omit every `--pick` to render all of them.
Reads `mineru/layout.json`, renders each bbox at `display-width × 2`, and prints a
ratio-check table. Publish `figs_hires/*.png` and keep the display width unchanged — the
uplift is pixel density, not layout.

Three rules make this safe, each learned from a real failure:

- **Never derive figure boundaries yourself.** Heuristics over text blocks and drawing rects
  mis-frame figures: one pass swallowed the paper title, authors, and URL into the teaser; the
  next clipped a side-by-side panel in half. `layout.json` carries MinerU's own detected bbox
  per figure (same `pdf_info` structure as `middle.json`) — use it as the authority. Given a
  correct rect, rendering is deterministic and safe.
- **Map by image filename, never by figure number.** MinerU mis-assigns caption numbers when
  two panels sit side by side (it labeled a Figure 15 panel as "Figure 14"). The filename it
  wrote for a bbox is unambiguous; the caption number is not.
- **Cross-check the aspect ratio** against MinerU's own raster for that filename. Matching
  ratios (within ~4%) prove you cropped the same region at higher resolution. The script flags
  mismatches — inspect those visually before publishing, and always eyeball the teaser plus any
  figure whose caption cites specific numbers.

If `layout.json` is missing, the MinerU result predates this skill keeping it. Re-run
`scripts/mineru_parse_pdf.sh` with `MINERU_REFRESH=true` to fetch it.

## Fast path and vector fallback

- If MinerU has a bbox for the figure, re-render it per "Resolution" above rather than
  publishing the JPEG.
- If MinerU split a composite figure into useful panels, either select the panel that supports
  the argument or recreate a compact comparison by using the original PDF crop.
- If the PDF inventory has a raster bbox matching the caption, crop it with `--auto`; do not
  render the page first.
- If a diagram is vector/composite and has no useful bbox, render that page at the default
  1×, inspect coordinates, then crop the final figure at the default 3×.
- Exclude the paper's original caption and write a concise Chinese caption explaining both
  what the figure shows and why it matters.

## Manifest from MinerU images

Create a manifest directly from selected MinerU image files:

```text
<!-- FIG images/figure_2.png | anchor:after-summary | w=720 | cap:图 1：…… -->
```

Keep paths relative to the Markdown package or the final working directory. If publishing to
Feishu, use the same manifest contract as cropped images: `file | anchor | width | caption`.

## PDF batch crop fallback

Create a JSON specification:

```json
{"figures": [
  {"page": 2, "auto": 0, "out": "fig1.png", "anchor": "after-summary",
   "width": 720, "caption": "图 1：……"},
  {"page": 6, "rect": [40, 70, 555, 310], "out": "fig2.png",
   "anchor": "after-architecture", "width": 720, "caption": "图 2：……"}
]}
```

Run once:

```bash
python3 <skill-dir>/scripts/extract_figures.py paper.pdf \
  --batch crop-spec.json --manifest figures.manifest
```

The manifest contains durable lines:

```text
<!-- FIG fig1.png | anchor:after-summary | w=720 | cap:图 1：…… -->
```

Keep stable descriptive anchors until publishing resolves backend block IDs.

## Qualitative-section layout

Do not stack several figures first and explain all of them in one trailing paragraph. Interleave
each evidence group with its interpretation in this order:

1. H3 comparison/theme title
2. one short orientation paragraph
3. centered figure with caption
4. concise observations or a centered comparison table
5. optional one-paragraph synthesis

Show the figure before the observations/table that interpret it. Keep each observation tied to
visible evidence in that figure; avoid repeating the caption verbatim.

## Related-work figures (explicit opt-in only)

Do not search for or extract figures from other papers by default. Activate this branch only
when the user explicitly asks for related-work/comparative architecture visuals. For a named
method in **相关工作**, add a figure only when it materially helps explain the lineage or
contrast. Search only primary sources: the method's arXiv/publisher PDF, official project page,
or official repository. Confirm the paper title and authors before using it.

- Prefer 1–2 high-value external figures, not one figure per cited paper.
- Download the source PDF and crop the real figure with this script; do not screenshot search
  results, blog posts, or paper-viewer pages.
- Write a new Chinese caption that states the model and learning value, and include the source
  paper/title link in the caption or adjacent text.
- Preserve source attribution for every reused figure. If the final note will be public, verify
  that the source license or permission allows republication; otherwise link to the original
  figure instead of embedding it.
- Time-box the search and skip immediately when no authoritative source, usable resolution, or
  clearly helpful figure is available. This opt-in enrichment must never block the main paper.
- Do not select an external figure that duplicates the main paper's own architecture figure or
  the concise pipeline diagram.
