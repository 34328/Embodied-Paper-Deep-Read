# Content depth (phase 3)

> A deep-read must be concrete enough to reconstruct the source's main technical
> argument and its evidential limits.

## Put evidence next to the claim in the published note

The evidence file is a checkpoint, not the reader's citation system. In the final
document, cite the PDF page next to each central technical claim, dataset statistic,
numerical comparison, and material limitation; include the source's figure, table,
or equation number when one carries the evidence. Use a locator such as
`（PDF 第 5 页，图 2）` or `（PDF 第 8 页，表 3）`. If printed and PDF pagination differ,
keep `PDF 第 n 页` as the stable locator and add the printed page only when useful.
Group a few adjacent claims under one citation only when the same source passage
supports all of them. Cite separately when the evidence changes.

Distinguish the authors' reported result or interpretation from this note's own
calculation or assessment. Show the inputs and conditions for a derived comparison.
For a parameter, data ratio, protocol detail, or ablation that materially affects
interpretation but is absent from the source, write `原文未披露` rather than estimating
or filling a plausible default. Do not turn an unknown into a claim of absence.

## Coverage applies across both reading categories

Use the two categories in `doc-structure.md` to choose emphasis, not to decide which reported
technical content may be omitted. A paper or technical report may combine a model, data
pipeline, training recipe, benchmark, real-world system, safety analysis, and deployment
details. Cover each reported area that supports a central claim, affects reproducibility or
interpretation, or determines where the result can be used, even when it is secondary to the
selected category.

While building `<slug>_evidence.md`, keep an internal coverage inventory for the areas present
in the source: model/system design; data sources and processing; training; experiments or
benchmark protocol; real-world/system evaluation; safety, privacy, or deployment; and
limitations/failures. For each material item, capture the steps or mechanism, consequential
choices and parameters, rationale when stated, evidence and outcome, limitations, and page
locators. Map it to a final chapter before drafting. Do not add empty headings for absent
content. When an unreported detail is necessary to interpret or reproduce a central claim,
state `原文未披露`.

Match detail to the source's technical density, not its label as a paper or report. For a dense
report, organize related details into compact tables and process diagrams, while explaining
the choices and consequences in prose. For a shorter paper, preserve the same coverage standard
without padding. Summarize repeated or peripheral details, but retain every material technical
claim, condition, caveat, and causal link.

## Methods need real dimensions

- For model and algorithm papers, explain each material module's mechanism and role;
  record its **input/output dimension and format when reported**. For a multi-module
  architecture, summarize the reported interfaces in a table (模块 / 输入 / 输出 /
  作用), including patch features, token dimensions, or head outputs where available.
  Mark a missing dimension that matters to understanding as `原文未披露`; do not infer it.
- Name concrete hyperparameters when the source gives them: number of blocks, heads,
  hidden dimension, MLP ratio, ViT variant, etc. Separate training-only components
  from the inference path and explain what each design choice changes.

## Visualize multi-stage methods when useful

For a model or algorithm with at least three dependent stages or a meaningful
output/training branch, place one concise pipeline **after the architecture
explanation and before the module input/output table when one is warranted**. For a
reported data pipeline, a process diagram may instead show the reported
acquisition, processing, quality-control, and release/evaluation path; it does not
require a model-module table. On Feishu use a Mermaid whiteboard; on Markdown use
a fenced Mermaid block.

- Show the main data path, module boundaries, output branches, and training-only branches.
- Keep node labels short; leave tensor details and hyperparameters to the
  accompanying table or prose.
- Complement rather than redraw the paper's architecture figure: the original figure preserves
  visual design, while the pipeline makes execution order and branching easy to scan.
- Omit the diagram when prose already makes the stages and dependencies clear.
- After publishing, export/preview the whiteboard once to verify that labels, arrows, and layout
  render correctly.

## Math / tensor dims: inline only when short

