# Document structure (phase 3)

> The method-paper skeleton below is a default, with Feishu-native auto-numbering.

## Choose the structure from the primary contribution

Identify the source's main contribution from its abstract, stated contributions, and
decisive evidence before assigning headings. Use the 1–5 skeleton below for a model or
algorithm paper, including most foundation-model, VLA, and world-model method papers.
When a report combines several contribution types, organize around its primary claim
and cover secondary contributions where they explain or test that claim. Do not force
unreported model components, training stages, or experiments into the note.

- **Data pipeline or governance as the main contribution:** keep the problem → design →
  evidence → limitations → implications progression. In the design chapter, follow the
  reported stages such as sourcing, filtering, deduplication, annotation, quality
  control, mixture decisions, and updates. In the evidence chapter, examine the
  reported data-quality, downstream-utility, and failure analyses. Use only stages
  and tests the source actually contains.
- **Dataset or benchmark as the main contribution:** make task definition, dataset
  construction, splits, metrics, evaluation protocol, and leakage controls central.
  Use the results chapter for baseline comparisons and diagnostic analyses under the
  reported protocol. Do not replace these with a generic network-architecture chapter.

For these two branches, use the following 1–5 chapter paths as starting points;
rename or fold chapters to match the source. The numbers below indicate order,
not text to type into Feishu headings.

| 顺序 | 数据管线 / 治理 | 数据集 / benchmark |
|---|---|---|
| 1 | 研究背景与数据目标 | 研究背景与评测空白 |
| 2 | 数据来源与治理机制 | 数据集与评测设计 |
| 3 | 数据质量与下游效用 | 基线结果与诊断分析 |
| 4 | 局限性 | 局限性 |
| 5 | 结论与适用范围 | 结论与使用边界 |

## Default method-paper chapter skeleton (H1 = chapter)

Adapt sub-sections to the paper, but keep this spine:

- **论文基本信息** — *front matter, unnumbered.* A table: 标题 / 作者 / 机构 / 发布
  (arXiv id + date, when available) / 项目主页 (when available). Immediately followed by the **精华提炼** callout
  (see `beautify.md`).
- **1 研究背景与动机**
  - 1.1 问题定义 — what problem, why it matters, why now.
  - 1.2 相关工作 — cover the authors' main method families and meaningful baselines; group
    similar works rather than enumerating the bibliography.
  - 1.3 核心贡献 — the paper's stated contributions, in your words.
- **2 方法**
  - 2.1 训练数据集 — reported size / ratio / purpose (see `content-depth.md`).
  - 2.2 网络架构 — reported encoder / backbone / heads and input-output dimensions.
  - 2.3 训练策略 — reported losses, schedule, init, multimodal dropout, etc.
  - Sub-titles follow the paper. **"核心创新" is NOT a mandatory subsection** — only some
    papers have a genuine standout innovation; if so, surface it as a ⭐ callout folded
    into the relevant section, not as its own heading. If there's no real innovation,
    don't manufacture one.
- **3 实验结果** — one sub-section per result theme. Reproduce only the tables needed to
  support the main claims; combine tightly related ablations.
- **4 局限性** — separate limitations stated by the authors from evidence-based
  limitations identified in this reading; do not attribute the latter to the authors.
- **5 结论与意义** — what the evidence supports and the authors' outlook, with
  forward-looking claims clearly attributed.
- **文末原文来源** — use an arXiv bookmark when an arXiv page exists; otherwise
  link an available DOI or official source. Do not invent a public link for a
  local-only PDF.

If the source genuinely lacks a subsection (e.g. no separate training strategy), fold
it in honestly rather than padding. Allocate detail according to the source's
contribution and evidence density, not an equal word count per heading.

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
