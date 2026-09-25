# Publisher: Feishu (Lark)

> Backend for phase 4. Feishu is the default target. This file is the only place
> Feishu-specific mechanics live — keep them out of phases 1–3.

## Publisher contract (applies to any backend)

A publisher consumes the two backend-agnostic artifacts from phases 1–3:
1. **document body** — the structured deep-read text (chapter skeleton, tables, callouts),
   including page or figure/table locators for pivotal technical and quantitative claims.
2. **figure manifest** — the `<!-- FIG file | anchor | w | cap -->` lines.

and produces a rendered document with figures placed at their anchors and your Chinese
captions attached. To add a new backend (Notion, etc.), write a sibling file that
fulfills this contract; nothing in phases 1–3 should change.

## Feishu specifics

**Environment**
- Require the official `@larksuite/cli`; do not assume a platform-specific installation path.
- Publish as the user so the document lands in the user's own Feishu library.
- `@file` arguments accept **cwd-relative paths only** (absolute → "unsafe file path").
  `cd` into the figure dir, or pass relative `./fig.png`.

## Setup and readiness

Before a Feishu publish, detect the current state and report the paper-reading and publishing
readiness separately. Feishu is ready only when `lark-cli` runs, `lark-doc` and `lark-shared`
guidance is available, and `lark-cli auth status --json --verify` succeeds. Skip setup only
when all three checks pass. Otherwise keep any working CLI and repair each missing component:
install the required CLI Skill if guidance is missing, or complete only app setup/login if
authorization is missing. If the CLI is absent or cannot start, follow the [official Feishu CLI
guide](https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md)
in the current Agent; do not ask the user to send a second prompt or use a project-specific
installer.

