# Grouped Evaluation Across Multiple Seeds

## Train/test split

`assets/benchmark_split_v1.json` defines the versioned train/test boundary by `(suite, base_task_id)`.
All `BASE`, `S01-S22`, `D01-D18`, `D20`, and `D21` instances of a base task follow that task's split;
they must not cross split boundaries. The current main branch contains 1349 training instances and
339 test instances, including 32/8 BASE instances, respectively.
Use `--split test` for evaluation and `--split train` for training rollouts. Combine these with
`--suite`, `--group`, and `--case` to select suites and perturbations precisely.

```bash
python scripts/run_grouped_eval.py plan \
  --split test \
  --suite libero_goal \
  --group all \
  --output-dir results/test-plan
```

The generated `plan.json` records the split name, version, SHA-256, suite/task allocation, and individual
perturbation episodes so that evaluation boundaries can be compared across models.

## Scope

Grouped evaluation adds task selection and plan expansion to the existing model-independent
`RunScheduler`. It does not change the service protocol, model adapter contract, or LIBERO tasks.
The server's `/v1/tasks` catalog is the sole source of valid combinations; nonexistent combinations
are never reconstructed.

Supported evaluation groups:

- `base`: all published BASE tasks.
- `static`: all published static perturbations.
- `dynamic`: all published dynamic perturbations.
- `all`: all published combinations.

Use `--suite` and `--case` to intersect selections. For example, `--group dynamic --suite libero_goal`
selects only published dynamic combinations in `libero_goal`; `--case D07` selects suites with a
published D07 instance.

## Generate and submit a plan

Preview the plan without submitting environment jobs:

```bash
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  plan \
  --group dynamic \
  --suite libero_goal \
  --seeds 42 43 44 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/goal_dynamic_plan
```

After checking the rollout count, submit the plan:

```bash
export LIBERO_REMOTE_API_KEY="ACCOUNT_API_KEY"
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  submit \
  --group dynamic \
  --suite libero_goal \
  --seeds 42 43 44 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/goal_dynamic
```

Without `--max-steps`, each episode uses its task's `max_steps` from `/v1/tasks`, so a plan spanning
suites can contain limits of 220, 280, 300, and 520 steps. Passing this option explicitly overrides
all episodes in the plan and records the source as `override` in `plan.json`.

Consecutive seeds can also be specified with:

```bash
--seed 42 --num-seeds 5
```

By default, seeds and initial states are paired; a single value on either side is broadcast:

```text
seed 42 -> init state 0
seed 43 -> init state 1
seed 44 -> init state 2
```

The Cartesian product of seeds and initial states is generated only when `--matrix` is explicit.

`submit` only submits the full plan to the model-independent scheduler. An online generic Agent
runner can claim the jobs. With `--wait`, the submission command waits for an external runner to
finish and exports the results automatically. This command does not load the model.

## Run from an existing Agent runner

User code that already constructs an `AgentAdapter` can reuse the same plan:

```python
from pathlib import Path

from libero_remote import RemoteRunClient
from libero_remote.benchmark import build_benchmark_plan, run_grouped_benchmark

with RemoteRunClient(server_url, api_key=api_key) as client:
    plan = build_benchmark_plan(
        client.get_task_catalog(),
        group="static",
        suites=["libero_spatial"],
        seeds=[42, 43, 44],
        init_state_ids=[0, 1, 2],
        control_mode="relative",
    )
    result = run_grouped_benchmark(
        client,
        plan,
        adapter,
        runner_id="host-a-gpu-0",
        output_dir=Path("results/spatial_static"),
    )
```

This function depends only on the repository's existing `AgentAdapter` contract, not on model names.

## Resume and export

The server persists run and episode state in SQLite. After an interruption, call
`run_grouped_benchmark(..., run_id=...)` with the original plan and existing `run_id`.
It validates each episode spec before claiming only the remaining jobs.

An existing run can also be exported directly:

```bash
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  export \
  --run-id run_xxx \
  --output-dir results/recovered_run
```

The output directory contains:

```text
plan.json          Task selection, manifest identity, and full episode plan
submission.json    Server run ID
run.json           Current run state
episodes.jsonl     Authoritative per-episode results
episodes.csv       Flattened results for spreadsheet analysis
failures.jsonl     Infrastructure failures
summary.json       Overall and suite/variant/group/seed summaries
```

Success rates use only policy episodes marked `completed` by the server as the denominator.
Infrastructure episodes marked `failed` are counted separately and are not treated as normal policy failures.
