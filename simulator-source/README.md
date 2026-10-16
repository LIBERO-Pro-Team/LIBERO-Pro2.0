# LIBERO-Pro simulator

This directory contains the LIBERO-based simulator, perturbation runtime, initial states, simulation assets, dataset utilities and upstream lifelong-learning implementations used by LIBERO-Pro.

Use the repository-level README and `docs/remote-evaluation-guide.md` for installation and evaluation. In the standalone evaluation archive, follow its top-level `README.md` and `docs/evaluation.md`. BDDL tasks and the split manifest are in the service source's `assets/` directory; simulation meshes and textures are in `libero/libero/assets/`.

Training implementations and configurations are in `libero/lifelong/` and `libero/configs/`. Training demonstrations are distributed separately at https://huggingface.co/datasets/zhouxueyang/LIBERO-Pro2.0-Train . Policy-specific loaders, dependencies and checkpoints must match the policy being trained.

Retain `LICENSE` and the third-party asset notices in `libero/libero/assets/perturbation_assets/`. Upstream LIBERO: https://github.com/Lifelong-Robot-Learning/LIBERO .
