# Beautify (phase 3)

> Use Feishu/Markdown-native components with restraint. Hierarchy comes from
> headings first; color and components are accents, not decoration.

## Callouts

Three callout types, each with a fixed emoji + background color on Feishu:

- **💡 精华提炼** — `light-blue`. Place one callout immediately after the 论文基本信息
  table. Write **one sentence stating the paper's central conclusion, followed by 3–5 concise
  bullets** with bold labels such as 核心方法、规模/数据、主要结果、迁移价值. Keep only
  headline facts and decisive numbers; move module-level implementation details into 方法.
  This executive-summary list is an intentional exception to the prose-first rule.
- **⭐ 核心创新** — `light-yellow`. **Only when the paper has a genuine standout
  innovation.** Fold it into the relevant method section, don't give it its own heading.
  Not every paper gets one — omit if there's nothing truly novel.
- **📘 术语与符号** — `gray`. When uncommon modules, terms, or symbols need a
  compact explanation, collect their precise definitions in one callout near where
  they first appear (usually in 方法). Keep the source's distinctions intact.

Feishu callout syntax (confirm exact attributes against the lark-doc embedded skill):
`<callout emoji="💡" background-color="light-blue"> … </callout>`.

## Tables

- Header row: light-gray background.
- Highlight one row only when it carries the table's central comparison: the
  source's method or the best result supported by the reported metric. Do not style
  the source's method as the winner if it does not lead on that metric.
- **Every table should read as full-width and centered on Feishu:** set every `<th>/<td>` child
  paragraph to `align="center"`, and use a sensible `colgroup` that spans the available width.
  If a reliable document width can be fetched, scale to it; otherwise use stable proportional
  widths. Do not spend extra iterations chasing pixel-perfect width when the table is already
  readable, centered, and not cramped.
- Preserve sensible column ratios when scaling a table to full width.

## Figures and diagrams

- Center every raster figure, attachment preview, and diagram/whiteboard. On Feishu, insert
  images with `--align center`; treat whiteboards as centered block components and preview them
  once after insertion.
- This is a document-wide invariant, not an optional styling preference.
- In qualitative comparisons, interleave image and analysis; never place multiple images in a
  row followed by one undifferentiated explanation block.

## Results / discussion / limitations: structure every section for scanning

These sections can collapse into text walls (a 300–400 字 paragraph per finding, or
a bold-lead run). When a result, discussion, or limitation section contains 2+
parallel findings, conditions, comparisons, or failure modes, adapt the pattern
below. If the section is a single continuous argument, keep it as prose.

**Scannable skeleton for parallel findings:**
1. One **framing sentence**: what this experiment asks and the headline verdict.
2. The **evidence**: a centered figure, a full-width table, or a short list of the decisive
   numbers — whichever shows the comparison most clearly (don't repeat the same numbers in all
   three).
3. A **list of findings/observations**, one complete bullet each, when there are 2+ parallel
   results, conditions, or failure modes. A single continuous result stays as one short
   paragraph.
4. Optional one-line takeaway.

Several task-by-task comparisons usually read better as a **list** or table than
as a single paragraph. Group reported failure modes in a list when that makes
their conditions and differences easier to compare.

**Highlight the key result, sparingly.** At most one accent per result section:
- a central row of the results table (light-blue + bold), when the metric and
  direction of improvement make its status clear, or
- a single bolded **关键结果** sentence stating the decisive comparison with its task,
  metric, evaluation conditions, and nearby source citation. For success rates,
  report the percentage-point difference; use a relative ratio only when it adds
  a valid interpretation.

Reserve color for the comparison that carries the section's claim; use ordinary
structure for supporting findings.

- Build hierarchy from heading levels + a little bold/color. Don't componentize
  everything — no whiteboard for something a sentence handles, no callout for ordinary
  prose.
- Use a Mermaid pipeline when the method or data process meets the trigger in
  `content-depth.md`. For a model method, place it before the input/output table;
  for a data pipeline, place it where its stages are explained. Verify its rendered
  preview and do not duplicate the source's own architecture figure.

## Backend note

These are Feishu-native affordances. On a Markdown backend, map callouts to blockquotes
with the emoji prefix (`> 💡 **精华提炼** …`) and drop the background colors — the
*content* and placement stay identical. See `publishers/local-md.md`.
