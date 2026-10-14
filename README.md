<h1 align="center">
LIBERO-Pro2.0: A Benchmark for Evaluating<br>
the Robustness of Embodied Foundation Models
</h1>

<p align="center">
  🌐 <a href="https://racingemperor.github.io/LIBERO-Pro2.0/index.html"><strong>Website</strong></a> |
  📁 <a href="https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0"><strong>Training Data</strong></a> |
  🏆 <a href="#-leaderboard"><strong>Leaderboard</strong></a> |
  📖 <a href="docs/remote-evaluation-guide.md"><strong>Evaluation Guide</strong></a>
</p>

![LIBERO-Pro2.0 benchmark overview](static/images/overview.png)

## 🔥 Overview

**LIBERO-Pro2.0** is a robustness benchmark for embodied foundation models. Built on LIBERO, it evaluates whether robot policies can generalize when conditions change before execution and adapt when interventions occur during an ongoing task.

The benchmark introduces **22 static distribution shifts** and **20 runtime interventions** across six domains, yielding **1,648 validated shifted task instances**. It separates **32 training tasks** from **8 held-out evaluation tasks** and provides **39,390 training trajectories** in the paper's collection. All shifted instances undergo six rounds of human review and correction, covering **19,776 reviewed rollouts**.

This repository provides the evaluation service, Python client, model adapter interfaces, and reproducible run planning. Robot policies run on the user's machine; the service handles task initialization, simulator execution, perturbations, and success checking.

## 📰 News

- **[2026-10-14]** The [native HDF5 training dataset](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0) is available on Hugging Face, with trajectory previews and review videos.
- **[2026-10-14]** Added the paper's static and runtime [leaderboards](#-leaderboard), covering **17 robot policies**.

## 📊 LIBERO-Pro2.0 Benchmark

### Six Perturbation Domains

1. **Condition** — Object poses, task geometry, receiving regions, and interaction constraints.
2. **Environment** — Object instances, distractors, clutter, appearance, and scene context.
3. **Observation** — Camera settings, sensor quality, frame streams, and modality alignment.
4. **Execution** — Control timing, command delivery, action chunks, and temporary interventions.
5. **Robot** — Initialization, calibration, joint state, grasp failures, and recoverable drops.
6. **Language** — Instruction paraphrases and runtime restatements that preserve the goal.

Static shifts are configured at reset. Runtime interventions are triggered at task-relevant stages such as approach, grasp, transport, or placement. Original task goals and success predicates are preserved.

### Task Partition

The paper samples two evaluation tasks from each LIBERO suite with seed **142**. Task IDs are **zero-based** within each suite. Their complement forms the training pool; all variants of a base task stay in the same partition.

| Suite | Held-out evaluation task IDs | Training tasks |
|---|---|---:|
| LIBERO-Spatial | 0, 8 | 8 |
| LIBERO-Object | 1, 8 | 8 |
| LIBERO-Goal | 3, 6 | 8 |
| LIBERO-10 | 5, 8 | 8 |
| **Total** | **8 evaluation tasks** | **32** |

