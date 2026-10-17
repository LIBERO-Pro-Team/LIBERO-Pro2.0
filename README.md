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
  🏆 <a href="https://racingemperor.github.io/LIBERO-Pro2.0/leaderboard.html"><strong>Leaderboard</strong></a> |
  📖 <a href="docs/remote-evaluation-guide.md"><strong>Evaluation Guide</strong></a>
</p>


Evaluation and training resources for robot-policy robustness under 22 static and 20 runtime perturbation types across six domains: Condition, Environment, Observation, Execution, Robot and Language.

![LIBERO-Pro2.0 benchmark overview](static/images/overview.png)

## Resources

| Repository | Contents | Use |
|---|---|---|
| [Evaluation resources](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval) | `evaluation.zip`, `assets.zip`, initial states, task/split manifests and installation tools | Set up evaluation without cloning GitHub |
| [Training data](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train) | Native HDF5 demonstrations, metadata and trajectory source indices | Train or fine-tune policies |

Pretrained-policy evaluation requires the evaluation resources and the policy's official checkpoint/inference environment. Training demonstrations are downloaded separately.

## Installation

### Evaluation Resources

<p align="justify">
Download <code>evaluation.zip</code> (evaluation code, task definitions, and initial states) and <code>assets.zip</code> (objects, scenes, and textures), together with the manifests and preparation script. Run the script below to verify and extract both archives. Allow at least <strong>3 GB</strong> for the package, plus space for dependencies, policy checkpoints, and results. The <a href="https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Eval/blob/main/docs/evaluation.md">installation and evaluation guide</a> covers Linux/NVIDIA EGL setup, policy adapters, batch runs, resuming interrupted runs, and exporting episode results.
</p>

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

<p align="justify">
To connect your policy to an evaluation server, install the client in your policy environment using Python <strong>3.8–3.12</strong>. Install your policy checkpoint and inference dependencies from the model's official release, and obtain the server URL and your API key from the server operator. The command below skips downloading simulator assets, which are included in the evaluation package.
</p>

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/LIBERO-Pro-Team/LIBERO-Pro2.0.git
cd LIBERO-Pro2.0
python -m pip install -e .

export LIBERO_REMOTE_BASE_URL="http://SERVER:8000"
export LIBERO_REMOTE_API_KEY="YOUR_ACCOUNT_API_KEY"
```

## 🔧 Evaluation

<p align="justify">
The Python example checks the connection by resetting a task and sending a zero action. The shell command creates a held-out evaluation plan with three seeds; it does not run the policy. Use <code>--group dynamic</code> to plan evaluation under runtime interventions. For scored evaluations, follow the <a href="docs/model-adapter-contract.md">model adapter</a> and <a href="docs/grouped-benchmark.md">batch evaluation</a> guides, preserving your policy's <strong>official action horizon, preprocessing, control convention, and suite-specific episode limits</strong>.
</p>

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

## Training

[LIBERO-Pro2.0-Train](https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train) contains native HDF5 demonstrations for the 32 training base tasks: 1,349 instances and 40,470 stored demonstrations. Demonstrations were generated by a privileged-state oracle. Of these, 106 instances replicate one source trajectory into 30 records; the release contains 37,396 unique source trajectories. Use `keep_without_declared_fanout` in `manifests/episodes.jsonl` to omit declared copies.

```bash
pip install -U huggingface_hub
hf download zhouxueyang/LIBERO-Pro2.0-Train --repo-type dataset \
  --include "data/**" "release.json" "manifests/**" \
            "docs/data_format.md" "scripts/inspect_episode.py" \
  --local-dir ./data/LIBERO-Pro2.0-Train
```

The [training guide](docs/training.md) explains the HDF5 schema and policy integration. The original LIBERO lifelong-learning implementations and configurations remain in `simulator-source/libero/lifelong/` and `simulator-source/libero/configs/`. Their original task loader expects LIBERO's per-task dataset layout; the released per-instance HDF5 files need an explicit loader or conversion for your policy. Model checkpoints and policy-specific training dependencies come from the corresponding official model releases.

## Licenses

Retain the [upstream LIBERO license](simulator-source/LICENSE) and the asset licenses in `simulator-source/libero/libero/assets/perturbation_assets/THIRD_PARTY_NOTICES.md`. The training dataset's license does not replace code or third-party asset terms.

## Citation

<p align="justify">
If you use LIBERO-Pro2.0 in your research, please cite this project and our earlier work, <a href="https://arxiv.org/abs/2510.03827">LIBERO-PRO</a>, and specify the repository revision used in your experiments:
</p>

```bibtex
@misc{zhou2026liberopro2,
  title = {LIBERO-Pro2.0: A Benchmark for Evaluating the Robustness of Embodied Foundation Models},
  author = {Xueyang Zhou and Yangming Xu and Qianjiang Li and Guiyao Tie and Junhao Wu and Ziheng Huang and Guowen Zhang and Zhijie Yuan and Di Wu and Duanfeng Chu and Pan Zhou and Lichao Sun and Yongchao Chen},
  year = {2026},
  howpublished = {GitHub repository},
  url = {https://github.com/LIBERO-Pro-Team/LIBERO-Pro2.0}
}

@article{zhou2025liberopro,
  title = {LIBERO-PRO: Towards Robust and Fair Evaluation of Vision-Language-Action Models Beyond Memorization},
  author = {Xueyang Zhou and Yangming Xu and Guiyao Tie and Yongchao Chen and Guowen Zhang and Duanfeng Chu and Pan Zhou and Lichao Sun},
  journal = {arXiv preprint arXiv:2510.03827},
  year = {2025},
  url = {https://arxiv.org/abs/2510.03827}
}
```
