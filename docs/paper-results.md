# Paper results and benchmark scope

[Back to the project README](../README.md)

The README leaderboards reproduce the active `tab:static_leaderboard` and
`tab:runtime_leaderboard` tables in `sections/Experiments.tex` from the supplied
LIBERO-Pro2.0 paper source. Commented-out earlier tables are excluded.

## Results

- [Machine-readable paper scores](results/paper-leaderboards.json)
- [Static leaderboard source](results/static-leaderboard.tex)
- [Runtime leaderboard source](results/runtime-leaderboard.tex)

Each table contains 17 policies and nine numerical fields per policy: six
perturbation-category scores, Avg., Base, and Δ. Values retain the paper's
one-decimal precision. The JSON stores the reported values as strings to retain
that precision and includes the SHA-256 of the source experiments file.
README rows are sorted by Avg.; values are not recomputed or taken from the
interactive website.

## Aggregation

Scores are task success rates (%). Base is nominal task success. Δ is
Avg. minus Base in percentage points, computed before rounding in the paper.
Subtracting the displayed, rounded numbers can therefore differ by 0.1 points
from the reported Δ.

Static category scores average valid suite–perturbation entries over
LIBERO-Goal, LIBERO-Object, LIBERO-Spatial, and LIBERO-10. Static Avg. covers
87 valid entries, excluding S04 in LIBERO-Spatial. It is not an unweighted
mean of the six displayed category scores.

| Category | Static IDs in the paper leaderboard | Runtime IDs in the paper leaderboard |
|---|---|---|
| Condition | S01–S05, S07–S09 | D01–D06 |
| Environment | S06, S10–S14, S22 | D07–D09 |
| Observation | S15–S16, S19 | D10–D13 |
| Execution | S20 | D14–D16 |
| Robot | S17–S18 | D17–D19 |
| Language | S21 | D20 |

The ranges above follow the leaderboard table headings. Figure panels may
combine several domains to illustrate mechanisms; they do not redefine the
leaderboard aggregation.

![Matched static and runtime perturbation results from the paper](../static/images/static-runtime-comparison.png)

*Original paper figure: comparisons between matched static and runtime
perturbations. These are per-perturbation results, distinct from category
averages in the leaderboards.*

## Paper task partition

The paper samples two held-out tasks per suite with seed 142. Task IDs are
zero-based within each suite.

| Suite | Evaluation IDs | Training-pool IDs |
|---|---|---|
| LIBERO-Spatial | 0, 8 | 1, 2, 3, 4, 5, 6, 7, 9 |
| LIBERO-Object | 1, 8 | 0, 2, 3, 4, 5, 6, 7, 9 |
| LIBERO-Goal | 3, 6 | 0, 1, 2, 4, 5, 7, 8, 9 |
| LIBERO-10 | 5, 8 | 0, 1, 2, 3, 4, 6, 7, 9 |

The paper reports 1,313 training and 335 evaluation shifted instances, totaling
1,648 validated shifted instances, and 39,390 training trajectories.

## Published training package

The linked Hugging Face package currently contains 40,470 stored demonstration
records over 1,349 instances. Its source audit reports 37,396 unique source
trajectories; 106 instances replicate one source trajectory into 30 stored
records. These release records are not a one-to-one count of the paper's
39,390 training trajectories. The README preserves both reported scopes
without claiming equivalence.

Use the [dataset card](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0)
and [data format guide](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0/blob/main/docs/data_format.md)
for download scope, schemas, and declared-copy filtering.

## Evaluation service versions

The paper's catalogue uses S01–S22 and D01–D20. The checked-in service
catalogues are separate versions; selecting the same eight base tasks does not
make their available perturbation combinations identical to the paper.

| Catalogue | BASE instances | Shifted instances | Training shifted instances | Evaluation shifted instances |
|---|---:|---:|---:|---:|
| Paper | — | 1,648 | 1,313 | 335 |
| `main` at `6586733` | 40 | 1,640 | 1,312 | 328 |
| `model-agnostic-multiuser` at `3ac451e` | 40 | 1,648 | 1,317 | 331 |

The branch counts come from their respective `assets/task_manifest.json`
files, using the held-out task IDs listed above. The shifted-instance columns
exclude BASE. Sources: [main manifest](https://github.com/Zxy-MLlab/LIBERO-Pro2.0/blob/6586733a731710a82979dfc6e952924d455d8a71/assets/task_manifest.json)
and [experimental manifest](https://github.com/Zxy-MLlab/LIBERO-Pro2.0/blob/3ac451e6e85ee6995bf684b56f6c04f8ef7c8829/assets/task_manifest.json).

The earlier `main` catalogue has 21 static types (S01–S21) and 20 runtime types
(D01–D19 and D21). The experimental branch has 22 static types (S01–S22) and
20 runtime types (D01–D18, D20, and D21). In the experimental branch, internal
D20 corresponds to paper D19 (robot joint perturbation), and internal D21
corresponds to paper D20 (instruction restatement); D01–D18 are unchanged.
Do not apply this mapping blindly to older catalogues.

Pin the server revision and inspect its `/v1/tasks` catalogue before submitting
an evaluation. The examples in the README demonstrate the client and planning
interfaces; they do not establish equivalence between these releases. The
[grouped evaluation guide](grouped-benchmark.md) describes task selection and export.

## Figures

- `static/images/overview.png`: rendered from `figures/promain.pdf`, then the
  lower logo line was shifted 35 pixels left to center it; its former background
  was restored. Figure labels, numbers, and dimensions are unchanged.
- `static/images/failure-patterns.png`: byte-preserved copy of `figures/example.png`.
- `static/images/static-runtime-comparison.png`: rendered directly from
  `figures/fig_grouped_static_runtime.pdf`.

PDF figures are rendered for browser display; their labels and numbers are
preserved. Source fingerprints are recorded in [figure-sources.json](results/figure-sources.json).
