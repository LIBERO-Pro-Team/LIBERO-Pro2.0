"""Run local xVLA inference against a server-hosted LIBERO environment."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from libero_remote import RemoteLiberoEnv
from libero_remote.environment.task_manifest import resolve_catalog_max_steps
from libero_remote.runner.report import build_run_manifest
from libero_remote.runner.video import ObservationVideoWriter, episode_video_path
from libero_remote.runner.xvla import (
    EpisodeSpec,
    XVLAPolicyAdapter,
    append_episode_result,
    append_run_manifest,
    run_remote_episode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://172.18.224.1:18082")
    parser.add_argument("--model-path", default="/mnt/d/models/xvla-libero")
    parser.add_argument("--lerobot-root", default="/mnt/d/lerobot")
    parser.add_argument(
        "--tokenizer-path", default="/mnt/d/models/facebook-bart-large-tokenizer"
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--variant", default="base")
    parser.add_argument("--init-state-id", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--video-dir", type=Path)
    parser.add_argument("--video-camera", default="agentview")
    parser.add_argument("--video-fps", type=float, default=20.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes < 1:
        raise SystemExit("--episodes must be at least 1")
    if args.max_steps is not None and args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1")
    if args.video_fps <= 0:
        raise SystemExit("--video-fps must be positive")
    if args.video_dir is not None and not args.record_video:
        raise SystemExit("--video-dir requires --record-video")

    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.is_dir():
        raise SystemExit(f"xVLA model directory does not exist: {model_path}")
    tokenizer_path = Path(args.tokenizer_path).expanduser().resolve()
    if not tokenizer_path.is_dir():
        raise SystemExit(f"tokenizer directory does not exist: {tokenizer_path}")
    lerobot_root = Path(args.lerobot_root).expanduser().resolve()
    if not lerobot_root.is_dir():
        raise SystemExit(f"LeRobot directory does not exist: {lerobot_root}")

    health = read_health(args.base_url, timeout=args.timeout)
    if health.get("status") != "ok":
        raise SystemExit(f"remote LIBERO service is not ready: {health}")
    catalog = read_json(args.base_url, "/v1/tasks", timeout=args.timeout)
    if "absolute" not in catalog.get("control_modes", []):
        raise SystemExit(
            "remote LIBERO service does not advertise absolute control; "
            "deploy the matching server code before running xVLA"
        )
    try:
        max_steps = args.max_steps or resolve_catalog_max_steps(
            catalog, args.suite, args.task_id, args.variant
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    output = args.output or default_output_path()
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
            "variant": args.variant,
            "initial_init_state_id": args.init_state_id,
            "episodes": args.episodes,
            "initial_seed": args.seed,
            "max_steps": max_steps,
            "control_mode": "absolute",
            "device": args.device,
            "record_video": args.record_video,
            "video_camera": args.video_camera if args.record_video else None,
            "video_fps": args.video_fps if args.record_video else None,
        },
    )
    append_run_manifest(output, manifest)
    policy = XVLAPolicyAdapter.load(
        str(model_path),
        device=args.device,
        tokenizer_path=str(tokenizer_path),
    )
    results = []
    for episode_index in range(args.episodes):
        env = RemoteLiberoEnv(args.base_url, timeout=args.timeout)
        spec = EpisodeSpec(
            suite=args.suite,
            task_id=args.task_id,
            init_state_id=args.init_state_id + episode_index,
            seed=args.seed + episode_index,
            max_steps=max_steps,
            variant=args.variant,
        )
        try:
            if args.record_video:
                video_path = episode_video_path(
                    video_dir,
                    model_name="xvla",
                    suite=spec.suite,
                    task_id=spec.task_id,
                    variant=spec.variant,
                    seed=spec.seed,
                    init_state_id=spec.init_state_id,
                )
                with ObservationVideoWriter(
                    video_path, camera=args.video_camera, fps=args.video_fps
                ) as recorder:
                    result = run_remote_episode(env, policy, spec, recorder=recorder)
            else:
                result = run_remote_episode(env, policy, spec)
        finally:
            env.close_transport()
        append_episode_result(output, result)
        results.append(result)
        print(json.dumps(result.to_dict(), sort_keys=True))

    summary = {
        "status": "completed",
        "output": str(output.resolve()),
        "episodes": len(results),
        "successes": sum(result.success for result in results),
        "success_rate": sum(result.success for result in results) / len(results),
        "video_dir": str(Path(video_dir).expanduser().resolve())
        if args.record_video
        else None,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def read_health(base_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    return read_json(base_url, "/v1/health", timeout=timeout)


def read_json(base_url: str, path: str, timeout: float = 5.0) -> Dict[str, Any]:
    with urlopen(f"{base_url.rstrip('/')}{path}", timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} response must be a JSON object")
    return payload


def default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("results") / f"xvla_remote_eval_{timestamp}.jsonl"


if __name__ == "__main__":
    main()
