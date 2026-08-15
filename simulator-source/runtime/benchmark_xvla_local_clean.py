from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.configs import PreTrainedConfig
from lerobot.envs import make_env_pre_post_processors
from lerobot.envs.configs import LiberoEnv as LiberoEnvConfig
from lerobot.envs.factory import make_env
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.scripts.lerobot_eval import close_envs, rollout
from lerobot.utils.random_utils import set_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite", default="libero_spatial")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument(
        "--bddl-file",
        type=Path,
        help="Optional generated perturbation BDDL for the selected suite task.",
    )
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--width", type=int, default=360)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process_started = time.perf_counter()
    set_seed(args.seed)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True

    env_cfg = LiberoEnvConfig(
        task=args.suite,
        task_ids=[args.task_id],
        bddl_file=str(args.bddl_file.resolve()) if args.bddl_file else None,
        episode_length=args.max_steps,
        obs_type="pixels_agent_pos",
        control_mode="absolute",
        init_states=True,
        observation_height=args.height,
        observation_width=args.width,
    )

    env_build_started = time.perf_counter()
    envs = make_env(env_cfg, n_envs=1, use_async_envs=False)
    env_build_seconds = time.perf_counter() - env_build_started

    model_load_started = time.perf_counter()
    policy_cfg = PreTrainedConfig.from_pretrained(str(args.model_path))
    policy_cfg.pretrained_path = args.model_path
    policy_cfg.device = "cuda"
    policy = make_policy(cfg=policy_cfg, env_cfg=env_cfg, rename_map={})
    policy.eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=policy_cfg,
        pretrained_path=str(args.model_path),
        preprocessor_overrides={
            "device_processor": {"device": "cuda"},
            "rename_observations_processor": {"rename_map": {}},
            "tokenizer_processor": {"tokenizer_name": str(args.tokenizer_path)},
        },
    )
    env_preprocessor, env_postprocessor = make_env_pre_post_processors(
        env_cfg=env_cfg,
        policy_cfg=policy_cfg,
    )
    torch.cuda.synchronize()
    model_load_seconds = time.perf_counter() - model_load_started

    env = envs[args.suite][args.task_id]
    episode_started = time.perf_counter()
    rollout_data = rollout(
        env=env,
        policy=policy,
        env_preprocessor=env_preprocessor,
        env_postprocessor=env_postprocessor,
        preprocessor=preprocessor,
        postprocessor=postprocessor,
        seeds=[args.seed],
        return_observations=False,
        render_callback=None,
    )
    torch.cuda.synchronize()
    episode_seconds = time.perf_counter() - episode_started

    done = rollout_data["done"][0].detach().cpu().numpy().astype(bool)
    finished = np.flatnonzero(done)
    steps = int(finished[0] + 1) if finished.size else int(done.shape[0])
    success = bool(rollout_data["success"][0, :steps].any().item())
    total_reward = float(rollout_data["reward"][0, :steps].sum().item())

    close_envs(envs)
    result = {
        "kind": "xvla_local_native_clean_latency",
        "suite": args.suite,
        "task_id": args.task_id,
        "bddl_file": str(args.bddl_file.resolve()) if args.bddl_file else None,
        "seed": args.seed,
        "init_state_id": 0,
        "initialization_mode": "official_init",
        "camera_height": args.height,
        "camera_width": args.width,
        "control_mode": "absolute",
        "max_steps": args.max_steps,
        "success": success,
        "steps": steps,
        "total_reward": total_reward,
        "env_build_seconds": env_build_seconds,
        "model_and_processor_load_seconds": model_load_seconds,
        "episode_seconds": episode_seconds,
        "episode_ms_per_step": episode_seconds * 1000.0 / steps,
        "process_seconds": time.perf_counter() - process_started,
        "model_path": str(args.model_path),
        "tokenizer_path": str(args.tokenizer_path),
        "device": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
