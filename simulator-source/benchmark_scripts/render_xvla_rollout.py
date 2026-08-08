from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

from lerobot.configs import PreTrainedConfig
from lerobot.envs import make_env_pre_post_processors, preprocess_observation
from lerobot.envs.configs import LiberoEnv as LiberoEnvConfig
from lerobot.envs.factory import make_env
from lerobot.policies.factory import make_policy, make_pre_post_processors
from lerobot.scripts.lerobot_eval import close_envs
from lerobot.utils.constants import ACTION
from lerobot.utils.io_utils import write_video
from lerobot.utils.random_utils import set_seed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one XVLA LIBERO rollout and save its rendered MP4."
    )
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--task-id", type=int, required=True)
    parser.add_argument(
        "--bddl-file",
        type=Path,
        help="Optional generated perturbation BDDL for the selected suite task.",
    )
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--max-steps", type=int, default=800)
    parser.add_argument("--height", type=int, default=360)
    parser.add_argument("--width", type=int, default=360)
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        help="Video frame rate. Defaults to the environment render FPS.",
    )
    return parser.parse_args()


def rollout_with_agent_frames(
    env,
    policy,
    env_preprocessor,
    env_postprocessor,
    preprocessor,
    postprocessor,
    seed: int,
) -> tuple[list[np.ndarray], int, bool, float]:
    """Run one rollout while retaining only the returned agent-view frames."""
    policy.reset()
    observation, _ = env.reset(seed=[seed])
    frames = [observation["pixels"]["image"][0].copy()]
    max_steps = int(env.call("_max_episode_steps")[0])
    success = False
    total_reward = 0.0

    for step in range(max_steps):
        policy_observation = preprocess_observation(observation)
        try:
            policy_observation["task"] = list(env.call("task_description"))
        except (AttributeError, NotImplementedError):
            policy_observation["task"] = list(env.call("task"))

        policy_observation = env_preprocessor(policy_observation)
        policy_observation = preprocessor(policy_observation)
        with torch.inference_mode():
            action = policy.select_action(policy_observation)
        action = postprocessor(action)
        action_transition = env_postprocessor({ACTION: action})
        action_numpy = action_transition[ACTION].to("cpu").numpy()

        observation, reward, terminated, truncated, info = env.step(action_numpy)
        # LiberoEnv returns the terminal observation even though it internally resets
        # after success. Reading env.render() here would instead show the reset state.
        frames.append(observation["pixels"]["image"][0].copy())
        total_reward += float(np.asarray(reward)[0])

        if "final_info" in info:
            success = success or bool(np.asarray(info["final_info"]["is_success"])[0])
        elif "is_success" in info:
            success = success or bool(np.asarray(info["is_success"])[0])

        if bool(np.asarray(terminated | truncated)[0]):
            return frames, step + 1, success, total_reward

    return frames, max_steps, success, total_reward


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
    env = envs[args.suite][args.task_id]

    try:
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
                "tokenizer_processor": {
                    "tokenizer_name": str(args.tokenizer_path)
                },
            },
        )
        env_preprocessor, env_postprocessor = make_env_pre_post_processors(
            env_cfg=env_cfg,
            policy_cfg=policy_cfg,
        )
        torch.cuda.synchronize()
        model_load_seconds = time.perf_counter() - model_load_started

        episode_started = time.perf_counter()
        frames, steps, success, total_reward = rollout_with_agent_frames(
            env=env,
            policy=policy,
            env_preprocessor=env_preprocessor,
            env_postprocessor=env_postprocessor,
            preprocessor=preprocessor,
            postprocessor=postprocessor,
            seed=args.seed,
        )
        torch.cuda.synchronize()
        episode_seconds = time.perf_counter() - episode_started

        task_description = ""
        try:
            task_description = str(env.call("task_description")[0])
        except (AttributeError, NotImplementedError):
            pass

        image_sequence = np.stack(frames)
        # Match LiberoEnv.render(), which flips raw robosuite camera arrays for display.
        video_frames = np.ascontiguousarray(image_sequence[:, ::-1, ::-1])
        fps = args.fps or int(env.unwrapped.metadata["render_fps"])
        args.video.parent.mkdir(parents=True, exist_ok=True)
        write_video(args.video, video_frames, fps)

        result = {
            "kind": "xvla_local_native_rendered_rollout",
            "suite": args.suite,
            "task_id": args.task_id,
            "task_description": task_description,
            "bddl_file": str(args.bddl_file.resolve()) if args.bddl_file else None,
            "seed": args.seed,
            "init_state_id": 0,
            "initialization_mode": "official_init",
            "video_frame_source": "step-returned pixels.image (pre-reset terminal observation)",
            "camera_height": args.height,
            "camera_width": args.width,
            "control_mode": "absolute",
            "max_steps": args.max_steps,
            "success": success,
            "steps": steps,
            "total_reward": total_reward,
            "video_path": str(args.video),
            "video_frames": len(video_frames),
            "video_fps": fps,
            "video_seconds": len(video_frames) / fps,
            "video_bytes": args.video.stat().st_size,
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
        args.output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False), flush=True)
    finally:
        close_envs(envs)


if __name__ == "__main__":
    main()
