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

Paper results for **17 policies**, ranked by average success rate. Scores are percentages (higher is better); **Base** is nominal success and **Δ = Avg. − Base** is in percentage points. Bold marks the best scores.

### Static Distribution Shifts

<table width="100%">
<thead>
<tr>
<th width="500" align="center">Rank</th>
<th width="2000" align="left">Policy</th>
<th width="1000" align="right">Avg. ↑</th>
<th width="1000" align="right">Base</th>
<th width="1000" align="right">Δ (pp)</th>
<th width="1000" align="right">Condition</th>
<th width="1000" align="right">Environment</th>
<th width="1000" align="right">Observation</th>
<th width="1000" align="right">Execution</th>
<th width="1000" align="right">Robot</th>
<th width="1000" align="right">Language</th>
</tr>
</thead>
<tbody>
<tr><td align="center">1</td><td align="left">MolmoAct2</td><td align="right"><strong>71.2</strong></td><td align="right">97.2</td><td align="right">-26.0</td><td align="right"><strong>63.8</strong></td><td align="right">85.0</td><td align="right">65.1</td><td align="right">0.0</td><td align="right">85.0</td><td align="right">94.6</td></tr>
<tr><td align="center">2</td><td align="left">Cosmos Policy</td><td align="right">70.8</td><td align="right">97.5</td><td align="right">-26.7</td><td align="right">56.9</td><td align="right"><strong>89.3</strong></td><td align="right"><strong>70.8</strong></td><td align="right">4.2</td><td align="right">82.5</td><td align="right">93.3</td></tr>
<tr><td align="center">3</td><td align="left">LingBot-VA</td><td align="right">68.7</td><td align="right">98.5</td><td align="right">-29.7</td><td align="right">52.2</td><td align="right">86.1</td><td align="right">35.7</td><td align="right"><strong>86.7</strong></td><td align="right"><strong>98.3</strong></td><td align="right"><strong>97.1</strong></td></tr>
<tr><td align="center">4</td><td align="left">π₀.₅</td><td align="right">66.7</td><td align="right">93.3</td><td align="right">-26.6</td><td align="right">60.7</td><td align="right">83.9</td><td align="right">43.3</td><td align="right">0.8</td><td align="right">85.0</td><td align="right">93.3</td></tr>
<tr><td align="center">5</td><td align="left">X-VLA</td><td align="right">61.2</td><td align="right">95.0</td><td align="right">-33.8</td><td align="right">42.1</td><td align="right">81.7</td><td align="right">49.3</td><td align="right">71.7</td><td align="right">61.7</td><td align="right">90.8</td></tr>
<tr><td align="center">6</td><td align="left">GR00T N1.7</td><td align="right">60.0</td><td align="right">90.4</td><td align="right">-30.4</td><td align="right">46.6</td><td align="right">79.2</td><td align="right">48.5</td><td align="right">0.0</td><td align="right">77.9</td><td align="right">88.8</td></tr>
<tr><td align="center">7</td><td align="left">OpenVLA-OFT_m</td><td align="right">59.3</td><td align="right">92.5</td><td align="right">-33.2</td><td align="right">45.9</td><td align="right">78.3</td><td align="right">49.7</td><td align="right">0.0</td><td align="right">72.1</td><td align="right">92.1</td></tr>
<tr><td align="center">8</td><td align="left">OpenVLA-OFT+</td><td align="right">59.2</td><td align="right">92.1</td><td align="right">-32.9</td><td align="right">47.2</td><td align="right">78.5</td><td align="right">45.0</td><td align="right">0.0</td><td align="right">73.8</td><td align="right">90.0</td></tr>
<tr><td align="center">9</td><td align="left">OpenVLA-OFT</td><td align="right">58.9</td><td align="right">97.1</td><td align="right">-38.2</td><td align="right">44.1</td><td align="right">82.0</td><td align="right">46.3</td><td align="right">0.0</td><td align="right">66.5</td><td align="right">94.6</td></tr>
<tr><td align="center">10</td><td align="left">FastWAM</td><td align="right">55.9</td><td align="right">97.8</td><td align="right">-41.8</td><td align="right">43.8</td><td align="right">84.7</td><td align="right">5.2</td><td align="right">2.8</td><td align="right">87.5</td><td align="right">90.3</td></tr>
<tr><td align="center">11</td><td align="left">Anchor-Align</td><td align="right">55.9</td><td align="right">91.3</td><td align="right">-35.4</td><td align="right">43.2</td><td align="right">74.3</td><td align="right">38.6</td><td align="right">0.8</td><td align="right">76.5</td><td align="right">90.8</td></tr>
<tr><td align="center">12</td><td align="left">RIPT-VLA</td><td align="right">54.1</td><td align="right">87.5</td><td align="right">-33.4</td><td align="right">41.0</td><td align="right">74.3</td><td align="right">41.8</td><td align="right">0.0</td><td align="right">63.8</td><td align="right">86.7</td></tr>
<tr><td align="center">13</td><td align="left">OpenVLA-OFT_w</td><td align="right">53.8</td><td align="right">89.2</td><td align="right">-35.4</td><td align="right">40.1</td><td align="right">64.9</td><td align="right">67.6</td><td align="right">0.4</td><td align="right">55.4</td><td align="right">90.0</td></tr>
<tr><td align="center">14</td><td align="left">π₀-FAST</td><td align="right">53.2</td><td align="right">80.4</td><td align="right">-27.3</td><td align="right">43.8</td><td align="right">71.5</td><td align="right">39.9</td><td align="right">0.0</td><td align="right">57.7</td><td align="right">81.2</td></tr>
<tr><td align="center">15</td><td align="left">UniVLA</td><td align="right">52.9</td><td align="right">92.1</td><td align="right">-39.2</td><td align="right">39.8</td><td align="right">59.5</td><td align="right">58.1</td><td align="right">0.0</td><td align="right">79.6</td><td align="right">91.7</td></tr>
<tr><td align="center">16</td><td align="left">π₀</td><td align="right">38.6</td><td align="right">63.8</td><td align="right">-25.1</td><td align="right">25.0</td><td align="right">53.8</td><td align="right">60.0</td><td align="right">5.0</td><td align="right">19.2</td><td align="right">46.3</td></tr>
<tr><td align="center">17</td><td align="left">OpenVLA</td><td align="right">33.9</td><td align="right">64.6</td><td align="right">-30.7</td><td align="right">25.2</td><td align="right">37.6</td><td align="right">34.4</td><td align="right">0.0</td><td align="right">54.0</td><td align="right">67.5</td></tr>
</tbody>
</table>

