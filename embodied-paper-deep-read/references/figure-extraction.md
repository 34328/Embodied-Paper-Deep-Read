# Figure extraction (phase 2)

Use MinerU's `full.md` image references and `images/` to **select** figures, but do not publish
the extracted images as-is: their resolution may be too low at 2x display density. Re-render
selected figures from the source PDF at MinerU's own boxes when `layout.json` supplies usable
ones. When a new MinerU result has no layout boxes, or a box is missing, split, or wrong, crop
the selected figure from the source PDF with PyMuPDF. Avoid web screenshots and repeated
full-page renders. PyMuPDF's role here is image work, not parsing the paper's body.

## Inventory once

```bash
rg -n '!\[|<img' "<paper-folder>/mineru/full.md"
find "<paper-folder>/mineru/images" -maxdepth 1 -type f | sort
```

Use Markdown image references as the primary inventory. Match each image to nearby caption
or section text. Select overview, architecture, decisive qualitative comparison, useful
ablation, and failure cases. Usually 3–6 figures are enough; each must add information.

If the MinerU task is still pending, wait for it to finish before finalizing the figure
selection. If MinerU fails, stop the deep-read per `SKILL.md`; PDF image cropping cannot replace
the required body parse. Once MinerU body output is available, use PDF cropping for selected
figures whose layout boxes are absent or unusable. Resolve figure identity against the PDF page
and caption before publishing.

If MinerU does not provide usable figures, fall back to PDF inventory:

```bash
python3 <skill-dir>/scripts/extract_figures.py "<paper-folder>/<slug>.pdf" \
  --scan-all "<paper-folder>/figures.json"
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
    "<paper-folder>/<slug>.pdf" "<paper-folder>/mineru" \
    --out "<paper-folder>/figs_hires" \
    --manifest "<paper-folder>/figures.manifest" \
    --pick bcedd339=Fig1:760 --pick f58ef364=Fig10:760
```

`--pick <filename-prefix>=<label>[:<display-width>]`; omit every `--pick` to render all of them.
Reads `mineru/layout.json`, renders each bbox at `display-width × 2`, and prints a
ratio-check table. On success, `--manifest` atomically replaces the selected MinerU-image paths
in `figures.manifest` with the corresponding `figs_hires/*.png` paths. Keep the display width
unchanged — the uplift is pixel density, not layout. If rendering fails, the provisional
manifest is unchanged; fix the selection or use the PDF crop fallback before publishing.

Three rules make this safe, each learned from a real failure:

- **Use MinerU's box when it is present and correct.** Heuristics over text blocks and drawing
  rects can mis-frame figures: one pass swallowed the paper title, authors, and URL into the
  teaser; the next clipped a side-by-side panel in half. `layout.json` carries MinerU's detected
  box per figure (same `pdf_info` structure as `middle.json`). Check the crop against the source
  PDF; a visually wrong box needs the PDF crop fallback.
- **Map by image filename, never by figure number.** MinerU mis-assigns caption numbers when
  two panels sit side by side (it labeled a Figure 15 panel as "Figure 14"). The filename it
  wrote for a bbox is unambiguous; the caption number is not.
- **Cross-check the aspect ratio** against MinerU's own raster for that filename. A mismatch
  can reveal a wrong box, but a match cannot prove the region is correct. Rendering now fails
  without updating the manifest if the ratio check fails or the comparison image is missing.
  Inspect each selected result against the PDF, especially the teaser and figures whose
  captions cite specific numbers.

If `layout.json` is missing from a newly completed MinerU result, the model may not emit it.
Do not re-upload only to seek layout data; use the PDF crop fallback. Refresh an older cached
result only when you know that its original package contained layout data that was discarded.

## Fast path and vector fallback

- If MinerU has a correct bbox for the figure, re-render it per "Resolution" above rather than
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

Create a provisional `<paper-folder>/figures.manifest` from the selected MinerU image files.
Paths are relative to the manifest's parent folder:

```text
<!-- FIG mineru/images/figure_2.png | anchor:after-summary | w=720 | cap:图 1：…… -->
```

After successful re-rendering, `--manifest` replaces the file path with, for example,
`figs_hires/Fig1.png`. When using PDF crops, write the crop's final path instead. Publish only
after every manifest path resolves to a final high-resolution file inside `<paper-folder>`;
the same `file | anchor | width | caption` contract applies to Feishu and Markdown.

## PDF batch crop fallback

Create a JSON specification:

```json
{"figures": [
  {"page": 2, "auto": 0, "out": "<paper-folder>/figs_hires/fig1.png", "anchor": "after-summary",
   "width": 720, "caption": "图 1：……"},
  {"page": 6, "rect": [40, 70, 555, 310], "out": "<paper-folder>/figs_hires/fig2.png",
   "anchor": "after-architecture", "width": 720, "caption": "图 2：……"}
]}
```

Run once:

```bash
python3 <skill-dir>/scripts/extract_figures.py "<paper-folder>/<slug>.pdf" \
  --batch "<paper-folder>/crop-spec.json" \
  --manifest "<paper-folder>/crop-figures.manifest"
```

The batch crop defaults to 3× PDF scale. Set an entry's `zoom` higher when needed so its PNG
has about twice the intended display width, and never set the display width above the PNG's
actual pixel width. Inspect the cropped image against the original PDF page and caption.

The crop manifest contains durable lines:

```text
<!-- FIG figs_hires/fig1.png | anchor:after-summary | w=720 | cap:图 1：…… -->
```

Replace the corresponding provisional entries in `<paper-folder>/figures.manifest` with these
crop entries. Do not pass the master manifest as `--manifest` for a mixed render/crop selection:
`extract_figures.py` writes a new file and would erase the already-rendered entries. Check that
every final master-manifest path resolves to the intended high-resolution image.

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
