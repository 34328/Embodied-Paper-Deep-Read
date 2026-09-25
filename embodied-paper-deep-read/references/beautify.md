# Beautify (phase 3)

> Use Feishu/Markdown-native components with restraint. Hierarchy comes from
> headings first; color and components are accents, not decoration.

## Callouts

Three callout types, each with a fixed emoji + background color on Feishu:

- **💡 精华提炼** — `light-blue`. Place one callout immediately after the 论文基本信息
  table. Lead with a concise, evidence-backed statement of the source's main contribution or
  conclusion, then add a few non-redundant bullets that expose its distinct technical points.
  Choose labels to fit the actual source: model mechanism, data pipeline, evaluation protocol,
  system behavior, and evidence limits are possible topics, not required fields. Keep only
  headline facts and decisive numbers; explain implementation details in the relevant chapter.
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
- **Every table should span the usable width on Feishu.** Center headers and short numeric or
  categorical values; left-align multi-line explanatory cells so mechanisms and caveats are
  readable. Give explanatory columns enough width with a sensible `colgroup`. If a long-text
  table is still cramped, split it by theme or use explanatory bullets instead of shrinking
  the text. Do not spend extra iterations chasing pixel-perfect width when it reads well.
- Use tables for brief values compared along shared dimensions. A risk, mechanism, or evidence
  column is useful when its cells remain compact; move explanations that need full sentences
  into adjacent prose or complete bullets, with source locators next to the supported claims.
  Avoid repeating the same page locator in every row when one nearby citation clearly supports
  the grouped comparison. Do not delete an informative column merely because it discusses risk.
- Preserve sensible column ratios when scaling a table to full width.

## Paragraph rhythm and page density

Apply this to every chapter, not only results and discussion. Visual hierarchy should expose
the argument while retaining its technical detail.

- Give each paragraph one job: frame a question, explain a mechanism, interpret evidence, or
  state a limitation. A normal paragraph is usually 2–4 sentences and about 80–180 Chinese
  characters.
- More than 220 Chinese characters is a review trigger, not an automatic cut-off. Split the
  paragraph when it combines separate stages, parallel findings, several metrics, or a claim
  with unrelated caveats. Keep one continuous causal argument together when splitting would
  make its reasoning harder to follow.
- Under an H2/H3, start with a short orientation, then use genuine subheadings, complete
  explanatory bullets, a comparison table, or a process diagram for distinct parts. Three or
  more consecutive dense paragraphs under one heading require restructuring or an explicit
  reason to keep them as prose.
- For a technical module, explain its purpose and mechanism in prose; use a table for repeated
  fields such as module / input / output / role, and a diagram for sequence or branching. Follow
  the visual with interpretation. Do not move essential explanations into a table alone.
- Keep paragraphs, lists, tables, and figures in reading order. Avoid repeated callouts, bold
  labels at the start of every paragraph, and components that restate the same content.

Before publishing, run `scripts/check_text_density.py --threshold 220` on the exact Markdown or
Feishu HTML/XML draft. It checks two risks:

- **Long block:** any paragraph, list item, table cell, blockquote, or callout over the
  single-block threshold.
- **Prose-wall run:** within one heading, a three-paragraph sliding window whose average is at
  least 110 CJK characters and where at least two paragraphs contain 80 or more CJK characters.
  Three consecutive top-level bold-lead paragraphs are also flagged regardless of length.

Headings, lists, tables, callouts, blockquotes, display formulas, figures, and whiteboards break
a prose run. Inline math does not. Overlapping windows merge into one candidate so a five-block
wall is reported once rather than as three noisy warnings.

Every candidate needs review before completion. Restructure parallel or separately
scannable material with the least elaborate fitting form: complete bullets for parallel facts,
a compact table for repeated fields, a real H3 for a sustained module, or a process diagram for
multi-stage or branching flow. A candidate may remain as prose when it forms one coherent
reading unit and the rendered section is visually readable. Record that decision in the working
notes or publish state; do not add internal QA narration to the user-facing completion summary.
The checker discovers risk but never chooses a component or edits the draft. Only a confirmed
text wall that remains unresolved blocks completion.

A clean exit is the structural rhythm gate, not proof of visual quality. Inspect each H2 as a
rendered reading unit, including cramped tables and dense figures, and confirm citations,
parameters, conditions, and caveats survive any restructuring.

## Figures and diagrams

- Center every raster figure, attachment preview, and diagram/whiteboard. On Feishu, insert
  images with `--align center`; treat whiteboards as centered block components and preview them
  once after insertion.
- This is a document-wide invariant, not an optional styling preference.
- In qualitative comparisons, interleave image and analysis; never place multiple images in a
  row followed by one undifferentiated explanation block.

## Results / discussion / limitations: structure every section for scanning

These sections are especially prone to text walls. State the result or limitation clearly,
then choose the least elaborate form that lets the reader inspect its evidence: connected prose
for one argument, complete bullets for distinct findings, a compact table for shared comparison
fields, or a figure when visual detail matters. Do not restate the same findings in a table,
bullets, and a following paragraph. Keep the interpretation that explains *why* the evidence
matters; move long reasoning out of table cells.

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
  `content-depth.md`. Place it where its stages are explained. Verify its rendered
  preview and do not duplicate the source's own architecture figure.

## Backend note

These are Feishu-native affordances. On a Markdown backend, map callouts to blockquotes
with the emoji prefix (`> 💡 **精华提炼** …`) and drop the background colors — the
*content* and placement stay identical. See `publishers/local-md.md`.
