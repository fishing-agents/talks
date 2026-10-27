# ODP output rewrite — design

## Problem

`render/odp.py` + `render/odf/*` hand-roll a second layout/paint engine
(`estimate_text_height`, ad hoc `StyleKey`s, manual grid math) in parallel
to the CSS the HTML/PDF path uses. It drifts: confirmed defects vs the
weasyprint PDF on `examples/test_kubecon.md` —

- slide/title backgrounds missing (gradient + dark bg never applied;
  `theme/parser.py:_build_theme_dict` never extracts `--color-background`,
  so `odp.py` paints pages with `ink_rgb_hex`, the *foreground* color)
- `_parse_sheet` flattens `:root` + `[data-theme="dark"]` into one dict
  with no scoping, so light/dark values overwrite each other by rule order
- list bullets: wrong glyph, wrong (bold) weight
- table: no header/zebra distinction, solid fill on every row
- cards: no border, no padding box, flat fill only
- title-slide vertical centering, type scale, all approximate/wrong

Root cause: the ODP renderer reimplements CSS layout/paint from scratch
instead of reusing the one engine (weasyprint) slidr already trusts for
the PDF output.

## Decision

Stop re-deriving geometry and paint. Render the real HTML through
weasyprint, walk its resolved layout box tree, and read position, size,
and computed style directly from it. Spiked and confirmed on weasyprint
69.0 (pinned in `pdm.lock`): `HTML(...).render().pages[i]._page_box`,
walked via `.children`, exposes `.element` (the source DOM node),
`.position_x/_y`, `.style[...]` with resolved `background_color`,
`background_image` (incl. `LinearGradient` objects — CSS gradients on
`.layout-title`/dark sections resolve correctly through the real
cascade, confirmed against `kubecon_japan.css`), `color`,
`border_*_width/color`, `border_*_left_radius`, etc., all as RGBA
floats 0–1 / CSS px.

**Geometry uses the border box, not the content box**: raw
`.position_x/_y` is the *margin*-box origin and raw `.width/.height` is
*content*-box only (excludes padding/border) — confirmed in the
installed weasyprint 69.0 (`boxes.py`: `border_box_x()` returns
`position_x + margin_left`; `border_width()`/`border_height()` add
padding and border on top of content size). A frame rect built from the
raw fields would be offset and undersized. Use
`box.border_box_x()/border_box_y()` and
`box.border_width()/border_height()` for every `Elem.box` rect.

This is the single IR fix: the bug was always "the renderer doesn't know
the real resolved style", and weasyprint already computes it correctly
for the PDF. ODP gets the same numbers.

### Identity: `data-slidr-id`

Boxes carry `.element` (lxml node) but matching by tag/text is fragile.
`render/html.py` gets one `data-slidr-id="{id}"` attribute per `Elem` it
emits (the id already exists implicitly as object identity in the IR
list; assign a stable counter during `build_ir` and store it on `Elem.id`).
The geometry pass matches `box.element.get("data-slidr-id")` back to
`Elem.id` — never by position/text.

### Where geometry lives

Added to `Elem` in `render/ir.py`: `box: BoxGeometry | None` (new
dataclass: `x, y, w, h` in px, plus `resolved: ResolvedStyle` — flattened
`bg` (alpha-composited onto the parent's resolved bg, computed in the
adapter, not left as raw rgba), `fg`, `border_color`, `border_width`,
`border_radius`, `font_family`, `font_size_px`, `font_weight`,
`text_align`, and `bg_gradient: list[tuple[float, str]] | None` (stop
offset, hex color) when `background_image` is a `LinearGradient`).

