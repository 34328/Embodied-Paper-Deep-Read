# Publisher: Feishu (Lark)

> Backend for phase 4. Feishu is the default target. This file is the only place
> Feishu-specific mechanics live — keep them out of phases 1–3.

## Publisher contract (applies to any backend)

A publisher consumes the two backend-agnostic artifacts from phases 1–3:
1. **document body** — the structured deep-read text (chapter skeleton, tables, callouts).
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

## First-time setup — you run it, not the user

The README tells the user to ask you to set Feishu up. So when `lark-cli` is missing or
unauthorized, **drive the setup yourself**; do not paste a list of commands and tell the user
to run them. Only two things genuinely need the user: approving an install, and the browser
authorization itself.

Check state first — skip any step that already passes:

```bash
command -v lark-cli && lark-cli auth status --json --verify
```

1. **Install** if `lark-cli` is absent: `npx @larksuite/cli@latest install` (needs Node.js 16+;
   if Node is missing, tell the user how to install it for their OS and stop there).
2. **Configure** if there is no app yet: `lark-cli config init --new`. This **blocks until the
   user finishes in the browser** — run it in the background and read the verification URL from
   its output. Inside an agent workspace (`OPENCLAW_HOME`/`HERMES_HOME` set) it refuses by
   design; use `lark-cli config bind` to bind the agent's existing app instead of creating a
   parallel one.
3. **Authorize** the minimum Docs/Drive scopes:
   `lark-cli auth login --domain docs --domain drive`. This also blocks on the browser. If your
   harness only delivers messages at end of turn, use `--no-wait --json`, give the user the
   verification URL (or `lark-cli auth qrcode`) as your final message, end the turn, then
   finish with `--device-code <code>` after they confirm.
4. **Verify** with `lark-cli auth status --json --verify` before publishing anything.

Request the minimum scopes needed to publish. Never ask the user to paste an app secret into
chat; `config init` takes it via `--app-secret-stdin`.

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
   - New doc: `lark-cli docs +create --parent-position my_library --content '<title>…</title>…'`
     (XML with `seq`/`seq-level` auto-numbering per `references/doc-structure.md`).
   - Default landing location is the user's **我的文档库 / My Library**. Do not create a new
     Feishu document without `--parent-position my_library` unless the user explicitly provides
     another folder/wiki parent.
   - If authentication or required scopes are missing, stop and give the user the official
     setup command. Do not silently publish elsewhere.
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
   - Always pass `--align center`. All tables must use the current document's actual usable
     width and centered cell paragraphs. Derive width from a fetched full-width/auto-layout
     table instead of hardcoding a constant. All display formulas must be standalone centered
     paragraphs.

4. **Verify once after all moves.** Re-fetch the outline and affected sections. Confirm that:
   - every numbered H1/H2/H3 has `seq` + `seq-level="auto"` in a targeted `--detail full` fetch;
   - heading text has no hand-written numeric prefix (`2 方法`, `2.1 网络架构`, etc.);
   - every table spans the full usable width and every cell paragraph is centered;
   - every image/whiteboard is centered, and every long/loss formula is a standalone
     `align="center"` paragraph;
   - every figure landed under the right heading with its
   caption. Inserted images render as **`<img … name=… caption=…>`** — grep for `<img`,
   NOT `<image>`, or you'll wrongly conclude zero images.

## Block ID lifecycle (don't reuse stale IDs)

After `overwrite` / `block_replace` / `block_delete`, the affected old block IDs are
dead — re-fetch with `with-ids` before referencing them. After insert/copy, the new IDs
only exist post-fetch. See lark-doc's "Block ID 生命周期" section.

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
