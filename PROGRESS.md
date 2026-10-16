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

## 2026-10-16 — Full-width leaderboard tables

- Replaced narrow summaries and collapsed details with two complete 11-column tables. Kept rank, policy and headline scores first, followed by all six perturbation categories.
- Used GitHub-compatible HTML column-width hints; measured both tables at 1280/1280 px in a wide README layout, with overflow confined to the table on narrower layouts.
- Rechecked all 306 scores against the paper data; other README sections are unchanged.
- Implementation commit: `51a31a7bd7d4bdf27dec1a0a1cda282c7d0201bd`.

## 2026-10-16 — Visual leaderboard redesign

- Replaced plain HTML tables with full-width SVG scoreboards: average bars, category heat cells, highlighted leading ranks and fixed single-line column labels. Both settings retain all 17 policies and all paper scores.
- Added a dependency-free deterministic renderer at `scripts/render_readme_leaderboards.py`; regenerate after updating the verified source JSON. SVGs use local assets and vector text without external fonts or scripts.
- Verified all 306 visible scores and both rank orders against the source JSON, inspected both browser-rendered figures at README width, checked text bounds and deterministic regeneration. Other README sections remain unchanged.
- Implementation commit: `3d350160bbf72eb1516edae7db2917024c4ecae0`.

## 2026-10-16 — Concise leaderboard notes

- Combined the three footer paragraphs into one continuous paragraph, shortened the link labels and clarified OFT variant descriptions. Detailed scoring scope remains in the linked results guide.
- Checked Markdown whitespace and confirmed that the figures, scores and other README sections are unchanged.
- Implementation commit: `9156fe616febcd27739c948e451ee99e5980e087`.

## 2026-10-16 — README editorial review

- Polished the overview, leaderboard explanations, catalogue description, resource table, installation steps, evaluation guidance and training-data introduction for an external research audience. Removed historical identifier commentary from the homepage and reduced repeated instructions.
- Retained the distinction between paper and release counts, clarified that the plan command does not execute a policy, and preserved all executable examples, author information and leaderboard graphics.
- Verified unchanged fenced code blocks, key counts, local link targets, resource anchors and Markdown whitespace.
- Implementation commit: `e2fb346ac144638619ebd6d1386a1e2500b2e656`.

## 2026-10-16 — LIBERO-PRO series attribution

- Introduced LIBERO-Pro2.0 as a continuation of the LIBERO-PRO benchmark series and linked the earlier repository from Overview.
- Added the LIBERO-PRO paper to Citation and requested attribution to both works. Verified title, eight-author order, year and arXiv identifier against the official repository and arXiv record; omitted placeholder publisher fields.
- Checked that only Overview and Citation changed in README and that Markdown fences and whitespace remain valid.
- Implementation commit: `0b4e82378828cc0ef03ab620793824ca4e17fe0f`.