This is one annotation pass, `render/geometry.py`, run after `build_ir`:
renders the already-built HTML string through weasyprint, walks the box
tree once per page, and fills `Elem.box` by id. HTML and PDF renderers
are untouched (they don't read `Elem.box`); ODP is the only consumer.
Private-API surface (`_page_box`, box internals) is isolated to this one
module, guarded by a test that asserts the expected attributes exist
against the pinned weasyprint version — if it breaks on an upgrade, this
module is the only place to fix.

Position and size come from the **border box** (see above) of the
**top-level block box** matching each `Elem`'s id (`<div class="card">`,
`<li>`, `<section>`) — never line/text sub-rects. Frame coordinates are
**section-relative**: subtract the containing section's border-box
`(border_box_x, border_box_y)` origin before
converting to cm, not the page box's — the box tree nests section under
`body`/`html` with a non-zero offset (`@page` margin + centering), so
page-relative coordinates would misplace every frame by that offset.

Resolved **style**, unlike position, is read from descendants inside
each Elem's subtree, by tag — not a second id scheme. Spiked on real
markup (`tr:nth-child(even)`, `th`, `.card h3`/`.card p`, `li::marker`,
inline `a`/`code`): every one of these appears as its own box with a
working `.style`, keyed by `element_tag` (`"th"`, `"li::marker"`,
`"section::before"`, etc.) and `.element` pointing at the real DOM node
— confirmed via `AbsolutePlaceholder`/`TableCellBox`/`TableRowBox` boxes
already surfacing distinct header/zebra/marker colors with zero extra
instrumentation. The adapter, after locating an Elem's anchor box by id,
walks its subtree once and buckets child styles by tag: `h3`/`p` for
card header/body color, `th`/`td`/odd-`tr`/even-`tr` for table styling,
`li`/`li::marker` for list item/bullet color. Inline run styling
(`strong`/`em`/`code`/`a`) isn't themed per-instance anywhere in the
existing theme CSS, so it's resolved **once globally** per
(tag, light/dark variant) from the first occurrence found anywhere in
the deck, not per Elem — avoids an id explosion for something the CSS
itself never varies per-instance.

**Pseudo-elements replace guesswork**: `section::before` (logo) and
`section::after` (watermark) surface as real boxes with `.element` =
the section and `.element_tag` ending `::before`/`::after` — their
resolved `position_x/y/width/height` directly replace
`_make_logo_frame`'s manual aspect-ratio/margin math; no separate logo
code path.

