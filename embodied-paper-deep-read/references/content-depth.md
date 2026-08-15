# Content depth (phase 3)

> Source rule: skill_notes §八 + §七. A deep-read must be concrete. Vague method
> summaries are the failure mode this file prevents.

## Methods need real dimensions

- Give the **input/output dimension and format** of each module, summarized in a **table**
  — not "编码器提取特征" hand-waving. E.g. a table with columns 模块 / 输入 / 输出 /
  说明, listing patch features, token dims, head outputs.
- Name concrete hyperparameters when the paper gives them: number of blocks, heads,
  hidden dim, MLP ratio, ViT variant, etc.

## Put a pipeline before the module table

When the method has at least three dependent stages or a meaningful output/training branch,
place one concise pipeline **after the architecture explanation and immediately before the
module input/output table**. On Feishu use a Mermaid whiteboard; on Markdown use a fenced
Mermaid block.

- Show the main data path, module boundaries, output branches, and training-only branches.
- Keep node labels short; leave tensor details and hyperparameters to the table below.
- Complement rather than redraw the paper's architecture figure: the original figure preserves
  visual design, while the pipeline makes execution order and branching easy to scan.
- Omit the pipeline for a one- or two-stage method where prose is already clearer.
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

## Dataset table: size / ratio / purpose

For training data, give a table with **size, mixing ratio, and purpose/stage** — sourced
from the paper's appendix.

- If the paper only does single-stage finetuning, say so honestly ("监督用途") — **do not
  invent** pre-training / post-training stages that aren't there.
- Distinguish geometry-only vs. motion-annotated datasets if the paper does.

## Experiment tables: faithful but selective

- Reproduce a complete table only when it is central and reasonably sized. Otherwise keep
  the paper's method, strongest/representative baselines, datasets, metrics, and rows needed
  for the claim. State explicitly which secondary rows or columns were omitted.
- Do not duplicate the same numbers in prose, a recreated table, and a figure. Choose the
  representation that makes the comparison clearest.
- Bold / highlight the paper's method (winning row) — see `beautify.md`.
