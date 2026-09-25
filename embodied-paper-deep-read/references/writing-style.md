# Writing style (phase 3)

> Write for a technically literate reader, with clear structure and source-faithful
> claims rather than formulaic summary language.

## Evidence-led tone

- Remove filler such as "本文将介绍…", "综上所述", and "值得注意的是" when it
  adds no information. State the substantive claim directly.
- Avoid formulaic hedging, but retain uncertainty, scope, sample size, and causal
  limits that matter to the evidence. Mark a reading-based inference as such rather
  than writing it as an author claim.
- Don't announce structure ("接下来我们分三点讨论"); let the headings do that.

## Two common layout failures

Dense notes often develop one of two layout problems:

- **Failure A — bold-lead wall.** A run of paragraphs each opening with a bold label:
  `**鸿沟一:…。** <150 字长段>` / `**Phase 1——冻结 VLM。** <长段,里面还套第二个加粗>`.
  Three or more of these in a row is the tell-tale AI rhythm, and each "paragraph" is
  usually a mini-section masquerading as prose.
- **Failure B — undifferentiated wall.** A single 300–400 字 paragraph that fuses setup +
  mechanism + numbers + qualitative analysis + caveat, with no visual structure at all.
  Common in 实验结果 / 讨论 sections.

When a block contains parallel or sequenced items (multiple gaps, stages, findings,
or failure modes), use a framing sentence followed by a list. Each item should be a
complete explanation. Keep flowing paragraphs for a continuous argument such as
motivation, a causal chain, or synthesis.

### Hard rules for paragraph structure

1. **Never place three or more bold-lead paragraphs in a row.** If they enumerate
   parallel items, convert them to a framing sentence plus a list. If they are distinct
   arguments, use genuine subheadings or ordinary paragraphs without repeated bold leads.
   For parallel items, use:
   `<p>` framing sentence + `<ul><li><b>标签:</b> 完整解释…</li>…</ul>`.
2. Give each paragraph one coherent argument. A claim, its decisive number, citation,
   and directly related caveat may stay together. Split a paragraph that piles setup,
   mechanism, multiple results, failure analysis, and limitations into one block.
3. **Never nest a second bold lead inside a bold-lead paragraph.** Use a real subheading
   or list for subtopics; use ordinary emphasis only where it clarifies the same point.
4. Continuous prose usually works best at 2–4 sentences per paragraph. Use the
   paragraph-density review in `beautify.md` for long blocks; do not split a continuous
   causal argument into disconnected fragments just to meet a character count.

### Prose-vs-points decision test

Before writing any block, ask: *are these items parallel/enumerable, or is this one continuous
argument?*
- **Parallel / sequenced** (三条鸿沟、两个 phase、四类 VQA、一组失败模式、三点结论) → **list**,
  one framing sentence above it. This is the default for "结果 / 讨论 / 局限" content.
- **Continuous** (为什么现有方法不行 → 所以本文这样做;一条因果链) → **prose**,
  with the reasoning and necessary evidence kept together, usually 2–4 sentences per paragraph.
- When it is unclear whether content is enumerable, prefer a list if the items have distinct
  conditions, mechanisms, or outcomes. Keep prose when the reader needs one uninterrupted
  causal explanation.

### Worked example (this is the exact mistake to avoid)

BAD — **bold-lead wall** (what a lazy pass produces):
```
<p><b>鸿沟一：模态与数据规模。</b>视觉编码器……（150 字）。</p>
<p><b>鸿沟二：预训练分布。</b>如图 1……（120 字）。</p>
<p><b>鸿沟三：训练目标。</b>LLM/VLM……（160 字）。</p>
```
GOOD — **framing sentence + list** (same content, real structure):
```
<p>作者把视觉语言模型用于连续动作预测时的难点归纳为三个方面：</p>
<ul>
  <li><b>模态与数据规模。</b>视觉特征可经 CLIP 与文本对齐，而动作是 3D+时间上的连续信号，
      缺乏长期表征研究与海量数据驱动……</li>
  <li><b>预训练分布。</b>具身视觉是第一人称、鱼眼、自遮挡，与互联网图像差异大，VLM 难覆盖
      具身 VQA……</li>
  <li><b>训练目标。</b>next-token 似然与连续动作生成的优化目标不同；性能影响须由原文实验说明。</li>
</ul>
```
The list keeps every technical claim, but the reader now sees the three aspects at a glance instead
of decoding three lookalike paragraphs. Apply the same conversion to sequential stages
(Inspiration / Integration phases), enumerated findings (每个 5.2.x 小节的结论), and
failure-mode inventories.

### Still true: don't over-fragment

- Use real paragraphs that connect ideas with reasoning for continuous argument; don't shatter
  a single causal chain into disconnected one-line bullets.
- Never bury a display equation inside a prose paragraph; introduce it, show it centered on its
  own line, then explain it below.
- A list item must be a **complete explanatory unit** (what it is / how it works / why it
  matters), never a keyword fragment. Bullet-shrapnel (标题式碎词) is as wrong as the walls.
- The top **精华提炼** callout follows the same list discipline: one conclusion sentence + 3–5
  parallel bullets.

### Synthesis, not paragraph-by-paragraph translation

