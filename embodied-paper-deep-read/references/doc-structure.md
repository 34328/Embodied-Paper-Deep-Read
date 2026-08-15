# Document structure (phase 3)

> Source rule: skill_notes §二 + §三. Fixed skeleton, Feishu-native auto-numbering.

## Chapter skeleton (H1 = chapter)

Adapt sub-sections to the paper, but keep this spine:

- **论文基本信息** — *front matter, unnumbered.* A table: 标题 / 作者 / 机构 / 发布
  (arXiv id + date) / 项目主页. Immediately followed by the **精华提炼** callout
  (see `beautify.md`).
- **1 研究背景与动机**
  - 1.1 问题定义 — what problem, why it matters, why now.
  - 1.2 相关工作 — cover the authors' main method families and meaningful baselines; group
    similar works rather than enumerating the bibliography.
  - 1.3 核心贡献 — the paper's stated contributions, in your words.
- **2 方法**
  - 2.1 训练数据集 — size / ratio / purpose table (see `content-depth.md`).
  - 2.2 网络架构 — encoder / backbone / heads, with input-output dimension tables.
  - 2.3 训练策略 — losses, schedule, init, multimodal dropout, etc.
  - Sub-titles follow the paper. **"核心创新" is NOT a mandatory subsection** — only some
    papers have a genuine standout innovation; if so, surface it as a ⭐ callout folded
    into the relevant section, not as its own heading. If there's no real innovation,
    don't manufacture one.
- **3 实验结果** — one sub-section per result theme. Reproduce only the tables needed to
  support the main claims; combine tightly related ablations.
- **4 局限性** — the paper's stated limitations (and honest ones you observed).
- **5 结论与意义** — what it unifies / enables; the authors' outlook.
- **文末:arXiv 原文书签卡** — a bookmark card linking the arXiv page.

If the paper genuinely lacks a section (e.g. no separate training-strategy), fold it in
honestly rather than padding.

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
- Front matter (论文基本信息) and the end bookmark card are **unnumbered** — plain `<h1>`
  with no `seq`.

Before publishing, inspect the generated XML: numbered H1/H2/H3 blocks must have both `seq` and
`seq-level="auto"`, and their inner text must begin directly with the title. After publishing,
fetch the outline and representative headings with `--detail full`; reject any numbered title
whose text still begins with a pattern such as `2 方法` or `2.1 网络架构`.

For a non-Feishu backend (local md), numbering is literal Markdown `#`/`##` and you may
write "1"、"1.1" as text — see `publishers/local-md.md`. The auto-numbering rule is a
Feishu concern; keep the *structure* identical across backends.
