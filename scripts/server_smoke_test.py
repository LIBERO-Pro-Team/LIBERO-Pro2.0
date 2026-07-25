"""Create, step, and close a remote environment from a client machine."""

import argparse
import json
from typing import Any, Dict
from urllib.request import urlopen

import numpy as np

from libero_remote import RemoteLiberoEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--init-state-id", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    health = read_health(args.base_url)
    if health.get("status") != "ok":
        raise SystemExit(f"server is not ready: {health}")

    with RemoteLiberoEnv(args.base_url, timeout=args.timeout) as env:
        observation, info = env.reset(
            suite=args.suite,
            task_id=args.task_id,
            init_state_id=args.init_state_id,
            seed=args.seed,
            camera_height=64,
            camera_width=64,
            max_steps=2,
        )
        schema = info["action_schema"]
        action = np.zeros(schema["shape"], dtype=np.float32)
        next_observation, reward, terminated, truncated, step_info = env.step(action)

    report = {
        "status": "passed",
        "backend": health["backend"]["name"],
        "session_id": info["session_id"],
        "episode_id": info["episode_id"],
        "observation_keys": sorted(observation),
        "next_observation_keys": sorted(next_observation),
        "reward": reward,
        "terminated": terminated,
        "truncated": truncated,
        "step_index": step_info["step_index"],
    }
    print(json.dumps(report, indent=2, sort_keys=True))


def read_health(base_url: str) -> Dict[str, Any]:
    with urlopen(f"{base_url.rstrip('/')}/v1/health", timeout=5.0) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("health response must be a JSON object")
    return payload


if __name__ == "__main__":
    main()
