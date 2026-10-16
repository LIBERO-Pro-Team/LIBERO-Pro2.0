<h1 align="center">
LIBERO-Pro2.0: A Benchmark for Evaluating<br>
the Robustness of Embodied Foundation Models
</h1>

<p align="center">
  Xueyang Zhou<sup>1,*</sup>, Yangming Xu<sup>1,*</sup>, Qianjiang Li<sup>1</sup>, Guiyao Tie<sup>1</sup>,<br>
  Junhao Wu<sup>2</sup>, Ziheng Huang<sup>2</sup>, Guowen Zhang<sup>1</sup>, Zhijie Yuan<sup>5</sup>,<br>
  Di Wu<sup>1</sup>, Duanfeng Chu<sup>3</sup>, Pan Zhou<sup>1,†</sup>, Lichao Sun<sup>4</sup>, Yongchao Chen<sup>2</sup>
</p>

<p align="center">
  <sup>1</sup> Huazhong University of Science and Technology &nbsp; <sup>2</sup> Tsinghua University<br>
  <sup>3</sup> Wuhan University of Technology &nbsp; <sup>4</sup> Lehigh University &nbsp; <sup>5</sup> University of Toronto
</p>

<p align="center">
  <sup>*</sup> Equal contribution. &nbsp; <sup>†</sup> Corresponding author.
</p>

<p align="center">
  <img src="static/institutions/hust.webp" height="34" alt="Huazhong University of Science and Technology"> &nbsp;
  <img src="static/institutions/tsinghua.webp" height="34" alt="Tsinghua University"> &nbsp;
  <img src="static/institutions/whut.webp" height="34" alt="Wuhan University of Technology"> &nbsp;
  <img src="static/institutions/lehigh.webp" height="34" alt="Lehigh University"> &nbsp;
  <img src="static/institutions/toronto.webp" height="34" alt="University of Toronto">
</p>

<p align="center">
  🌐 <a href="https://racingemperor.github.io/LIBERO-Pro2.0/index.html"><strong>Website</strong></a> |
  📁 <a href="https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train"><strong>Training Data</strong></a> |
  📦 <a href="https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval"><strong>Evaluation Resources</strong></a> |
  🏆 <a href="#-leaderboard"><strong>Leaderboard</strong></a> |
  📖 <a href="docs/remote-evaluation-guide.md"><strong>Evaluation Guide</strong></a>
</p>

![LIBERO-Pro2.0 benchmark overview](static/images/overview.png)

## 🔥 Overview

**LIBERO-Pro2.0** is a robustness benchmark for embodied foundation models. Built on LIBERO, it evaluates whether robot policies can generalize when conditions change before execution and adapt when interventions occur during an ongoing task.

The benchmark introduces **22 static distribution shifts** and **20 runtime interventions** across six domains, yielding **1,648 validated shifted task instances**. It separates **32 training tasks** from **8 held-out evaluation tasks** and provides **39,390 training trajectories** in the paper's collection. All shifted instances undergo six rounds of human review and correction, covering **19,776 reviewed rollouts**.

This repository provides the evaluation service, Python client, model adapter interfaces, and reproducible run planning. Robot policies run on the user's machine; the service handles task initialization, simulator execution, perturbations, and success checking.

## 📰 News

- **[2026-10-14]** The [native HDF5 training dataset](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train) is available on Hugging Face, with trajectory previews and review videos.
- **[2026-10-14]** Added the paper's static and runtime [leaderboards](#-leaderboard), covering **17 robot policies**.

## 🏆 Leaderboard

Paper results for **17 policies**, ranked by average success rate. **Avg.** and **Base** are percentages (higher is better); **Δ = Avg. − Base** is in percentage points. Bold marks the best scores. Expand either table to see the six perturbation categories.

### Static Distribution Shifts

| Rank | Policy | Avg. ↑ | Base | Δ (pp) |
|:---:|---|---:|---:|---:|
| 1 | MolmoAct2 | **71.2** | 97.2 | -26.0 |
| 2 | Cosmos Policy | 70.8 | 97.5 | -26.7 |
| 3 | LingBot-VA | 68.7 | 98.5 | -29.7 |
| 4 | π₀.₅ | 66.7 | 93.3 | -26.6 |
| 5 | X-VLA | 61.2 | 95.0 | -33.8 |
| 6 | GR00T N1.7 | 60.0 | 90.4 | -30.4 |
| 7 | OpenVLA-OFT_m | 59.3 | 92.5 | -33.2 |
| 8 | OpenVLA-OFT+ | 59.2 | 92.1 | -32.9 |
| 9 | OpenVLA-OFT | 58.9 | 97.1 | -38.2 |
| 10 | FastWAM | 55.9 | 97.8 | -41.8 |
| 11 | Anchor-Align | 55.9 | 91.3 | -35.4 |
| 12 | RIPT-VLA | 54.1 | 87.5 | -33.4 |
| 13 | OpenVLA-OFT_w | 53.8 | 89.2 | -35.4 |
| 14 | π₀-FAST | 53.2 | 80.4 | -27.3 |
| 15 | UniVLA | 52.9 | 92.1 | -39.2 |
| 16 | π₀ | 38.6 | 63.8 | -25.1 |
| 17 | OpenVLA | 33.9 | 64.6 | -30.7 |