### Runtime Distribution Shifts

<table width="100%">
<thead>
<tr>
<th width="500" align="center">Rank</th>
<th width="2000" align="left">Policy</th>
<th width="1000" align="right">Avg. ↑</th>
<th width="1000" align="right">Base</th>
<th width="1000" align="right">Δ (pp)</th>
<th width="1000" align="right">Condition</th>
<th width="1000" align="right">Environment</th>
<th width="1000" align="right">Observation</th>
<th width="1000" align="right">Execution</th>
<th width="1000" align="right">Robot</th>
<th width="1000" align="right">Language</th>
</tr>
</thead>
<tbody>
<tr><td align="center">1</td><td align="left">LingBot-VA</td><td align="right"><strong>81.8</strong></td><td align="right">98.5</td><td align="right">-16.7</td><td align="right"><strong>77.3</strong></td><td align="right">81.5</td><td align="right">90.5</td><td align="right"><strong>96.8</strong></td><td align="right">59.3</td><td align="right"><strong>96.7</strong></td></tr>
<tr><td align="center">2</td><td align="left">MolmoAct2</td><td align="right">76.9</td><td align="right">97.2</td><td align="right">-20.3</td><td align="right">58.6</td><td align="right">74.2</td><td align="right">90.3</td><td align="right">90.4</td><td align="right"><strong>79.0</strong></td><td align="right">94.2</td></tr>
<tr><td align="center">3</td><td align="left">π₀.₅</td><td align="right">73.8</td><td align="right">93.3</td><td align="right">-19.5</td><td align="right">60.5</td><td align="right">58.1</td><td align="right">86.6</td><td align="right">88.9</td><td align="right">77.5</td><td align="right">94.2</td></tr>
<tr><td align="center">4</td><td align="left">Cosmos Policy</td><td align="right">72.2</td><td align="right">97.5</td><td align="right">-25.3</td><td align="right">45.6</td><td align="right"><strong>84.7</strong></td><td align="right">87.9</td><td align="right">85.6</td><td align="right">70.6</td><td align="right">95.8</td></tr>
<tr><td align="center">5</td><td align="left">FastWAM</td><td align="right">70.1</td><td align="right">97.8</td><td align="right">-27.6</td><td align="right">43.6</td><td align="right">67.1</td><td align="right">90.7</td><td align="right">89.9</td><td align="right">71.4</td><td align="right">93.2</td></tr>
<tr><td align="center">6</td><td align="left">X-VLA</td><td align="right">66.0</td><td align="right">95.0</td><td align="right">-29.0</td><td align="right">41.7</td><td align="right">59.7</td><td align="right"><strong>93.6</strong></td><td align="right">70.1</td><td align="right">70.1</td><td align="right">95.0</td></tr>
<tr><td align="center">7</td><td align="left">OpenVLA-OFT</td><td align="right">64.6</td><td align="right">97.1</td><td align="right">-32.5</td><td align="right">42.8</td><td align="right">63.1</td><td align="right">80.4</td><td align="right">85.3</td><td align="right">57.6</td><td align="right">95.4</td></tr>
<tr><td align="center">8</td><td align="left">OpenVLA-OFT_m</td><td align="right">64.3</td><td align="right">92.5</td><td align="right">-28.2</td><td align="right">39.6</td><td align="right">61.4</td><td align="right">80.4</td><td align="right">85.7</td><td align="right">63.6</td><td align="right">93.8</td></tr>
<tr><td align="center">9</td><td align="left">GR00T N1.7</td><td align="right">63.9</td><td align="right">90.4</td><td align="right">-26.6</td><td align="right">41.7</td><td align="right">66.0</td><td align="right">77.9</td><td align="right">82.4</td><td align="right">60.3</td><td align="right">89.6</td></tr>
<tr><td align="center">10</td><td align="left">OpenVLA-OFT+</td><td align="right">63.8</td><td align="right">92.1</td><td align="right">-28.3</td><td align="right">41.3</td><td align="right">56.9</td><td align="right">79.8</td><td align="right">84.2</td><td align="right">64.0</td><td align="right">93.8</td></tr>
<tr><td align="center">11</td><td align="left">OpenVLA-OFT_w</td><td align="right">61.9</td><td align="right">89.2</td><td align="right">-27.3</td><td align="right">34.9</td><td align="right">77.8</td><td align="right">74.6</td><td align="right">81.0</td><td align="right">54.0</td><td align="right">91.7</td></tr>
<tr><td align="center">12</td><td align="left">Anchor-Align</td><td align="right">61.6</td><td align="right">91.3</td><td align="right">-29.7</td><td align="right">42.4</td><td align="right">47.4</td><td align="right">77.4</td><td align="right">87.5</td><td align="right">58.8</td><td align="right">88.3</td></tr>
<tr><td align="center">13</td><td align="left">UniVLA</td><td align="right">61.0</td><td align="right">92.1</td><td align="right">-31.1</td><td align="right">30.9</td><td align="right">71.7</td><td align="right">78.9</td><td align="right">81.5</td><td align="right">56.2</td><td align="right">90.8</td></tr>
<tr><td align="center">14</td><td align="left">RIPT-VLA</td><td align="right">58.5</td><td align="right">87.5</td><td align="right">-29.0</td><td align="right">38.4</td><td align="right">57.6</td><td align="right">72.0</td><td align="right">76.3</td><td align="right">54.6</td><td align="right">86.7</td></tr>
<tr><td align="center">15</td><td align="left">π₀-FAST</td><td align="right">55.9</td><td align="right">80.4</td><td align="right">-24.5</td><td align="right">45.6</td><td align="right">45.4</td><td align="right">60.9</td><td align="right">70.0</td><td align="right">58.3</td><td align="right">79.2</td></tr>
<tr><td align="center">16</td><td align="left">OpenVLA</td><td align="right">36.4</td><td align="right">64.6</td><td align="right">-28.2</td><td align="right">20.6</td><td align="right">41.9</td><td align="right">41.3</td><td align="right">53.6</td><td align="right">29.9</td><td align="right">63.8</td></tr>
<tr><td align="center">17</td><td align="left">π₀</td><td align="right">35.3</td><td align="right">63.8</td><td align="right">-28.4</td><td align="right">24.9</td><td align="right">56.9</td><td align="right">52.7</td><td align="right">30.8</td><td align="right">7.2</td><td align="right">61.3</td></tr>
</tbody>
</table>

Δ is taken directly from the paper and computed before rounding. Static Avg. covers 87 valid suite–perturbation entries (LIBERO-Spatial S04 excluded).

**OFT variants:** `_w` omits wrist observations; `_m` jointly fine-tunes on the four original LIBERO suites; `+` uses mixed fine-tuning on LIBERO-Plus data.

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