After validation, the paper contains **1,313 training instances** and **335 evaluation instances**. Detailed perturbation definitions and visual examples are available in the [project documentation](https://racingemperor.github.io/LIBERO-Pro2.0/docs.html).

### Repository and Paper Versions

The overview and leaderboards describe the paper benchmark. The current `main` branch still contains an earlier **1,680-instance manifest**: 40 BASE instances and 1,640 shifted instances, with **21 static** and **20 runtime** perturbation types. Its catalogue is not the paper's 42-type release.

The [`model-agnostic-multiuser` branch](https://github.com/Zxy-MLlab/LIBERO-Pro2.0/tree/model-agnostic-multiuser) contains **1,688 instances**, including 40 BASE and 1,648 shifted instances across all 42 types. Its task partition also differs from the paper's reported 1,313/335 split. See [versioned catalogue counts and case-ID mapping](docs/paper-results.md#evaluation-service-versions) before choosing a server version; the evaluation commands below use the connected server's catalogue.

## 🏆 Leaderboard

The following tables reproduce the **17-policy results from the accompanying paper**. All success rates are percentages; **Δ = Avg. − Base** is measured in percentage points. Rows are ranked by Avg., and the highest scores in each perturbation column and Avg. are bolded.

Category averages and Δ are computed before rounding in the paper. The displayed Δ is therefore preserved as reported, rather than recalculated from rounded Avg. and Base. The [table sources and machine-readable results](docs/paper-results.md) provide the full provenance and category definitions.

### Static Distribution Shifts

Avg. covers **87 valid suite–perturbation entries**, excluding S04 in LIBERO-Spatial.

| Model | Cond. | Env. | Obs. | Exec. | Robot | Lang. | Avg. | Base | Δ (pp) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MolmoAct2 | **63.8** | 85.0 | 65.1 | 0.0 | 85.0 | 94.6 | **71.2** | 97.2 | -26.0 |
| Cosmos Policy | 56.9 | **89.3** | **70.8** | 4.2 | 82.5 | 93.3 | 70.8 | 97.5 | -26.7 |
| LingBot-VA | 52.2 | 86.1 | 35.7 | **86.7** | **98.3** | **97.1** | 68.7 | 98.5 | -29.7 |
| π₀.₅ | 60.7 | 83.9 | 43.3 | 0.8 | 85.0 | 93.3 | 66.7 | 93.3 | -26.6 |
| X-VLA | 42.1 | 81.7 | 49.3 | 71.7 | 61.7 | 90.8 | 61.2 | 95.0 | -33.8 |
| GR00T N1.7 | 46.6 | 79.2 | 48.5 | 0.0 | 77.9 | 88.8 | 60.0 | 90.4 | -30.4 |
| OpenVLA-OFT_m | 45.9 | 78.3 | 49.7 | 0.0 | 72.1 | 92.1 | 59.3 | 92.5 | -33.2 |
| OpenVLA-OFT+ | 47.2 | 78.5 | 45.0 | 0.0 | 73.8 | 90.0 | 59.2 | 92.1 | -32.9 |
| OpenVLA-OFT | 44.1 | 82.0 | 46.3 | 0.0 | 66.5 | 94.6 | 58.9 | 97.1 | -38.2 |
| FastWAM | 43.8 | 84.7 | 5.2 | 2.8 | 87.5 | 90.3 | 55.9 | 97.8 | -41.8 |
| Anchor-Align | 43.2 | 74.3 | 38.6 | 0.8 | 76.5 | 90.8 | 55.9 | 91.3 | -35.4 |
| RIPT-VLA | 41.0 | 74.3 | 41.8 | 0.0 | 63.8 | 86.7 | 54.1 | 87.5 | -33.4 |
| OpenVLA-OFT_w | 40.1 | 64.9 | 67.6 | 0.4 | 55.4 | 90.0 | 53.8 | 89.2 | -35.4 |
| π₀-FAST | 43.8 | 71.5 | 39.9 | 0.0 | 57.7 | 81.2 | 53.2 | 80.4 | -27.3 |
| UniVLA | 39.8 | 59.5 | 58.1 | 0.0 | 79.6 | 91.7 | 52.9 | 92.1 | -39.2 |
| π₀ | 25.0 | 53.8 | 60.0 | 5.0 | 19.2 | 46.3 | 38.6 | 63.8 | -25.1 |
| OpenVLA | 25.2 | 37.6 | 34.4 | 0.0 | 54.0 | 67.5 | 33.9 | 64.6 | -30.7 |

### Runtime Distribution Shifts

| Model | Cond. | Env. | Obs. | Exec. | Robot | Lang. | Avg. | Base | Δ (pp) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LingBot-VA | **77.3** | 81.5 | 90.5 | **96.8** | 59.3 | **96.7** | **81.8** | 98.5 | -16.7 |
| MolmoAct2 | 58.6 | 74.2 | 90.3 | 90.4 | **79.0** | 94.2 | 76.9 | 97.2 | -20.3 |
| π₀.₅ | 60.5 | 58.1 | 86.6 | 88.9 | 77.5 | 94.2 | 73.8 | 93.3 | -19.5 |
| Cosmos Policy | 45.6 | **84.7** | 87.9 | 85.6 | 70.6 | 95.8 | 72.2 | 97.5 | -25.3 |
| FastWAM | 43.6 | 67.1 | 90.7 | 89.9 | 71.4 | 93.2 | 70.1 | 97.8 | -27.6 |
| X-VLA | 41.7 | 59.7 | **93.6** | 70.1 | 70.1 | 95.0 | 66.0 | 95.0 | -29.0 |
| OpenVLA-OFT | 42.8 | 63.1 | 80.4 | 85.3 | 57.6 | 95.4 | 64.6 | 97.1 | -32.5 |
| OpenVLA-OFT_m | 39.6 | 61.4 | 80.4 | 85.7 | 63.6 | 93.8 | 64.3 | 92.5 | -28.2 |
| GR00T N1.7 | 41.7 | 66.0 | 77.9 | 82.4 | 60.3 | 89.6 | 63.9 | 90.4 | -26.6 |
| OpenVLA-OFT+ | 41.3 | 56.9 | 79.8 | 84.2 | 64.0 | 93.8 | 63.8 | 92.1 | -28.3 |
| OpenVLA-OFT_w | 34.9 | 77.8 | 74.6 | 81.0 | 54.0 | 91.7 | 61.9 | 89.2 | -27.3 |
| Anchor-Align | 42.4 | 47.4 | 77.4 | 87.5 | 58.8 | 88.3 | 61.6 | 91.3 | -29.7 |
| UniVLA | 30.9 | 71.7 | 78.9 | 81.5 | 56.2 | 90.8 | 61.0 | 92.1 | -31.1 |
| RIPT-VLA | 38.4 | 57.6 | 72.0 | 76.3 | 54.6 | 86.7 | 58.5 | 87.5 | -29.0 |
| π₀-FAST | 45.6 | 45.4 | 60.9 | 70.0 | 58.3 | 79.2 | 55.9 | 80.4 | -24.5 |
| OpenVLA | 20.6 | 41.9 | 41.3 | 53.6 | 29.9 | 63.8 | 36.4 | 64.6 | -28.2 |
| π₀ | 24.9 | 56.9 | 52.7 | 30.8 | 7.2 | 61.3 | 35.3 | 63.8 | -28.4 |

**Columns:** Cond. = Condition; Env. = Environment; Obs. = Observation; Exec. = Execution; Lang. = Language; Base = nominal performance.

**OpenVLA-OFT variants:** `_w` omits wrist-camera observations; `_m` uses joint fine-tuning across the four original LIBERO suites; `+` uses mixed fine-tuning on LIBERO-Plus data.

Visit the [interactive leaderboard](https://racingemperor.github.io/LIBERO-Pro2.0/leaderboard.html) to explore models and perturbations. The tables above reflect the supplied paper snapshot.

## 🛠️ Installation

### Model Client

Install the lightweight client in your model environment (Python **3.8–3.12**):

```bash
git clone https://github.com/Zxy-MLlab/LIBERO-Pro2.0.git
cd LIBERO-Pro2.0
python -m pip install -e .
```

The model runs locally and connects to an evaluation server. Obtain the server URL and an account API key from the server operator. To host your own service, follow the [Conda deployment guide](deploy/customer-conda/README.md) or the [complete evaluation and deployment guide](docs/remote-evaluation-guide.md).

### Training Data

```bash
pip install -U huggingface_hub
hf download zhouxueyang/LIBERO-Pro2.0 \
  --repo-type dataset --local-dir ./data/LIBERO-Pro2.0
```

The public release uses native HDF5 and includes camera observations, robot states, actions, metadata, and review clips. Allow approximately **220 GiB**, plus cache space.

The paper's collection reports **39,390 training trajectories**. The current Hugging Face package exposes **40,470 stored demonstration records**, including declared replicated trajectories; its record counts and provenance are documented in the [dataset card](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0). These are distinct reporting scopes.

## 🔧 Evaluation

### Connect to an Environment

Set the URL and API key for your evaluation server:

```bash
export LIBERO_REMOTE_BASE_URL="http://SERVER:8000"
export LIBERO_REMOTE_API_KEY="YOUR_ACCOUNT_API_KEY"
```

The client follows a Gym-style `reset()` / `step()` interface. This example sends one zero action to check the connection; use your policy's action for model evaluation.

```python
import os
import numpy as np
from libero_remote import RemoteLiberoEnv

with RemoteLiberoEnv(
    os.environ["LIBERO_REMOTE_BASE_URL"],
    api_key=os.environ["LIBERO_REMOTE_API_KEY"],
) as env:
    observation, info = env.reset(
        suite="libero_spatial",
        task_id=0,
        init_state_id=0,
        seed=142,
        control_mode="relative",
    )
    action = np.zeros(7, dtype=np.float32)
    observation, reward, terminated, truncated, info = env.step(action)
```

Match your policy's preprocessing and control semantics to the server's observation and action schema. See the [model adapter guide](docs/model-adapter-contract.md) for integrating a policy with the scheduled runner.

### Plan a Held-Out Evaluation

```bash
python scripts/run_grouped_eval.py \
  --base-url "$LIBERO_REMOTE_BASE_URL" \
  plan --split test --group static \
  --seeds 142 143 144 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/static-plan
```

This three-seed command is a planning example, not the full paper evaluation protocol. For scored runs, also match the model's official action horizon and suite-specific episode limit.

Use `--group dynamic` for runtime interventions. Available combinations come from the server's `/v1/tasks` catalog. The `plan` command previews episodes; `submit` queues them for an external model runner. See [grouped evaluation](docs/grouped-benchmark.md) for execution, resume, and result export.

## Documentation

- [Evaluation and deployment](docs/remote-evaluation-guide.md)
- [Conda server deployment](deploy/customer-conda/README.md)
- [Model adapter contract](docs/model-adapter-contract.md)
- [Grouped evaluation and result export](docs/grouped-benchmark.md)
- [Paper results and source tables](docs/paper-results.md)
- [Environment reproducibility and evaluation SOP](docs/LIBERO_PRO_Agent_SOP.md)

## Citation

If you use LIBERO-Pro2.0, please acknowledge this project and cite the repository revision used. A repository citation is provided below:

```bibtex
@misc{zhou2026liberopro2,
  title = {LIBERO-Pro2.0: A Benchmark for Evaluating the Robustness of Embodied Foundation Models},
  author = {Xueyang Zhou and Yangming Xu and Qianjiang Li and Guiyao Tie and Junhao Wu and Ziheng Huang and Guowen Zhang and Zhijie Yuan and Di Wu and Duanfeng Chu and Pan Zhou and Lichao Sun and Yongchao Chen},
  year = {2026},
  howpublished = {GitHub repository},
  url = {https://github.com/Zxy-MLlab/LIBERO-Pro2.0}
}
```
