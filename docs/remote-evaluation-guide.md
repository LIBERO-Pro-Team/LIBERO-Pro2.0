# Install and run LIBERO-Pro evaluation

This bundle contains the evaluation service/client, batch scheduler, 1,688 BDDL task definitions, and the 40 initial-state files used by the four supported LIBERO suites. The separate `assets.zip` supplies simulator objects, scenes, textures and perturbation assets. The preparation script installs those assets into the correct directory. No GitHub clone or Git LFS download is required after downloading both archives.

## Install the environment (Linux, NVIDIA EGL, Conda)

The reference simulator environment uses Python 3.8.10, MuJoCo 3.2.3 and robosuite 1.4.0. `requirements-lock.txt` is the captured reference dependency lock. An NVIDIA driver/EGL installation and access to Conda/Python package indexes are needed. The simulator uses CPU Torch from this lock; run policy inference in the model's separate official environment.

```bash
cd LIBERO-Pro-evaluation
export LIBERO_PRO_CONDA_PREFIX="$PWD/.envs/libero-pro"
bash install.sh "$LIBERO_PRO_CONDA_PREFIX"
bash configure.sh "$LIBERO_PRO_CONDA_PREFIX"
bash start.sh
bash healthcheck.sh
set -a
source client.env
set +a
"$LIBERO_PRO_CONDA_PREFIX/bin/python" smoke_test.py
```

The smoke test executes one zero action to check the simulator and transport; it is not a scored model evaluation. `configure.sh` generates private credentials and defaults to localhost. `runtime/scheduler.sqlite3` persists runs. Keep the bundle, runtime database and credentials in place to resume work; stop normally with `bash stop.sh`. EGL troubleshooting is in `EGL_HEADLESS.md`.

## Plan and submit repeated evaluation

Run the policy in its own official Python environment, with the lightweight client installed:

```bash
python -m pip install -e ./service-source
set -a
source client.env
set +a
python service-source/scripts/run_grouped_eval.py \
  --base-url "$LIBERO_REMOTE_URL" \
  plan --split test --group all --seed 142 --num-seeds 30 \
  --init-state-ids 0 --control-mode relative --output-dir results/plan
```

`plan` only previews work. This selects 339 valid held-out instances, including BASE, for **10,170 episodes** (30 seeds per instance, fixed initial-state ID 0). This is a runnable repeated-evaluation example, not a claim that this seed/initial-state schedule exactly reproduces the paper. To score static/runtime cases separately, use `--group static` or `--group dynamic`; select suites/cases with `--suite` and `--case`. An explicit list of seed and initial-state IDs can be supplied for a different protocol.

Submit the same selection (do not use `--wait` before starting a runner):

```bash
python service-source/scripts/run_grouped_eval.py \
  --base-url "$LIBERO_REMOTE_URL" \
  submit --split test --group all --seed 142 --num-seeds 30 \
  --init-state-ids 0 --control-mode relative --output-dir results/run
```

Copy the printed `run_id`. Create a factory `your_policy:create_adapter(**kwargs)` returning an adapter with `reset(context)`, `act(observation)` and `close()`. Pass checkpoint/configuration options in your own JSON file. The complete input/action contract is in `model-adapter-contract.md`.

```bash
python service-source/scripts/run_policy.py \
  --base-url "$LIBERO_REMOTE_URL" --run-id RUN_ID \
  --adapter-factory your_policy:create_adapter \
  --adapter-kwargs policy_config.json --output-dir results/run
```

The factory is the user's model integration, not a bundled checkpoint. The runner loads it once and repeatedly claims pending episodes. For interrupted runs, rerun the runner with the same `run_id`; do not submit a duplicate run. Adapter reset must clear model state, action queues and history at each independent episode. Invalid actions cause an explicit failed attempt, not an invented valid action.

Use each model's **official action horizon and preprocessing** inside its adapter. The bundle preserves the published suite defaults (Spatial 220, Object 280, Goal 300, LIBERO-10 520 environment steps); if a model's official evaluation requires a different suite limit, set `--max-steps` to that official value and record it. This changes episode length, not action chunk length. Match `--control-mode` to the official policy (relative/absolute); never reuse a different model's action convention.

## Results, continuous execution and parallel runners

```bash
python service-source/scripts/run_grouped_eval.py \
  --base-url "$LIBERO_REMOTE_URL" export --run-id RUN_ID --output-dir results/run
```

Exports include per-episode JSONL/CSV with success, episode specifications and attempt metadata, plus grouped JSON summaries by suite, perturbation, group and seed. Distinguish policy failures, incomplete episodes and infrastructure errors when reporting success rates. The scheduler database is the authority for completed episodes.

For concurrent policy processes, configure `LIBERO_REMOTE_MAX_SESSIONS` and `LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER` before the first `configure.sh` call; start each runner with a unique `--runner-id`. The default is one active simulator session. This release raises only the queue capacity to 16,384 so the 10,170-episode example fits; it does not force GPU concurrency or alter task parameters. Start more model processes only when memory and simulator capacity allow. Do not share a model's state between processes.

## Task catalogue and scope

`service-source/assets/task_manifest.json` lists 1,688 BDDL files: 40 BASE, 863 static and 785 dynamic. The complete catalogue is provided for compatibility; held-out evaluation is selected by `--split test`, not by training on these task definitions. The split file contains train 1,349 (32 BASE + 1,317 shifted) and test 339 (8 BASE + 331 shifted). Held-out zero-based base task IDs are Spatial 0/8, Object 1/8, Goal 3/6, LIBERO-10 5/8.

Historical path suffix `1680` and manifest version `1706` are identifiers, not current counts. Internal D20/D21 correspond to paper D19/D20. Do not silently rename runtime IDs when reproducing evaluation.

Training HDF5 and trajectory metadata are in https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train and are not required to evaluate a pretrained policy. Official model checkpoints remain in their respective model repositories.

## Verification boundary

Archive inventories/checksums, all 1,688 BDDL hashes, split counts, 40 initial-state file paths, Python syntax and the bundled service/scheduler tests are checked during release preparation. The package retains the pinned runtime and task definitions. A new GPU/EGL model rollout and a fresh Linux installation of all dependency wheels are not implied by these checks; run the smoke test on the target machine before starting scored runs.

## Run from the GitHub source

The simulator's upstream baseline is `c02ee2c8255db1c36664fad978197c47e495f178`; the repository includes subsequent runtime and asset updates. Use the source and task manifest from the same checkout or release, rather than combining files from different revisions.

The archive layout above uses `service-source/` for the repository root and `simulator-source/` for the bundled simulator. When running from a GitHub checkout, remove the `service-source/` prefix from client commands. Download Git LFS assets with `git lfs pull`, or use the verified asset package from the evaluation repository. For the complete non-Docker installation, use the HF preparation script so deployment scripts are placed next to both source directories.

To build the Docker service directly from the checkout, copy `.env.example` to `.env`, generate your own account-key hash and result-signing secret as described in that file, then run `docker compose up --build -d`. Supply the same plaintext account key to the client as `LIBERO_REMOTE_API_KEY`; do not commit credentials. See `deploy/customer-conda/EGL_HEADLESS.md` for EGL requirements.