Tensor shapes and math symbols go in **inline LaTeX**, not inline code fences:

- Right: `<latex>\mathbb{R}^{1024 \times H/14 \times W/14}</latex>`
- Wrong: `<code>R^{1024×H/14×W/14}</code>`

This applies to dimensions, formulas, factorization equations (`G = s · T · R · D`),
loss terms, everything mathematical. On a Markdown backend, use `$…$` instead.

Use inline `<latex>` only for short symbols and shapes that belong grammatically inside a
sentence. Put every loss definition, multi-term equation, update rule, or visually long formula
on its own centered line:

```xml
<p align="center"><latex>\mathcal{L}=\lambda_1\mathcal{L}_1+\lambda_2\mathcal{L}_2</latex></p>
```

- Do not append prose, punctuation-heavy explanations, or coefficient values after a display
  equation on the same line.
- Put a second long coefficient/update expression in its own centered formula block; otherwise
  move coefficients into a centered table.
- On Markdown use `$$…$$` display math for these formulas, not inline `$…$`.

## Training data and data-resource tables

When the source reports model-training composition, give a table using the main text and
relevant appendix. Include the fields that are reported and material: source/dataset, size or
units, modality or task, mixing ratio, filtering or annotation, purpose/training stage, and
whether it is used for training, validation, or evaluation. If a value is not reported, mark a
consequential gap `原文未披露` instead of calculating a ratio from incompatible counts.

For a data resource or benchmark, use a table when it makes the source's data inventory clearer.
Select fields supported by the paper, such as source, scale, modality, task, annotation, split,
quality controls, license, and intended use. Explain relationships and design rationale in
prose; do not turn a table into a substitute for describing the pipeline.

- If the paper only does single-stage finetuning, say so honestly ("监督用途") — **do not
  invent** pre-training / post-training stages that aren't there.
- Distinguish geometry-only vs. motion-annotated datasets if the paper does.

## Data pipelines, datasets, and benchmarks wherever they appear

Apply this section whenever the source contains material data governance, a data pipeline, a
dataset, or a benchmark, whether it is the primary contribution or part of a model/system
technical report. Explain the technical decisions that make the contribution work and the
evidence that tests them; use only fields supported by the source.

- For a data pipeline or governance report, trace reported provenance, collection
  and selection rules, annotation or synthesis, deduplication, quality control,
  mixtures, updates, and known coverage or privacy limits. Explain how each
  decision affects the resulting data or downstream task when the report tests it.
- For a dataset or benchmark report, define the tasks and units of evaluation,
  splits, metric computation, allowed inputs, baseline setup, and any leakage or
  contamination controls. Explain what the benchmark measures and what its
  protocol cannot establish. Mark important undisclosed controls explicitly.

## System, real-world, safety, and deployment details

When these details are part of the reported contribution or evidence, explain the concrete
setup rather than summarizing it as “validated in the real world.” Include reported robot or
hardware, sensors, control frequency, action interface, runtime components, latency or compute,
operator intervention, task/environment conditions, number of trials, safety constraints, and
deployment failures when available. Separate an illustrative demo from a controlled evaluation;
state what the evidence does and does not establish. Mark material missing details as
`原文未披露` and cite the relevant pages.

## Experiment tables: faithful but selective

- Reproduce a complete table only when it is central and reasonably sized. Otherwise keep
  the paper's method, strongest/representative baselines, datasets, metrics, and rows needed
  for the claim. State explicitly which secondary rows or columns were omitted.
- Do not duplicate the same numbers in prose, a recreated table, and a figure. Choose the
  representation that makes the comparison clearest.
- Keep the dataset, metric, evaluation conditions, and baseline identity alongside
  each decisive number. Distinguish absolute differences (percentage points) from
  relative change; do not call a result a win when the table does not show one.
- Highlight the source's method row only when it helps the comparison, and identify
  a best result only where the reported evidence supports it — see `beautify.md`.