For every major H2, lead with the specific point the reader should retain, then select the
source facts needed to establish it. Do not follow the paper's paragraph order merely to
restate it in Chinese. Where the source compares approaches, give the reader the comparison:
**named example → mechanism or protocol → distinguishing tradeoff → supporting evidence or
boundary**. Close with a short inference only when the evidence warrants one, and label it as
this reading's inference rather than the authors' result.

Before accepting a section, scan its blocks: if it contains two or more families, criteria,
failure modes, or stages but only consecutive prose paragraphs, turn the parallel parts into
complete bullets or a comparison table. Keep the causal explanation that connects them in
short prose. A section made of generic category definitions without representative methods or
evidence has not yet been analyzed deeply enough.

### Open with the issue, then develop the evidence

Sections that stay as prose (问题定义、动机、综述引言) should open with a short
statement of the issue before the detailed evidence.

- **The first paragraph under a section should state its point in 1–2 sentences.** Then
  develop the mechanism, evidence, and qualification in following paragraphs or structured
  blocks. Do not front-load several long setup paragraphs before stating the section's claim.
- Paragraph length follows the argument; split a dense block at changes in idea without
  deleting distinct technical claims or necessary context. Use the character-count review in
  `beautify.md` as a warning gate, not a target for deleting content.
- Remove repeated context and unsupported qualifiers. Prefer concrete, scoped claims
  over claims that a method is "本质上" limited or that one factor is the sole "根源".

## Chinese punctuation and mixed-language typography

Default output is Chinese prose. Use Chinese punctuation in Chinese sentences: `，`、`。`、`：`、`；`、`（ ）`、`“ ”`、`《 》`.

Do not use ASCII punctuation as Chinese sentence punctuation. ASCII punctuation such as `,`、`.`、`:`、`;`、`()` is allowed only inside code, commands, URLs, file paths, XML/HTML tags, LaTeX, JSON, exact paper titles, model names, package names, and quoted source text.

For mixed Chinese-English technical prose, keep technical terms as-is but punctuate the sentence in Chinese:

- Good: `VLM 已能处理图像，但仍不能生成可执行动作。`
- Bad: `VLM 已能处理图像, but still cannot generate actions.`
- Good: `Qwen2.5-VL-3B 作为 backbone，Flow Matching 负责连续动作建模。`

Do not add decorative spaces around every English term. Add spaces only where readability or the original technical name requires it.

## Structure for comprehension, not shortening

"Concise" means **remove repetition and expose structure**, not delete learning content. Before
restructuring a dense section, inventory its technical claims, formulas, dimensions, metrics,
baselines, assumptions, caveats, causal explanations, and concrete examples. Preserve them in
the rewritten section unless they are genuinely duplicated or incorrect.

- Convert parallel facts into complete explanatory bullets: each bullet should state what the
  item is, how it works or differs, and why it matters. Do not leave keyword fragments.
- Use a comparison table when several methods/options share the same dimensions; keep the
  interpretation paragraph after the table.
- Use H2/H3 to expose genuine conceptual layers, then place paragraphs, figures, lists, and
  tables in the reader's learning order: context → evidence/mechanism → comparison → takeaway.
- Do not shorten a section merely because it looks long. Split and reorganize it when the
  information is valuable; delete only repetition, filler, or unsupported claims.
- After rewriting, cross-check against the evidence note/source section and confirm that every
  unique number, condition, failure case, and conclusion still appears.

## Anchors / sub-titles: short and sharp

- Section anchors should be crisp nouns: "问题定义"、"相关工作"、"因子化表示" —
  **not** conversational questions like "论文在做什么、为何这样做".
- Prefer the terminology the field actually uses.
- Use a real H3 when an H2 contains several genuine subtopics and each subtopic supports at
  least two paragraphs or one paragraph plus a grouped list/table. Never simulate a subsection
  with a paragraph-opening pattern such as `**三维重建。** ...` or `**动态重建。** ...`.
- Do not promote a one-sentence label into H3. In that case, keep it inside the paragraph or
  use a list label only when the surrounding items are truly parallel.
- In dense method sections, use **H3 for real modules/stages**, short paragraphs for mechanism
  and causal explanation, lists for parallel token roles/heads/losses, and at most one callout
  for the paper's genuinely central design gain. Do not repeat the same dimensions and metrics
  in prose, the pipeline, and the module table.

## Related work: cover the meaningful landscape

Follow the authors' topical grouping. Cover method families and named works that the prose
discusses substantively or that appear as meaningful experimental baselines: what they do,
their limitation, and the resulting gap. Do not turn every bibliography citation into a
mini-summary. Merge works with the same role and keep the section proportional to the paper.

For a dense Related Work section, use this hierarchy: **H3 for each research lineage → one
orientation paragraph → bullets/table grouped by technical route → optional synthesis
paragraph**. The bullets enumerate comparable method families; they do not replace the
historical or causal explanation.

## Tone

Knowledgeable peer explaining the paper to another researcher: precise, direct, assumes
technical literacy. Avoid casual section labels, marketing adjectives ("革命性的",
"强大的"), and sweeping claims ("通往 AGI 的核心瓶颈") unless they are
explicitly attributed and supported by the source. State the task, metric,
comparison conditions, and uncertainty when reporting a result.
