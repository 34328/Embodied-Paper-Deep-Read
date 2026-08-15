# Beautify (phase 3)

> Source rule: skill_notes §五. Feishu/Markdown-native components, used with restraint.
> Hierarchy comes from headings first; color and components are accents, not decoration.

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
- **📘 名词小抄** — `gray`. One callout collecting brief plain-language glosses of the
  uncommon modules/terms (e.g. DPT head, DINOv2, alternating-attention, factored
  representation) so the reader isn't stranded. Place it near where the terms first cluster
  (usually in 方法).

Feishu callout syntax (confirm exact attributes against the lark-doc embedded skill):
`<callout emoji="💡" background-color="light-blue"> … </callout>`.

## Tables

- Header row: light-gray background.
- The protagonist / best row (the paper's own method or the winning result): light-blue
  background + bold.
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

These sections are where documents most often collapse into text walls (a 300–400 字 paragraph
per finding, or a bold-lead run). When a result, discussion, or limitation section contains 2+
parallel findings, conditions, comparisons, or failure modes, use the scannable skeleton below.
If the section is a single continuous argument, keep it as short prose — do not force a template.

**Scannable skeleton for parallel findings:**
1. One **framing sentence**: what this experiment asks and the headline verdict.
2. The **evidence**: a centered figure, a full-width table, or a short list of the decisive
   numbers — whichever shows the comparison most clearly (don't repeat the same numbers in all
   three).
3. A **list of findings/observations**, one complete bullet each, when there are 2+ parallel
   results, conditions, or failure modes. A single continuous result stays as one short
   paragraph.
4. Optional one-line takeaway.

Concretely: a finding like "ID 100% vs DP 80%; harder task 90% vs 20%; OOD 80% vs 0%" is three
parallel comparisons → a **list** or table, never one paragraph. A qualitative analysis that
enumerates failure modes (阶段混乱、消歧失败、视野外目标) is a **list**, not a run-on paragraph.

**Highlight the key result, sparingly.** At most one accent per result section:
- the winning row of the results table (light-blue + bold), or
- a single **🏁 关键结果** / **💡** callout stating the one number or conclusion that matters most
  (e.g. "字母积木指令跟随 87% vs π0 9%，接近 10×").

Do not callout every finding — if everything is highlighted, nothing is. Reserve color for the
one comparison that carries the section's claim.

- Build hierarchy from heading levels + a little bold/color. Don't componentize
  everything — no whiteboard for something a sentence handles, no callout for ordinary
  prose.
- Use a Mermaid pipeline only when the method flow meets the trigger in `content-depth.md`.
  Place it before the input/output table and verify its rendered preview; do not duplicate the
  paper's architecture figure.

## Backend note

These are Feishu-native affordances. On a Markdown backend, map callouts to blockquotes
with the emoji prefix (`> 💡 **精华提炼** …`) and drop the background colors — the
*content* and placement stay identical. See `publishers/local-md.md`.
