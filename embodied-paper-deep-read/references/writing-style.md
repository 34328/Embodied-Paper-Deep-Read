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
  `**条件一：…。** <长段>` / `**阶段二：…。** <长段,里面还套第二个加粗>`.
  Three or more of these in a row is the tell-tale AI rhythm, and each "paragraph" is
  usually a mini-section masquerading as prose.
- **Failure B — undifferentiated wall.** A single 300–400 字 paragraph that fuses setup +
  mechanism + numbers + qualitative analysis + caveat, with no visual structure at all.
  Common in 实验结果 / 讨论 sections.

When a block contains independent, comparable items (multiple findings, criteria, or failure
modes), use a framing sentence followed by a list or table. Each item should be a complete
explanation. Keep flowing paragraphs for a dependent sequence, derivation, causal argument, or
synthesis; a process diagram may help when the sequence has branches.

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
- **Parallel, comparable items** → **list or table**, with one framing sentence and enough
  detail to distinguish the items.
- **Dependent steps, derivation, or one causal claim** → **prose or a process diagram**, keeping
  the necessary reasoning and evidence together.
- Choose the form that makes the relationship visible; do not convert a method's dependent
  steps into disconnected bullets merely because they can be numbered.

### Still true: don't over-fragment

- Use real paragraphs that connect ideas with reasoning for continuous argument; don't shatter
  a single causal chain into disconnected one-line bullets.
- Never bury a display equation inside a prose paragraph; introduce it, show it centered on its
  own line, then explain it below.
- A list item must be a **complete explanatory unit** (what it is / how it works / why it
  matters), never a keyword fragment. Bullet-shrapnel (标题式碎词) is as wrong as the walls.
- The top **精华提炼** callout gives a brief overall judgment and a few nonredundant takeaways
  drawn from the source's actual contributions; do not pad it to a fixed count.

### Analytical self-check across source types

For each substantive section, make the answer to the relevant questions clear: What claim or
technical choice does this section explain? How does the mechanism, data process, or evaluation
protocol work? What evidence and conditions support the result? What distinguishes it from a
meaningful alternative, and what limits that comparison? These are review questions, not a
required paragraph order or a demand to fill fields the source does not report. Make the point
clear early, but let essential definitions or setup come first when needed.

Do not follow the source's paragraph order merely to restate it in Chinese. When the source
compares alternatives, explain the concrete difference and evidence; when it presents one
design, trace its inputs, operations, outputs, and consequences; when it contributes data or a
benchmark, explain the construction or protocol and what its tests can establish. Attribute
original results, cited studies, and this reading's inferences separately. If several
comparable items are buried in consecutive paragraphs, expose the comparison with complete
bullets or a table, while preserving the causal explanation in prose.

If an important method or pipeline appears in several parts of the note, give the reader one
place to follow its purpose, state or data representation, main operations, training or
construction, evidence, and material cost where the source reports them. Later references
should add a new distinction or point back to that explanation, not repeat its name and slogan.

### Open with the issue, then develop the evidence

Sections that stay as prose (问题定义、动机、综述引言) should open with a short
statement of the issue before the detailed evidence.

- **The opening should make the section's question or point clear within a short span.** Then
  develop the mechanism, evidence, and qualification in following paragraphs or structured
  blocks. Do not front-load several long setup paragraphs before revealing the section's role.
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
- Use a comparison table only when several methods/options share concise dimensions and the
  layout is easier to scan than prose or bullets. Add interpretation without repeating its rows.
- Use H2/H3 for genuine conceptual layers. Arrange paragraphs, figures, lists, and tables so
  each claim has the setup and evidence needed to understand it; avoid a fixed block order.
- Do not shorten a section merely because it looks long. Split and reorganize it when the
  information is valuable; delete only repetition, filler, or unsupported claims.
- After rewriting, cross-check against the evidence note/source section and confirm that every
  material number, condition, failure case, and conclusion still appears.

## Anchors / sub-titles: short and sharp

- Section anchors should be crisp nouns: "问题定义"、"相关工作"、"因子化表示" —
  **not** conversational questions like "论文在做什么、为何这样做".
- Prefer the terminology the field actually uses.
- Use a real H3 when a subtopic needs sustained treatment and helps navigation. Do not turn
  every bold lead into a heading or simulate a series of subsections with repeated bold leads.
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

For a dense Related Work section, group by the source's meaningful research lineages. Use H3
when a lineage needs sustained explanation, and bullets or a table when several approaches
share comparison dimensions. Keep the historical or causal explanation that connects them.

## Tone

Knowledgeable peer explaining the paper to another researcher: precise, direct, assumes
technical literacy. Avoid casual section labels, marketing adjectives ("革命性的",
"强大的"), and sweeping claims ("通往 AGI 的核心瓶颈") unless they are
explicitly attributed and supported by the source. State the task, metric,
comparison conditions, and uncertainty when reporting a result.
