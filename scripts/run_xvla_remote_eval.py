"""Run local xVLA inference against a server-hosted LIBERO environment."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.request import urlopen

from libero_remote import RemoteLiberoEnv
from libero_remote.runner import (
    EpisodeSpec,
    XVLAPolicyAdapter,
    append_episode_result,
    run_remote_episode,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://172.18.224.1:18082")
    parser.add_argument("--model-path", default="/mnt/d/models/xvla-libero")
    parser.add_argument(
        "--tokenizer-path", default="/mnt/d/models/facebook-bart-large-tokenizer"
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--init-state-id", type=int, default=0)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=300)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.episodes < 1:
        raise SystemExit("--episodes must be at least 1")
    if args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1")

    model_path = Path(args.model_path).expanduser().resolve()
    if not model_path.is_dir():
        raise SystemExit(f"xVLA model directory does not exist: {model_path}")

    health = read_health(args.base_url)
    if health.get("status") != "ok":
        raise SystemExit(f"remote LIBERO service is not ready: {health}")
    catalog = read_json(args.base_url, "/v1/tasks")
    if "absolute" not in catalog.get("control_modes", []):
        raise SystemExit(
            "remote LIBERO service does not advertise absolute control; "
            "deploy the matching server code before running xVLA"
        )

    output = args.output or default_output_path()
    policy = XVLAPolicyAdapter.load(
        str(model_path),
        device=args.device,
        tokenizer_path=args.tokenizer_path,
    )
    results = []
    for episode_index in range(args.episodes):
        env = RemoteLiberoEnv(args.base_url, timeout=args.timeout)
        spec = EpisodeSpec(
            suite=args.suite,
            task_id=args.task_id,
            init_state_id=args.init_state_id + episode_index,
            seed=args.seed + episode_index,
            max_steps=args.max_steps,
        )
        try:
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
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def read_health(base_url: str) -> Dict[str, Any]:
    return read_json(base_url, "/v1/health")


def read_json(base_url: str, path: str) -> Dict[str, Any]:
    with urlopen(f"{base_url.rstrip('/')}{path}", timeout=5.0) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} response must be a JSON object")
    return payload


def default_output_path() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("results") / f"xvla_remote_eval_{timestamp}.jsonl"


if __name__ == "__main__":
    main()
