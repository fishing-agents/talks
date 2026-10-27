# Deck concepts for the Tuesday talk

**Final candidates (2026-10-25):** A, B and C were merged into two decks; the drafts moved to `drafts/` (their asset paths no longer resolve from there).

| Deck | File | Structure |
|---|---|---|
| Story | `containerdays_neocloud_story.md` | C's one-H200 day carries the talk, A's mechanism detail inside it, B's limits and evidence to close. 17 main slides, 5 backups |
| Blueprint | `containerdays_neocloud_blueprint.md` | Abstract order on A's five layers, B's production evidence per layer. 17 main slides, 7 backups |

The original concepts:

All three keep the CFP title "10x Your Neocloud's GPU Utilization with HAMi", 25 minutes, and cover every promise in `cfp.md` ("What the talk must deliver"). They differ in structure and opening.

| Deck | File | Structure | Opening hook | Anchor evidence |
|---|---|---|---|---|
| A. Blueprint | `containerdays_neocloud_a_blueprint.md` | The stack, bottom-up: enforce → schedule → request (DRA) → sell (SKUs) → operate | "A GPU box is not a GPU cloud" | DaoCloud D.run (10,000+ cards, SKUs, >80%) |
| B. Evidence | `containerdays_neocloud_b_evidence.md` | What 10 production users measured: the waste, the multipliers, what they share and what they don't, the limits | "Seven organisations measured the same 5-20%" | All 11 CNCF case studies |
| C. One GPU | `containerdays_neocloud_c_one_gpu.md` | Follow one H200 through a day; each hour introduces one mechanism | "One job, 1 GB of a 141 GB H200" | Own H200 measurements (3.4x, 18% → 100% SM), then case studies to generalise |

Recommended combination if picking one: start from C's hook and day story, use A's stack slides for the mechanism section, and B's "what not to share" + limits slides near the end.

## How the 10x is framed in all three

10x holds where the starting point is 5-15% (CI, dev envs, notebooks, embedding, small inference): NIO CI up to 10x, CETC 15x, Sangfor 8x models/GPU. Whole platforms land at 2-3x because training already uses its cards. Saying this on stage is the honest version of the title and matches "no vendor pitch".