**Background image + gradient** (`--bg-image` cover + `--bg-overlay`,
`.layout-title`'s gradient-over-image): `background_image` returns
`(("linear-gradient", LinearGradient(...)), ("url", "file:///…png"))`
— the `url` component is already a resolved local file path, no
rendering needed to get it. This composes as two **native ODF** layers,
no rasterization, no new dependency:

1. Base: the bitmap itself as the slide/master fill
   (`draw:fill="bitmap"`, a `DrawFillImage` registered from the same
   local path via `doc.add_file`, `style:repeat="stretch"` for a
   cover-like fit).
2. Overlay: a full-slide `RectangleShape` on top, `draw:fill="gradient"`
   built from the `LinearGradient`'s stops (hue only — ODF gradient
   stops carry no alpha), paired with a genuine per-axis transparency
   gradient rather than one averaged opacity: a manually-built
   `<draw:opacity draw:name="…" draw:style="linear" draw:start="…%"
   draw:end="…%" draw:angle="…"/>` element (ODF opacity values are
   *transparency* — 0% opaque, 100% fully transparent, so invert the
   CSS stop alphas; angle is the CSS gradient angle in tenths of a
   degree, e.g. CSS `135deg` → `draw:angle="1350"`), appended to
   `office:styles` and referenced via `draw:opacity-name` on the
   overlay rect's graphic-properties — odfdo has no `Style` family for
   either `draw:gradient` or `draw:opacity` (confirmed: `Style("opacity",
   ...)` raises `ValueError: Unknown family value`), both are built as
   raw `Element.from_tag(...)` and appended directly, the same manual
   pattern `bg_gradient` already required. A flat plateau in the CSS
   stops (e.g. kubecon_japan's 0–58% at constant alpha) is approximated
   with `draw:border` on the opacity element, which holds the start
   value out before the fade begins. When only a flat `--bg-overlay`
   color sits over the image (not a gradient), the overlay is a
   solid-fill rect at a single `draw:opacity` percentage instead — the
   per-axis gradient is only needed for the gradient-over-image case.

This only runs for the themes that actually set a non-`none`
`--bg-image` (`kubecon_japan`, `ossummit_europe` today); themes with a
flat/gradient-only background (`default`, `kcd_vietnam`,
`kubecon_china`, `ossummit_korea`) skip the bitmap layer entirely and
use the cheap pure-ODF solid/gradient fill alone. No new runtime
dependency (`soffice`, `pymupdf`, or otherwise) — everything here is
native odfdo/ODF.

**Text overflow**: LibreOffice's text layout differs from Pango/weasy,
so text frames get `draw:auto-grow-height="true"` (or
`draw:fit-to-size="shrink-to-fit"` for fixed-position elements inside a
grid cell, where growing would overlap siblings) rather than trusting
the weasyprint-measured height to be exact in LibreOffice too.

### ODP renderer rewrite

Replace `render/odp.py` + `render/odf/style.py` + `render/odf/layout.py`
with:

- `render/odf/geometry.py` — the weasyprint adapter described above.
- `render/odf/styles.py` — turns a `ResolvedStyle` into (cached,
  deduplicated) odfdo `Style` objects: graphic style (fill — solid,
  `draw:fill="gradient"` from `bg_gradient` stops, or the bitmap-plus-
  overlay-rect pair for a `--bg-image` background — `draw:stroke`/
  `svg:stroke-color`
  from border, `draw:corner-radius` from radius) and paragraph/text
  style (color, family, size in pt via `px * 0.75`, weight).
- `render/odf/shapes.py` — one function per `Elem.kind` producing a
  `Frame` positioned at `Elem.box` (cm = `px / 96 * 2.54`, section-
  relative), with ODF **semantic** content built from the `Elem`'s own
  structured fields (not by stripping HTML): `text:list`/
  `text:list-item` for `list`; `table:table` appended **directly** as a
  `Frame` child for `table` — `Table(name, width=ncols, height=nrows)`
  + `t.set_value((col, row), text)` then `frame.append(t)`, no
  `draw:text-box` wrapper (a table inside a text-box is not an Impress
  table and LibreOffice drops/mangles it; `odp.py`'s existing
  `_render_table` establishes the right frame shape but **not** its
  per-cell styling call: `t.get_cell(coord)` defaults to `clone=True`
  and returns a detached copy, so the existing code's
  `cell.get_element("text:p"); p.clear(); p.append(Span(...))` silently
  never touches the real table — verified empirically: the mutation is
  visible on the cloned cell but absent from `t.get_cell(coord)`
  afterwards. The rewrite uses `t.get_cell(coord, clone=False)` (or
  `set_value(coord, value, style=cell_style)` directly) so header-bold
  and zebra-row cell styles actually apply);
  `draw:text-box` paragraphs with per-run `text:span` for inline
  bold/italic/code (reusing `Elem.inlines`, already resolved by the
  parser — the current `_build_paragraph` walker is kept for structure,
  extended to use the globally-resolved inline tag colors above), image
  frames for `image`/svg/mermaid/dot/seaborn output (unchanged — image
  embedding already worked).
- `render/odp.py` — thin orchestrator: `build_ir` → `annotate_geometry`
  → one `DrawPage` per slide, `page.master_page` background style built
  from that slide's **root section box** (not swapped-in dark-mode
  globals — the real resolved style already reflects `data-theme`).

Every odfdo call this design relies on (`DrawPage`, `Frame`,
`Style`/`set_properties`, `insert_style`, `Table`/`set_value`) has been
individually re-verified against the installed `odfdo==3.23.0` in
`slidr/.venv` (not just the 3.27.2 `references/odfdo` checkout) —
signatures match; `Frame.table_frame`/`set_table` exist only in 3.27.2
and are not used (direct `frame.append(table)` works in both and is
what the current code already does).

