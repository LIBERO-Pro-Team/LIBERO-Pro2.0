# LIBERO-PRO v1.0.0: Conda Deployment

This directory provides a local Linux runtime as an alternative to Docker deployment. Regular users
start both the service and model client; routine operation requires no root, sudo, or Docker.
NVIDIA drivers, host EGL driver libraries, and Conda are host prerequisites. Initial driver
installation may require an administrator.

Download the full installation package from
[LIBERO-Pro2.0-Eval](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval).
Follow the root README to verify and extract `evaluation.zip` and `assets.zip` with
`scripts/prepare_evaluation.py`, then enter the generated `LIBERO-Pro-evaluation/` directory
and run the commands below. The release contains 1688 task instances: 40 BASE, 863 static, and
785 dynamic. See the package's `SOURCE_BASELINE.json` for the exact source revision.
This directory contains deployment script sources; it does not itself provide the package's
two-source-tree layout.

## Pinned baseline

Python dependencies are pinned to the validated Docker `v1.0.0` runtime; see `requirements-lock.txt`.
Exact versions include Python `3.8.10`, Torch `1.11.0+cpu`, MuJoCo `3.2.3`, robosuite `1.4.0`,
FastAPI `0.103.2`, and Uvicorn `0.23.2`. Service and simulator code come from the release snapshot:

- Service: `service_commit` in the package's `SOURCE_BASELINE.json`.
- Simulator: the `simulator-source/` subdirectory at the same repository revision; see `simulator_commit` and `simulator_subdirectory`. The upstream revision is `c02ee2c8255db1c36664fad978197c47e495f178`, with subsequent runtime and asset fixes included.
- Reference Docker image digest (for comparison only, not a Conda runtime image): `sha256:969cdf6bc1a3a9f50ce5529bfd7aab6e746d53f9b3d03333bbe793636ba4f933`

Use `SOURCE_BASELINE.json` and the download repository's per-file manifests for verification.
Keep the packaged `service-source/`, `simulator-source/`, and task manifests together. The package
includes full source and environment assets; Python/Conda dependency installation still requires
access to the configured package repositories.

## Host requirements

- Ubuntu 20.04/22.04 x86_64, with user write access to the target Conda prefix and package directory.
- Conda or Miniconda/Miniforge capable of creating a Python 3.8 environment.
- NVIDIA drivers allowing the current user to run `nvidia-smi`. Drivers must provide `libEGL_nvidia.so`; CPU OSMesa results cannot substitute for GPU/EGL evaluation.
- No Docker, Docker Compose, NVIDIA Container Toolkit, or root access is required at runtime.

## Installation

After extracting the release package, run from its deployment directory:

```bash
conda --version
conda create -p /data/user/envs/libero-pro2 python=3.8.10
bash install.sh /data/user/envs/libero-pro2
```

`install.sh` synchronizes Conda build tools and EGL libraries from `environment.yml`, installs exact
Python dependencies from `requirements-lock.txt`, then installs both pinned source trees in editable
mode. Omit the argument to use `$HOME/.conda/envs/libero-pro2`. The script does not invoke sudo or Docker.

## Configure, start, and check

Initial configuration generates a random account key. The server stores only its SHA-256 hash;
the plaintext client key is written to `client.env`. Both files use mode `0600`; do not commit or share them.

```bash
bash configure.sh /data/user/envs/libero-pro2
bash start.sh
bash status.sh
bash healthcheck.sh
set -a
source client.env
set +a
/data/user/envs/libero-pro2/bin/python smoke_test.py
```

Stop the service:

```bash
bash stop.sh
bash status.sh
```

`configure.sh` binds to `127.0.0.1:8000` by default. A model on the same host can load the client configuration:

```bash
set -a
source client.env
set +a
/data/user/envs/libero-pro2/bin/python your_model_client.py
```

For evaluation across machines, explicitly set the service bind address and client URL before
configuration. Restrict firewall access to the designated model host; do not expose plaintext
HTTP on port 8000 to the public Internet:

```bash
export LIBERO_REMOTE_HOST=0.0.0.0
export LIBERO_REMOTE_PORT=8000
export LIBERO_REMOTE_PUBLIC_URL=http://LIBERO_SERVER_LAN_IP:8000
bash configure.sh /data/user/envs/libero-pro2
```

For concurrent accounts, set total capacity before initial configuration, then generate a separate
client file for each account. Stop the service before changing accounts:

```bash
export LIBERO_REMOTE_MAX_SESSIONS=2
bash configure.sh /data/user/envs/libero-pro2
bash add_account.sh team-b
bash start.sh
```

Give `client.env` and `client-team-b.env` only to their respective users; do not share them.
The service isolates sessions, runs, leases, and results by account, with one active session per
account by default.

## Model integration

The server provides environment reset/step/result interfaces without loading model weights.
Clients can implement an `AgentAdapter` or use `RemoteLiberoEnv` directly; the service is not tied
to xVLA, Pi0, or any other model. Fix inference randomness, processor versions, and action sequences
on the model side to reproduce full trajectories.

## Reproducibility

`smoke_test.py` uses the published `libero_goal/task 9/BASE/init state 0/seed 142` and sends one zero
action. It checks the service connection, not policy success. Byte-identical initial environment
states require the same suite, task, variant, initial state, seed, camera dimensions, control mode,
and perturbation plan. Full trajectory reproduction also requires the same model, processor,
model seed, and action sequence. Retries must reuse the episode spec rather than randomly choosing
another task or seed.

## Runtime files

`runtime/` stores the scheduler database and PID metadata; `logs/` stores service logs. Do not delete
database or PID files while the service runs. Use `bash stop.sh` for a normal shutdown. To rotate
keys, stop the service, back up and remove `server.env`/`client.env`, then rerun `configure.sh`.

See [`EGL_HEADLESS.md`](EGL_HEADLESS.md) for detailed EGL, MuJoCo, and host-driver checks.
