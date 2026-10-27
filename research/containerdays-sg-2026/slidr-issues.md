# slidr renderer issues found while building the ContainerDays decks

Found by the deck agents on 2026-10-24 and worked around in the decks. Issues 1-5 and 7-10 have since been fixed in slidr commit `78eebf2`: 1-5, 7 and 8 have regression tests, and the CSS fixes 9-10 were checked by rendering a 6-card timeline to PDF. The deck workarounds still work and can be removed.

| # | Issue | Workaround used in decks | Severity |
|---|---|---|---|
| 1 | Double quotes inside `<!-- notes -->` are not escaped in the `data-notes` attribute, so note text leaks onto the slide | single quotes in notes | high (silently corrupts slides) |
| 2 | `>` in card / metric text renders as literal `&gt;` (double-escaped) | `80%+`, `3x+`, "over 95%" | high |
| 3 | `> quote` inside `::: notes` renders the `>` literally (README documents that syntax) | plain text | medium |
| 4 | Text after a seaborn fence inside a `::: card` is dropped | put text in the card `###` header before the chart | medium |
| 5 | Auto-grouped cards split around a following non-card block (table, paragraph, quote, chart): first card alone, block, then the rest | explicit `::: grid {cols=N}` | medium |
| 6 | Six auto-grouped cards become six columns and overflow | explicit `grid cols=3` | low |
| 7 | `**bold**` / inline code inside pipe-table cells is stripped | icons + legend line | low |
| 8 | Inline code in `@subtitle` shows literal backticks | removed backticks | low |
| 9 | `timeline-horizontal` cards are content-sized with no shrink; 5-6 cards overflow the slide width | deck CSS: `.layout-timeline-horizontal .card { max-width: 11em; font-size: 0.88em; }` | medium |
| 10 | `{focus}` uses `box-shadow`, which weasyprint ignores (invisible in PDF) | deck CSS adds a border on `.card.focus` | medium |
| 11 | A metric grid followed by another grid gets no vertical gap | deck CSS `.slide-body > .grid + .grid { margin-top: 0.8em }` | low |
| 12 | Graphviz node `class="cyan"/"green"` renders grey under `kubecon_japan` | explicit fillcolor/color | low (fixed in slidr `7c2a96e`) |
| 13 | `two-col` with a left column taller than the slide: flex children shrink and overlap | shorter bullets | low |
| 14 | `seaborn_theme: kubecon_japan` sets `patch.force_edgecolor` with the red accent and darkgrid lines | charts set `force_edgecolor` False, `ax.grid(False)` | low |
| 15 | Title-slide speaker link icons render dark on the dark gradient (also in `gpu_workshop.md`) | not fixed | cosmetic |
| 16 | Icons with `cls=accent-*` inside table cells look the same colour as text in PDF | not investigated | cosmetic |