Deleted: `estimate_text_height`/`estimate_elem_height` (height guessing),
the old `StyleKey`/`GraphicStyleRegistry` dedup keyed on guessed values
(replaced by one keyed on `ResolvedStyle`, same dedup idea, correct
input), `_swap_elem_colors`/`_create_dark_master` (dark handling is now
just "read the resolved style of this section's box" — no separate
light/dark code path).

`theme/parser.py`'s `_build_theme_dict`/`_parse_sheet` business is no
longer used by the ODP path (geometry replaces it entirely for layout +
color). `theme/parser.py` stays only if something else still imports it
— checking current call sites is part of implementation, not this spec;
if nothing but the old ODP path calls it, delete it rather than leave
dead code.

### Non-goals

- HTML/PDF rendering: untouched.
- Slide transitions, presenter view, speaker notes UI: untouched (ODP
  speaker notes field keeps using `SlideIR.notes` as plain text, already
  correct).
- Pixel-perfect ODP↔HTML parity for things LibreOffice can't render
  (CSS animations, `clip-path`, arbitrary SVG filters) — those degrade to
  the nearest ODF primitive (e.g., mermaid/dot/seaborn already rasterize
  to image, so no gap there).

## Risks

- **Private API drift**: isolated to `render/odf/geometry.py` + one
  pinned-version assertion test. weasyprint is already an exact-pinned
  direct dependency (`pyproject.toml`), so upgrades are a deliberate,
  reviewed action, not silent.
- **Gradient fidelity in LibreOffice**: ODF `draw:gradient` supports
  linear/axial/radial but not arbitrary CSS angle+multi-stop easing;
  approximate multi-stop as a 2-stop axial gradient (first/last stop)
  if odfdo/LibreOffice chokes on N-stop — confirm in implementation via
  the visual diff harness, not guessed here.
- **Frame-per-leaf-box frame count**: one `Frame` per block-level `Elem`
  (not per line) keeps counts bounded to what the current IR already
  produces per slide (headings, paragraphs, list containers, cards,
  table, not per-table-cell frames — cells are ODF table cells, not
  frames).

## Verification

- Visual diff harness already built this session (`/tmp/cmp.py` +
  soffice `--convert-to pdf` + pymupdf raster, isolated venv at
  `/tmp/cmpenv`) re-run against every `examples/*.md` after the rewrite,
  compared to the existing weasyprint PDF.
- `tests/test_odp.py` rewritten to assert the observable ODF contract
  (parsed content.xml/styles.xml): page bg hex equals the resolved
  section bg, card frame has a border + fill, list items are
  `text:list-item`, frame rects lie within page bounds and don't overlap
  within a grid, dark-variant slide fg/bg match the dark CSS variables.
  Tests pinning old guessed-height/StyleKey internals get deleted.
- `pdm run pytest` green.

## odfdo API notes feeding this design

Full cheat-sheet at `local://odfdo-api.md` (verified against
`references/odfdo/src/odfdo`). Decisions this spec depends on:

- `DrawPage(draw_id=..., name=..., master_page=..., style=...)` —
  keyword-only, first positional is `draw_id` not `name`.
- Presentation-family styles can't take property kwargs directly
  (`Style("presentation", ...)` raises); graphic/paragraph/text styles
  must go through `set_properties(area=..., **kwargs)` with unit
  strings (`"18pt"`, not `18`) — int/float values are silently dropped.
- Master-page background: `insert_style(automatic=True)` targets
  content.xml, but master-page lookups only resolve `drawing-page`
  styles from styles.xml automatic-styles — so the per-theme master
  background style must be appended directly to
  `doc.styles.get_element("office:automatic-styles")`, not via
  `insert_style`. One master per resolved-bg combination (not one
  per slide) — dedup key is the same `ResolvedStyle`-derived style key
  used for graphic styles.
- Lists/tables use real `List`/`ListItem`/`Table` objects inside
  `Frame.text_frame`/`Frame.table_frame` — not manual text with bullet
  characters, confirming the "real ODF semantics" requirement above.
- Slide-root frames need `anchor_type="page"` (default is
  `"paragraph"` when only `position=` is given).
- `doc.body.clear()` is required — `Document("presentation")`'s
  template is not empty.
