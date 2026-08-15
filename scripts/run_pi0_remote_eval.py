"""Run local Pi0 inference against a server-hosted LIBERO environment."""

import argparse
import json
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from libero_remote import RemoteLiberoEnv
from libero_remote.runner.agent import AgentEpisodeSpec, run_remote_agent_episode
from libero_remote.runner.pi0 import Pi0PolicyAdapter
from libero_remote.runner.report import build_run_manifest
from libero_remote.runner.video import ObservationVideoWriter, episode_video_path
from libero_remote.runner.xvla import append_episode_result, append_run_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://172.18.224.1:18082")
    parser.add_argument(
        "--model-path", default="/mnt/d/models/pi0-libero-finetuned-v044"
    )
    parser.add_argument(
        "--tokenizer-path", default="/mnt/d/models/paligemma-3b-pt-224"
    )
    parser.add_argument("--lerobot-root", default="/mnt/d/lerobot")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--suite", default="libero_spatial")
    parser.add_argument("--task-id", type=int, default=8)
    parser.add_argument("--init-state-id", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--variant", default="base")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("runtime/pi0_remote_eval_spatial_task8_clean.jsonl"),
    )
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--video-dir", type=Path)
    parser.add_argument("--video-camera", default="agentview")
    parser.add_argument("--video-fps", type=float, default=20.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes < 1:
        raise SystemExit("--episodes must be at least 1")
    if args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1")
    if args.video_fps <= 0:
        raise SystemExit("--video-fps must be positive")
    if args.video_dir is not None and not args.record_video:
        raise SystemExit("--video-dir requires --record-video")

    model_path = _require_directory(args.model_path, "Pi0 model")
    tokenizer_path = _require_directory(args.tokenizer_path, "PaliGemma tokenizer")
    lerobot_root = _require_directory(args.lerobot_root, "LeRobot")
    validate_pi0_artifacts(model_path, tokenizer_path)

    health = read_json(args.base_url, "/v1/health", timeout=args.timeout)
    if health.get("status") != "ok":
        raise SystemExit(f"remote LIBERO service is not ready: {health}")
    catalog = read_json(args.base_url, "/v1/tasks", timeout=args.timeout)
    if "relative" not in catalog.get("control_modes", []):
        raise SystemExit("remote LIBERO service does not advertise relative control")
    if args.variant not in catalog.get("variants", []):
        raise SystemExit(
            f"remote LIBERO service does not advertise variant {args.variant!r}"
        )

    output = args.output.expanduser().resolve()
    video_dir = args.video_dir or output.parent / f"{output.stem}_videos"
    repo_root = Path(__file__).resolve().parents[1]
    manifest = build_run_manifest(
        health=health,
        repo_root=repo_root,
        lerobot_root=lerobot_root,
        model_path=model_path,
        tokenizer_path=tokenizer_path,
        evaluation={
            "suite": args.suite,
            "task_id": args.task_id,
            "initial_init_state_id": args.init_state_id,
            "episodes": args.episodes,
            "initial_seed": args.seed,
            "max_steps": args.max_steps,
            "variant": args.variant,
            "control_mode": "relative",
            "device": args.device,
            "record_video": args.record_video,
            "video_camera": args.video_camera if args.record_video else None,
            "video_fps": args.video_fps if args.record_video else None,
        },
    )
    append_run_manifest(output, manifest)
    agent = Pi0PolicyAdapter.load(
        str(model_path),
        device=args.device,
        tokenizer_path=str(tokenizer_path),
    )

    results = []
    for episode_index in range(args.episodes):
        env = RemoteLiberoEnv(args.base_url, timeout=args.timeout)
        spec = AgentEpisodeSpec(
            suite=args.suite,
            task_id=args.task_id,
            init_state_id=args.init_state_id + episode_index,
            seed=args.seed + episode_index,
            max_steps=args.max_steps,
            control_mode="relative",
            variant=args.variant,
        )
        try:
            if args.record_video:
                video_path = episode_video_path(
                    video_dir,
                    model_name="pi0",
                    suite=spec.suite,
                    task_id=spec.task_id,
                    variant=spec.variant,
                    seed=spec.seed,
                    init_state_id=spec.init_state_id,
                )
                with ObservationVideoWriter(
                    video_path, camera=args.video_camera, fps=args.video_fps
                ) as recorder:
                    result = run_remote_agent_episode(env, agent, spec, recorder=recorder)
            else:
                result = run_remote_agent_episode(env, agent, spec)
        finally:
            env.close_transport()
        append_episode_result(output, result)
        results.append(result)
        print(json.dumps(result.to_dict(), sort_keys=True))

    successes = sum(result.success for result in results)
    summary = {
        "status": "completed",
        "output": str(output),
        "episodes": len(results),
        "successes": successes,
        "success_rate": successes / len(results),
        "video_dir": str(Path(video_dir).expanduser().resolve())
        if args.record_video
        else None,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def read_json(base_url: str, path: str, timeout: float = 5.0) -> Dict[str, Any]:
    with urlopen(f"{base_url.rstrip('/')}{path}", timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} response must be a JSON object")
    return payload


def _require_directory(value: str, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise SystemExit(f"{label} directory does not exist: {path}")
    return path


def validate_pi0_artifacts(model_path: Path, tokenizer_path: Path) -> None:
    required_model_files = (
        "config.json",
        "model.safetensors",
        "policy_preprocessor.json",
        "policy_preprocessor_step_5_normalizer_processor.safetensors",
        "policy_postprocessor.json",
        "policy_postprocessor_step_0_unnormalizer_processor.safetensors",
    )
    missing = [name for name in required_model_files if not (model_path / name).is_file()]
    if not (tokenizer_path / "tokenizer_config.json").is_file():
        missing.append("tokenizer/tokenizer_config.json")
    if not any(
        (tokenizer_path / name).is_file() for name in ("tokenizer.json", "tokenizer.model")
    ):
        missing.append("tokenizer/tokenizer.json or tokenizer/tokenizer.model")
    if missing:
        raise SystemExit(f"Pi0 runtime artifacts are incomplete: {missing}")


if __name__ == "__main__":
    main()
