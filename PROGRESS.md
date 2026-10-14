# Project progress

## 2026-10-14 — Paper-aligned project README

- Replaced the deployment-heavy homepage with the project overview, paper figures, two 17-policy leaderboards, and installation/evaluation entry points.
- Preserved the former README in `docs/remote-evaluation-guide.md`; repaired relative links after moving it.
- Extracted active LaTeX tables, excluding commented older results. Preserved all 306 reported values, including deltas computed before rounding.
- Kept paper collection statistics distinct from Hugging Face stored-record counts and documented legacy service case labels.
- Validation: 4 existing client/CLI tests passed; installed CLI help, Markdown links, source hashes, numerical values, and desktop/mobile previews checked.
- For future leaderboard updates, use the source tables and retain reported precision instead of copying website rankings or recomputing rounded deltas.
- Implementation commit: `de12db7d892d2334e8a488146ee7c0a505d78c3c`.
