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

Paper results for **17 policies**, ranked by average success. Bars compare average success; shaded cells show performance across the six perturbation categories. **Base** is nominal success, and **Δ** is the change from Base in percentage points. Click a figure to view it at full resolution.

### Static Distribution Shifts

[![Static leaderboard: all 17 policies and six perturbation categories](static/leaderboards/static.svg)](static/leaderboards/static.svg)

### Runtime Distribution Shifts

[![Runtime leaderboard: all 17 policies and six perturbation categories](static/leaderboards/runtime.svg)](static/leaderboards/runtime.svg)

Δ is taken directly from the paper and computed before rounding. Static Avg. covers 87 valid suite–perturbation entries (LIBERO-Spatial S04 excluded).

**OFT variants:** `_w` omits wrist observations; `_m` jointly fine-tunes on the four original LIBERO suites; `+` uses mixed fine-tuning on LIBERO-Plus data.

[Result definitions and source tables](docs/paper-results.md) · [Scores (JSON)](docs/results/paper-leaderboards.json) · [Interactive leaderboard](https://racingemperor.github.io/LIBERO-Pro2.0/leaderboard.html)

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
