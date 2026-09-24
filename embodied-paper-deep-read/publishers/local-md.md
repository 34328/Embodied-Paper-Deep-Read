# Publisher: Local Markdown

> Backend for phase 4. This publisher writes without a Feishu connection when the user
> requests local output or Feishu is unavailable. The deep-read itself still requires MinerU
> to parse the PDF body. The normal default remains the user's own Feishu document.

## Publisher contract

Same as any backend (see `feishu.md` top): consume the **document body** + **figure
manifest**, emit a rendered doc with figures at their anchors and your Chinese captions.

## Output

Write a single `.md` file plus a figures folder inside the paper folder required by `SKILL.md`:

```
<paper-folder>/
  <slug>.md
  images/
    fig1_overview.png
    fig3_arch.png
    …
```

## Mapping the structure to Markdown

- **Headings**: literal Markdown. Since Markdown has no Feishu-native auto-numbering, you
  may write the numbers as text — `# 1 研究背景与动机`, `## 1.1 问题定义`. Keep the exact
  same skeleton as `references/doc-structure.md`; only the numbering mechanism differs.
- **精华提炼 / 核心创新 / 术语与符号 callouts** → blockquotes with the emoji prefix, drop the
  background color:
  ```
  > 💡 **精华提炼**
  >
  > 一句话说明论文的核心结论。
  >
  > - **核心方法：** …
  > - **规模 / 数据：** …
  > - **主要结果：** …
  > - **迁移价值：** …
  ```
- **Tables** → GitHub-flavored Markdown tables. Bold the paper's own method when it is the
  comparison focus, or the actual winning row when that is the claim; do not equate the two.
  Center every column via `:---:`.
- **Math / tensor dims** → `$…$` inline LaTeX instead of `<latex>`:
  `$\mathbb{R}^{1024 \times H/14 \times W/14}$`.
- **Mermaid pipeline** → a fenced ` ```mermaid ` block (renders on GitHub/many viewers).

## Figures

For each `<!-- FIG file | anchor | w | cap -->` manifest line, resolve `file` relative to
`<paper-folder>/figures.manifest`. Require it to point to the final high-resolution render or
PDF crop, copy that file into `<paper-folder>/images/`, and place it at its anchor as:

```
<p align="center"><img src="images/fig1_overview.png" width="720"></p>

<p align="center"><sub>图 1：…你的中文图注…</sub></p>
```

- Use the centered HTML form above for every figure so alignment is deterministic.
- The `<sub>` line is your Chinese caption (small font). Never copy the paper's English
  caption.
- Unlike Feishu, nothing wipes these — but keep the manifest anyway so the doc is
  portable to another backend later.

## Source reference

At the end, link to the actual source when a public URL exists. Use the paper's own arXiv ID,
DOI, publisher page, or official project page; never copy a sample ID. For example:
```
---
📄 **原文**：[arXiv:<actual-id>](https://arxiv.org/abs/<actual-id>)
```
If the user supplied a PDF without a public URL, link to the copied file in the same paper
folder as `📄 **原文**：[PDF](<slug>.pdf)` rather than inventing an arXiv link.