<details>
<summary>View scores by perturbation category</summary>

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

</details>

### Runtime Distribution Shifts

| Rank | Policy | Avg. ↑ | Base | Δ (pp) |
|:---:|---|---:|---:|---:|
| 1 | LingBot-VA | **81.8** | 98.5 | -16.7 |
| 2 | MolmoAct2 | 76.9 | 97.2 | -20.3 |
| 3 | π₀.₅ | 73.8 | 93.3 | -19.5 |
| 4 | Cosmos Policy | 72.2 | 97.5 | -25.3 |
| 5 | FastWAM | 70.1 | 97.8 | -27.6 |
| 6 | X-VLA | 66.0 | 95.0 | -29.0 |
| 7 | OpenVLA-OFT | 64.6 | 97.1 | -32.5 |
| 8 | OpenVLA-OFT_m | 64.3 | 92.5 | -28.2 |
| 9 | GR00T N1.7 | 63.9 | 90.4 | -26.6 |
| 10 | OpenVLA-OFT+ | 63.8 | 92.1 | -28.3 |
| 11 | OpenVLA-OFT_w | 61.9 | 89.2 | -27.3 |
| 12 | Anchor-Align | 61.6 | 91.3 | -29.7 |
| 13 | UniVLA | 61.0 | 92.1 | -31.1 |
| 14 | RIPT-VLA | 58.5 | 87.5 | -29.0 |
| 15 | π₀-FAST | 55.9 | 80.4 | -24.5 |
| 16 | OpenVLA | 36.4 | 64.6 | -28.2 |
| 17 | π₀ | 35.3 | 63.8 | -28.4 |

<details>
<summary>View scores by perturbation category</summary>

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

</details>

Δ is taken directly from the paper and computed before rounding. Static Avg. covers 87 valid suite–perturbation entries (LIBERO-Spatial S04 excluded).

**Category key:** Cond. = Condition; Env. = Environment; Obs. = Observation; Exec. = Execution; Lang. = Language. **OFT variants:** `_w` omits wrist observations; `_m` jointly fine-tunes on the four original LIBERO suites; `+` uses mixed fine-tuning on LIBERO-Plus data.