The [Feishu CLI page](https://www.feishu.cn/feishu-cli) is the user-facing entry point. The
official guide requires Node.js/npm/npx and installs both `lark-cli` and its required CLI Skill.
For its `npx skills add` step, preserve the official arguments and add
`--global --agent <current-agent-id>` (for example, `codex` or `claude-code`) so the companion
Skill is installed only in the current Agent's user-level directory, not project scope or every
Agent.
If Node.js is missing, use the official [Node.js download page](https://nodejs.org/en/download/)
and the operating system's supported installation method. Go and Python are only needed for
source builds. App setup and login require the user to complete browser authorization; request
that interaction only when the official flow reaches it. Verify with
`lark-cli auth status --json --verify`.

The expected states are:

- `lark-cli`, both guidance Skills, and verified user auth present: ready; skip setup.
- `lark-cli` present but guidance missing: keep the CLI and install the required CLI Skill.
- `lark-cli` present but auth unverified: keep the CLI and complete app/login setup.
- Both guidance and auth missing: report and resolve both; do not stop after the first finding.
- `lark-cli` missing: install it and its required CLI Skill from the official guide.
- Node.js/npm/npx missing: install the runtime first, then resume the official CLI steps.

Read the version-matched `lark-doc` and `lark-shared` guidance before publishing:

```bash
lark-cli skills read lark-doc
lark-cli skills read lark-shared
```

For this publisher, keep the requested Feishu permissions to Docs and Drive. If the official
login flow offers broader recommended scopes, choose only the scopes needed for document
creation and image upload.

- **`config init` and `auth login` both block on a browser.** Run them in the background and
  read the verification URL out of their output. If your harness only delivers messages at end
  of turn, use `auth login --no-wait --json`, send the user the URL (or `lark-cli auth qrcode`)
  as your final message, end the turn, and finish with `--device-code <code>` afterwards.
- **Inside an agent workspace** (`OPENCLAW_HOME`/`HERMES_HOME` set) `config init` refuses by
  design. Use `lark-cli config bind` to bind the agent's existing app rather than creating a
  parallel one; `--force-init` only if the user explicitly wants a separate app.
- **Never take an app secret through chat.** `config init` reads it via `--app-secret-stdin`.

If the user asked for local Markdown, Feishu setup is not required. Otherwise, complete the
official setup or stop at the specific user action that remains (usually Node.js installation
permission or browser authorization); state the exact missing item and resume once it is ready.

**MUST read the version-matched embedded skill before writing** — do not rely on this
file for exact command flags, they can change:
```
lark-cli skills read lark-doc
```
and the references it names: `references/lark-doc-fetch.md`,
`references/lark-doc-media-insert.md` (or `+media-insert --help`),
`references/lark-doc-update.md`. This skill's job is the *workflow*; lark-doc is the
*command reference*. `lark-cli --help` and each subcommand's `--help` carry their own
agent-driving notes; prefer them over this file when they disagree.

## Publish workflow

1. **Create / overwrite the text body first, figures second.**
   - Save the complete XML body as `<paper-folder>/<slug>_draft.xml`. Replace the path
     placeholders with their actual values, then run
     `python3 "<skill-dir>/scripts/check_text_density.py" --threshold 220 "<paper-folder>/<slug>_draft.xml"`
     and review each reported block with `references/writing-style.md` and
     `references/beautify.md`.
     Restructure unrelated or parallel content before publishing; preserve all technical claims,
     evidence, citations, and caveats. Publish the exact reviewed XML.
   - New doc: `lark-cli docs +create --parent-position my_library --content '<title>…</title>…'`
     (XML with `seq`/`seq-level` auto-numbering per `references/doc-structure.md`).
   - Default landing location is the user's **我的文档库 / My Library**. Do not create a new
     Feishu document without `--parent-position my_library` unless the user explicitly provides
     another folder/wiki parent.
   - If authentication or required scopes are missing, follow "Setup and readiness" above: run
     the official setup steps and start the browser authorization for the user. Continue after
     authorization succeeds. If setup cannot be completed, state the exact failed step. When
     Feishu was only the default destination, use local Markdown; when the user explicitly
     requested Feishu, stop without publishing elsewhere.
   - Follow the source-reference rule in `references/doc-structure.md`. For a PDF without an
     arXiv ID, use an available DOI, publisher, or official project link. If no accessible
     public URL exists, identify the source PDF by title or filename without inventing a link
     or exposing the user's local filesystem path in Feishu.
   - Existing doc, full rewrite: `docs +update --command overwrite`.
   - ⚠️ **`overwrite` WIPES every already-inserted `<img>`.** (Mermaid whiteboards
     survive; raster figures do not.) So always (re)insert figures *after* any text
     overwrite — never assume inserted images are durable. This is exactly why the
     figure manifest exists.

2. **Resolve all anchors in one pass.** Fetch the outline once, then fetch only sections whose
   descendants are needed. Build one anchor→block-id map before inserting figures:
   ```
   lark-cli docs +fetch --doc <id> --scope outline --max-depth 3 --detail with-ids
   lark-cli docs +fetch --doc <id> --scope section --start-block-id <hid> --detail with-ids
   ```
   Note: block IDs come from **`--detail with-ids`**, NOT `--scope with-ids` (there is no
   such scope value; scopes are full/outline/range/keyword/section). Map each manifest
   anchor description ("after-table1", "after-mermaid-whiteboard") to the real block ID.

   Do not run a full-document fetch separately for every figure.

3. **Insert each figure, then move it using the saved map.** `media-insert` appends to the
   END of the doc and returns a new block id; then reposition:
   ```
   cd <figure-dir>
   lark-cli docs +media-insert --doc <id> --file ./fig1_overview.png \
       --align center --width 720 --caption "图 1：…你的中文图注…"
   # -> prints progress lines; grep the returned block_id (don't pipe to json.load)
   lark-cli docs +update --doc <id> --command block_move_after \
       --block-id <anchor_block_id> --src-block-ids <img_block_id>
   ```
   - `--width` alone auto-computes height for PNG/JPEG/GIF.
   - `--from-clipboard` is an alternative when the image is already on the clipboard;
     `--file` for on-disk crops.
   - media-insert prints progress lines to stdout — **grep for the block id**, don't feed
     the stream to `json.load`.
   - Always pass `--align center` for figures. Give tables a full-width appearance; center
     headers and compact values, but left-align explanatory cells that wrap across lines.
     Derive the usable width from a fetched full-width/auto-layout table when one exists;
     otherwise use stable proportional column widths as in `references/beautify.md`.
     All display formulas must be standalone centered paragraphs.

4. **Verify once after all moves.** Re-fetch the outline and affected sections. Use
   `--detail full` when checking colors, widths, alignment, or other styles: the default
   simple fetch omits these attributes. Confirm that:
   - every numbered H1/H2/H3 has `seq` + `seq-level="auto"` in a targeted `--detail full` fetch;
   - heading text has no hand-written numeric prefix (`2 方法`, `2.1 网络架构`, etc.);
   - the five numbered H1 chapters have exactly four native `<hr/>` separators, only between
     chapters 1–2, 2–3, 3–4, and 4–5; there are none within a chapter or around front matter
     and the source section;
   - every table spans the full usable width, with readable column widths and alignment
     appropriate to cell content;
   - every image/whiteboard is centered, and every long/loss formula is a standalone
     `align="center"` paragraph;
   - after media placement, save one full XML fetch locally and run the density checker on its
     JSON response, which extracts `data.document.content` without loading the whole body into
     the working context. Replace `<id>` and path placeholders with the actual document ID and
     paths:
     ```bash
     lark-cli docs +fetch --doc "<id>" --doc-format xml --detail full --format json \
         > "<paper-folder>/<slug>_published.json"
     python3 "<skill-dir>/scripts/check_text_density.py" --threshold 220 \
         "<paper-folder>/<slug>_published.json"
     ```
     Compare every flagged block with the approved draft. If Feishu merged distinct paragraphs,
     correct the body and verify again; a coherent long argument may remain after review.
     An all-clear from this checker is only a block-length result.
   - every figure landed under the right heading with its
     caption. Inserted images render as **`<img … name=… caption=…>`** — grep for `<img`,
     NOT `<image>`, or you'll wrongly conclude zero images.

   Finally, scan the rendered Feishu document H2 by H2 for a visible conclusion and readable
   parallel distinctions. Inspect the longest table and a dense figure at their displayed sizes:
   explanatory cells and figure labels must be legible, not merely high-resolution on disk.
   Fix text walls or cramped tables in the source draft, then republish text and reinsert figures
   as required by step 1. If the rendered page is inaccessible, inspect an available local
   preview and state that Feishu visual verification remains unconfirmed. XML structure and the
   density checker cannot establish visual readability on their own.

## Block ID lifecycle (don't reuse stale IDs)

After `overwrite` / `block_replace` / `block_delete`, the affected old block IDs are
dead — re-fetch with `with-ids` before referencing them. `media-insert` returns its new block
ID for the immediate move in step 3; if that output does not provide a usable ID, fetch the
affected section before moving it. See lark-doc's "Block ID 生命周期" section.

For a long publish, keep a local `publish-state.json` containing the document ID, current
text-revision marker, resolved anchor map, and successfully inserted figure filenames/block
IDs. Update it after every successful move. On resume, fetch the affected sections once,
confirm the recorded images still exist, and continue with the missing figures. Discard the
saved block IDs whenever the text body is overwritten.

## Keep the manifest authoritative

Because overwrite wipes images, the manifest (in the doc body as `<!-- FIG … -->`
comments, and/or the local source file) is the durable record of figure placement. Keep its
anchors descriptive and stable. Store current-revision block IDs only in `publish-state.json`;
never make ephemeral block IDs the durable manifest contract.
