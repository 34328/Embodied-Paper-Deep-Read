# Document structure (phase 3)

> Choose one of two content paths. Keep the shared five-chapter spine; adapt the internal
> sections to the source. Feishu uses native auto-numbering.

## Classify by research focus, not document format

There are exactly two top-level reading categories:

- **模型类（Foundation Model / Model-centric）** — the central research object is a model,
  its capabilities, architecture, training method, or inference behavior. This includes
  foundation models, VLA, world models, and other model or algorithm papers.
- **数据类（Data-centric）** — the central research object is a dataset, data-generation or
  curation pipeline, data governance, or a benchmark and its evaluation protocol. Benchmarks
  are part of this category, not a third category.

“Technical report” describes a document format, not a reading category. A report may contain
model design, data pipelines, evaluation, robot or system integration, safety, and deployment
in one source. Select the category whose research object best matches the central claim and
strongest evidence, record the other material contributions, and cover every technically
material area the source actually reports. The selected category sets emphasis; it never
removes a reported pipeline, model, experiment, or system result from the note.

Before drafting, make a compact source-wide coverage inventory in `<slug>_evidence.md` and map
each material contribution to a final chapter. Apply the coverage and evidence-detail criteria
in `content-depth.md`. Omit only content that is absent or immaterial; never infer an unreported
stage or parameter.

## Shared five-chapter spine

Use this chapter order for both categories. Keep the five-chapter structure stable; adapt the
subsections so the central object and every material secondary contribution are explained.

- **论文基本信息** — *front matter, unnumbered.* A table: 标题 / 作者 / 机构 / 发布
  (arXiv id + date, when available) / 项目主页 (when available) / 研读类别（模型类或数据类）.
  Immediately follow it with the **精华提炼** callout (see `beautify.md`).
- **1 研究背景与动机** — define the problem and why it matters; group related methods or
  datasets by role; state the paper's claims and contributions in your own words.
- **2 方法与技术设计** — explain the central model or data contribution and every material
  supporting system, data, training, or evaluation component. Use the category paths below.
- **3 实验结果与证据** — organize by claim or result theme. Cover evidence for the model,
  data resource, benchmark, system, and secondary contributions that the source reports.
- **4 局限性与适用边界** — separate author-stated limitations from evidence-based limitations
  found in this reading; do not attribute the latter to the authors.
- **5 结论与意义** — state what the evidence supports, where the work applies, and how the
  authors' outlook differs from demonstrated results.
- **文末原文来源** — use an arXiv bookmark when available; otherwise link an available DOI,
  publisher, or official source. Do not invent a public link for a local-only PDF.

### 模型类路径

In chapter 2, adapt these subsections to the source:

- **训练数据与数据流程** — describe reported sources, composition, selection, annotation,
  filtering, mixture, and training stage when material. A substantial pipeline gets its own
  subsection even when the primary category is 模型类.
- **模型与系统架构** — explain each material module, its role, and reported inputs, outputs,
  dimensions, and interfaces. Include robot, runtime, or system integration when it is part of
  the contribution.
- **训练与推理** — cover reported objectives, losses, schedules, initialization, inference
  procedure, and deployment settings. Do not invent a stage the source does not describe.

For results, include the decisive model comparisons and ablations, plus material data-quality,
robustness, real-robot/system, latency, safety, or deployment evidence present in the source.

### 数据类路径

In chapter 2, adapt these subsections to the source:

- **数据目标与来源** — define the target tasks and population, source domains, collection
  conditions, licenses or consent, and intended use when reported.
- **构建与治理流程** — trace reported filtering, deduplication, annotation or synthesis,
  quality control, curation, mixture decisions, versioning, and release. Explain important
  design choices and their effects, rather than listing steps without rationale.
- **数据资产与评测协议** — describe schema, modalities, splits, task definitions, metrics,
  baseline setup, allowed inputs, and leakage or contamination controls as applicable. Include
  model details when needed to interpret baselines or downstream utility.

For results, cover data quality and coverage, benchmark diagnostics, downstream utility,
baseline comparisons, robustness, and failure analysis that the source reports.

### Reports with both kinds of contribution

Choose one of the two categories as the organizing path, then give each substantial secondary
contribution a named subsection under chapter 2 and matching evidence under chapter 3. For
example, a foundation-model technical report may need full sections on data construction,
robot evaluation, and deployment; a data report may need a detailed account of the models used
to establish downstream value. Do not compress such content into a passing sentence or omit it
because it is not the primary contribution. Allocate detail by technical importance and
evidence, not by paper genre or equal word count.

“核心创新” is not a mandatory subsection. Surface a genuine distinctive idea in its relevant
section or a concise callout; do not manufacture one. If the source lacks a subsection, fold it
in honestly instead of padding.

## Numbering: Feishu-native auto only

**Hard invariant: heading text contains no numeric prefix.** Never hand-type `1`、`1.`、
`1.1`、`1.2.1`、`一、` or `（一）` into an H1/H2/H3 title. A heading that merely looks numbered is
wrong; it must carry Feishu's native `seq` attributes so insertion/deletion re-numbers it:

- Chapter start: `<h1 seq="1" seq-level="auto">研究背景与动机</h1>`
- Continue chapters: `<h1 seq="auto" seq-level="auto">方法</h1>`
- Sub-headings restart per chapter: first H2 in a chapter `seq="1"`, rest `seq="auto"`,
  all with `seq-level="auto"`.
- When an H2 genuinely needs research-line/method-family subsections, start its first H3 with
  `seq="1"` and continue sibling H3 blocks with `seq="auto"`, all with
  `seq-level="auto"`. Do not create H3 for a lone lead-in sentence.
- Front matter (论文基本信息) and the end source section are **unnumbered** — plain
  `<h1>` with no `seq`.

Before publishing, inspect the generated XML: numbered H1/H2/H3 blocks must have both `seq` and
`seq-level="auto"`, and their inner text must begin directly with the title. After publishing,
fetch the outline and representative headings with `--detail full`; reject any numbered title
whose text still begins with a pattern such as `2 方法` or `2.1 网络架构`.

For a non-Feishu backend (local md), numbering is literal Markdown `#`/`##` and you may
write "1"、"1.1" as text — see `publishers/local-md.md`. The auto-numbering rule is a
Feishu concern; keep the *structure* identical across backends.
