# Project progress

## 2026-10-14 — Paper-aligned project README

- Replaced the deployment-heavy homepage with the project overview, paper figures, two 17-policy leaderboards, and installation/evaluation entry points.
- Preserved the former README in `docs/remote-evaluation-guide.md`; repaired relative links after moving it.
- Extracted active LaTeX tables, excluding commented older results. Preserved all 306 reported values, including deltas computed before rounding.
- Kept paper collection statistics distinct from Hugging Face stored-record counts and documented legacy service case labels.
- Validation: 4 existing client/CLI tests passed; installed CLI help, Markdown links, source hashes, numerical values, and desktop/mobile previews checked.
- For future leaderboard updates, use the source tables and retain reported precision instead of copying website rankings or recomputing rounded deltas.
- Implementation commit: `de12db7d892d2334e8a488146ee7c0a505d78c3c`.

## 2026-10-14 — Project news section

- Replaced the complete Key Findings section, including its figure and caption, with News entries about the available training dataset and paper leaderboards.
- Verified the change is confined to that README section and Markdown whitespace checks pass.
- Implementation commit: `f01bcdad9977ca6086423fde016fc1d765e2f860`.

## 2026-10-16 — README authors and affiliations

- Added all 13 paper authors, five numbered affiliations, equal-contribution and corresponding-author markers below the title.
- Reused the five original institution logos from the project website; stored them in `static/institutions/`.
- Verified names, order and markers against the paper source; checked desktop rendering and mobile wrapping without horizontal overflow.
- Implementation commit: `49a61f51b206fca5a4a6118f1e76b384edcbf4e7`.

## 2026-10-16 — Resource chapter organization

- Grouped Released Code and Task Catalogue and Resource Repositories under one Data and Evaluation Resources chapter, immediately before Installation.
- Preserved the original section bodies and all other README content; checked Markdown whitespace and heading order.
- Implementation commit: `e373fe55ac81f440aff6d7d2e2d7d67a7146c504`.

## 2026-10-16 — Leaderboard presentation

- Removed the standalone LIBERO-Pro2.0 Benchmark chapter. Added ranked five-column static/runtime summaries with complete six-category results in expandable details.
- Shortened resource table labels and descriptions. Preserved installation and subsequent sections.
- Verified all 306 detailed values and 102 summary values against the paper source JSON; checked ordering, expanding details and mobile page width.
- Implementation commit: `8508c30f10a276a3d0da1745e14a02b8661515e4`.
