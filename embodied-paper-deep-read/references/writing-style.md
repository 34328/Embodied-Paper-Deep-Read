# Writing style (phase 3)

> Source rule: skill_notes §四. This is what separates a real deep-read from an
> AI-generated summary. Violating these makes the document read as machine-written.

## Ban AI-tone tells

- **No disclaimer / meta-narration.** Never write "（以下均以论文原文所述为准）",
  "本文将介绍…", "综上所述", "值得注意的是" as filler. Just state the content.
- **No hedging boilerplate** wrapping every claim.
- Don't announce structure ("接下来我们分三点讨论"); let the headings do that.

## The two failure modes, and the rule that prevents both

Deep-read bodies fail in two opposite ways. Both are common; you must avoid both.

- **Failure A — bold-lead wall.** A run of paragraphs each opening with a bold label:
  `**鸿沟一:…。** <150 字长段>` / `**Phase 1——冻结 VLM。** <长段,里面还套第二个加粗>`.
  Three or more of these in a row is the tell-tale AI rhythm, and each "paragraph" is
  usually a mini-section masquerading as prose.
- **Failure B — undifferentiated wall.** A single 300–400 字 paragraph that fuses setup +
  mechanism + numbers + qualitative analysis + caveat, with no visual structure at all.
  Common in 实验结果 / 讨论 sections.

**The fix for both is the same move:** when a block of text contains a set of parallel or
sequenced items (multiple gaps, multiple stages, multiple findings, multiple failure modes),
lead with **one framing sentence**, then break the items into a **list** — each item a
complete explanatory bullet (可长可短). Reserve flowing multi-paragraph prose for genuinely
*continuous* argument (motivation, a single causal chain, synthesis), not for enumerations.

### Hard rule (not a preference)

1. **Never place 3+ bold-lead paragraphs in a row.** The moment you have three parallel items
   each wanting a bold label, that is a **list**, not three paragraphs. Convert it:
   `<p>` framing sentence + `<ul><li><b>标签:</b> 完整解释…</li>…</ul>`.
2. **Never let one paragraph carry more than one of** {setup, mechanism, numeric results,
   qualitative failure analysis, caveat}. If it does, split — and move the parallel part into
   a list or table.
3. **Never nest a second `<b>…。</b>` lead inside a bold-lead paragraph** (e.g. a bold "Phase 1"
   paragraph whose body then bolds "静态路由"). Put the bold label on its own short line, then
   explain in following short paragraphs — or make the whole thing a list.

### Prose-vs-points decision test

Before writing any block, ask: *are these items parallel/enumerable, or is this one continuous
argument?*
- **Parallel / sequenced** (三条鸿沟、两个 phase、四类 VQA、一组失败模式、三点结论) → **list**,
  one framing sentence above it. This is the default for "结果 / 讨论 / 局限" content.
- **Continuous** (为什么现有方法不行 → 所以本文这样做;一条因果链;一段综述) → **prose**,
  2–4 sentences per paragraph, connected with 因为 / 相比之下 / 这带来的问题是.
- When in doubt on enumerable content, prefer the list. The recurring failure is always too
  much undifferentiated prose, never too many well-formed lists.

### Worked example (this is the exact mistake to avoid)

BAD — **bold-lead wall** (what a lazy pass produces):
```
<p><b>鸿沟一：模态与数据规模。</b>视觉编码器……（150 字）。</p>
<p><b>鸿沟二：预训练分布。</b>如图 1……（120 字）。</p>
<p><b>鸿沟三：训练目标。</b>LLM/VLM……（160 字）。</p>
```
GOOD — **framing sentence + list** (same content, real structure):
```
<p>作者把用当前 VLM 学动作的困难，归纳为三条根本性的鸿沟：</p>
<ul>
  <li><b>模态与数据规模。</b>视觉特征可经 CLIP 与文本对齐，而动作是 3D+时间上的连续信号，
      缺乏长期表征研究与海量数据驱动……</li>
  <li><b>预训练分布。</b>具身视觉是第一人称、鱼眼、自遮挡，与互联网图像差异大，VLM 难覆盖
      具身 VQA……</li>
  <li><b>训练目标。</b>next-token 似然 vs 连续高频动作的生成目标，直接嫁接会灾难性退化……</li>
</ul>
```
The list keeps every technical claim, but the reader now sees "three gaps" at a glance instead
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

### Open tight — even prose sections must not front-load a wall

Sections that legitimately stay as prose (问题定义、动机、综述引言) still fail if they open with a
dense multi-sentence pile. A reader landing on a heading should meet a **short hook**, not a
paragraph they must decode.

- **First paragraph = 1–2 sentences that state the point.** Set up the tension, don't
  exhaustively justify it yet. Details come in the following paragraphs.
- **Squeeze filler from every setup paragraph.** Cut throat-clearing ("之所以…是因为…", long
  appositive clauses, restated context). Keep every technical term and named method; delete the
  connective padding around them. A background paragraph can usually lose ~⅓ of its words with
  zero information loss.
- Prefer active, compact phrasing: "VLM 已能 X，却仍 Y" beats "VLM 正在快速进步：……能够 X……
  但它们本质上仍是 Y 的——".

BAD — front-loaded wall (three long setup paragraphs, each ~150 字, before any payoff):
```
<p>语言与视觉的基座模型正在快速进步：Gemini 2.5、GPT-5 这类全能模型能够联合处理文本与视觉，
并保持审慎的推理能力。但它们本质上仍是“离身”的——既不能……，也无法……。因此……。</p>
<p>问题的根子在于数据。文本和 2D 视觉之所以较早获得……，是因为互联网提供了海量、分布丰富、
易获取的……。而在具身场景中，……。于是主流思路转向……。</p>
```
GOOD — short hook, then tightened setup (same facts, ~⅓ fewer words, colon leads into the list):
```
<p>Gemini 2.5、GPT-5 等 VLM 已能联合处理文本与视觉、保持审慎推理，却仍是“离身”的：不能从物理
交互中自我修正，也无法生成可执行动作。动作的理解与生成因此成为具身空间通往 AGI 的核心瓶颈。</p>
<p>根源在数据。……主流思路因此转向把强 VLM 主干迁移到动作空间（OpenVLA、π0）。</p>
<p>但迁移并不轻松：……作者把困难归结为三条根本鸿沟：</p>
```

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
technical literacy, no marketing adjectives ("革命性的", "强大的") unless quoting the paper.