[Result definitions and source tables](docs/paper-results.md) · [Interactive leaderboard](https://racingemperor.github.io/LIBERO-Pro2.0/leaderboard.html)

## Data and Evaluation Resources

### Released Code and Task Catalogue

`main` is the maintained branch for the evaluation code, simulator, and task catalogue. It contains **1,688 task instances**: **40 BASE**, **863 static**, and **785 runtime** instances across **22 static** and **20 runtime** perturbation types. All 1,688 BDDL files are listed, with checksums, in [`assets/task_manifest.json`](assets/task_manifest.json) and stored under [`assets/bddl/libero-pro2.0-1680-v1/`](assets/bddl/libero-pro2.0-1680-v1/). The `1680` directory suffix and `1706` manifest version are legacy identifiers, not current counts.

The released catalogue has 1,317 training and 331 evaluation shifted instances (BASE excluded); the paper reports 1,313/335. See [catalogue scope and case-ID mapping](docs/paper-results.md#evaluation-service-versions) for this remaining difference. The evaluation commands below use the connected server's catalogue.

### Resource Repositories

| Resource | Purpose | Includes |
|---|---|---|
| [Training data](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train) | Train or fine-tune policies | HDF5 demonstrations for 32 training tasks, metadata, review videos and trajectory previews. |
| [Evaluation resources](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval) | Deploy and evaluate | Service/client, batch runner, 1,688 BDDL definitions, 40 initial-state files, simulator assets, locked dependencies and setup/verification tools. |
| [GitHub source](https://github.com/Zxy-MLlab/LIBERO-Pro2.0/tree/main) | Develop and integrate | Maintained evaluation code, simulator, task catalogue, model adapters and documentation. |

**To evaluate a pretrained model, start with the [Evaluation Resources](#evaluation-resources) below.** Download `evaluation.zip` (code, BDDL and initial states) and `assets.zip` (objects, scenes and textures), together with the manifests and preparation script. Training HDF5 files and preview videos are not needed. Obtain the policy checkpoint and its official inference dependencies from the model's own release.

The Eval repository includes the full compatible catalogue, while the benchmark split remains by base task: **1,349 training instances** (32 BASE + 1,317 shifted) and **339 held-out instances** (8 BASE + 331 shifted). Use `--split test` for held-out evaluation; the authoritative partition is [`assets/benchmark_split_v1.json`](assets/benchmark_split_v1.json). Training review videos are not held-out evaluation results.

## 🛠️ Installation

### Evaluation Resources

Download [Eval](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval) for evaluation code, BDDL, initial states and simulator assets; training trajectories are unnecessary. The script verifies and extracts both archives into a new directory. Reserve at least **3 GB**, plus dependencies, checkpoints and results. Follow the [installation and evaluation guide](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval/blob/main/docs/evaluation.md) for Linux/NVIDIA EGL setup, policy adapters, continuous execution, resume and per-episode result export.

```bash
pip install -U huggingface_hub
hf download zhouxueyang/LIBERO-Pro2.0-Eval --repo-type dataset \
  --include "evaluation.zip" "evaluation.zip.sha256" "assets.zip" "assets.zip.sha256" \
            "manifests/**" "scripts/**" "docs/**" "README.md" "LICENSE_NOTICE.md" "release.json" \
  --local-dir ./data/LIBERO-Pro2.0-Eval

python ./data/LIBERO-Pro2.0-Eval/scripts/prepare_evaluation.py \
  --download-dir ./data/LIBERO-Pro2.0-Eval --output-dir ./libero-pro-install
```

### Model Client

For a separate model client, install this package in your policy environment (Python **3.8–3.12**) and obtain the server URL and API key from its operator. This clone skips simulator assets; the HF bundle already includes them. Fetch official checkpoints and inference dependencies from each model's release.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Zxy-MLlab/LIBERO-Pro2.0.git
cd LIBERO-Pro2.0
python -m pip install -e .

export LIBERO_REMOTE_BASE_URL="http://SERVER:8000"
export LIBERO_REMOTE_API_KEY="YOUR_ACCOUNT_API_KEY"
```

## 🔧 Evaluation

Using the GitHub client, the examples below check connectivity with a zero action and preview a three-seed held-out plan. Keep your policy's **official action horizon, preprocessing, control convention and suite-specific episode limits**; use `--group dynamic` for runtime interventions. See [model adapters](docs/model-adapter-contract.md) and [batch evaluation](docs/grouped-benchmark.md) for scored runs, resume and result export.

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

```bash
python scripts/run_grouped_eval.py \
  --base-url "$LIBERO_REMOTE_BASE_URL" \
  plan --split test --group static \
  --seeds 142 143 144 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/static-plan
```

## Training Data

Download HDF5 demonstrations and metadata from [Train](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train). The command excludes videos, Viewer previews and simulator assets; the full collection needs about **220 GiB** plus cache space. The release contains **40,470 stored records**, including declared replicas, while the paper reports **39,390 training trajectories**; see the [dataset card](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train) for the counting scope.

```bash
pip install -U huggingface_hub
hf download zhouxueyang/LIBERO-Pro2.0-Train --repo-type dataset \
  --include "data/**" "release.json" "manifests/**" \
            "docs/data_format.md" "scripts/inspect_episode.py" \
  --exclude "data/**/review_videos/**" "manifests/assets_manifest.json" \
  --local-dir ./data/LIBERO-Pro2.0-Train
```

## Documentation

[Deployment](docs/remote-evaluation-guide.md) · [Conda setup](deploy/customer-conda/README.md) · [Model adapters](docs/model-adapter-contract.md) · [Batch evaluation](docs/grouped-benchmark.md) · [Paper results](docs/paper-results.md) · [Reproducibility](docs/LIBERO_PRO_Agent_SOP.md)

## Citation

If you use LIBERO-Pro2.0, cite the project and record the repository revision:

```bibtex
@misc{zhou2026liberopro2,
  title = {LIBERO-Pro2.0: A Benchmark for Evaluating the Robustness of Embodied Foundation Models},
  author = {Xueyang Zhou and Yangming Xu and Qianjiang Li and Guiyao Tie and Junhao Wu and Ziheng Huang and Guowen Zhang and Zhijie Yuan and Di Wu and Duanfeng Chu and Pan Zhou and Lichao Sun and Yongchao Chen},
  year = {2026},
  howpublished = {GitHub repository},
  url = {https://github.com/Zxy-MLlab/LIBERO-Pro2.0}
}
```
