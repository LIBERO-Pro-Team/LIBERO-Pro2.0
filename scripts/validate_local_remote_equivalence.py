"""Validate SOP protocol, adapter, and environment equivalence layers."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen

import numpy as np

from libero_remote import RemoteLiberoEnv
from libero_remote.environment import create_environment_adapter
from libero_remote.protocol.models import PROTOCOL_VERSION
from libero_remote.server.runtime import collect_runtime_manifest
from libero_remote.validation import (
    compare_observations,
    validate_messagepack_roundtrip,
    validate_xvla_adapter_mapping,
)

REPORT_SCHEMA_VERSION = "1.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--local-backend", choices=("libero", "fake"), default="libero")
    parser.add_argument("--suite", default="libero_goal")
    parser.add_argument("--task-id", type=int, default=9)
    parser.add_argument("--init-state-id", type=int, default=0)
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--control-mode", choices=("relative", "absolute"), default="relative")
    parser.add_argument("--camera-height", type=int, default=128)
    parser.add_argument("--camera-width", type=int, default=128)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--actions", type=Path)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--state-rtol", type=float, default=1e-5)
    parser.add_argument("--state-atol", type=float, default=1e-6)
    parser.add_argument("--image-max-abs", type=float, default=0.0)
    parser.add_argument("--image-mean-abs", type=float, default=0.0)
    parser.add_argument("--image-mismatch-ratio", type=float, default=0.0)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    for name in (
        "state_rtol",
        "state_atol",
        "image_max_abs",
        "image_mean_abs",
        "image_mismatch_ratio",
    ):
        if getattr(args, name) < 0:
            raise SystemExit(f"--{name.replace('_', '-')} must not be negative")

    health = _read_health(args.base_url)
    if health.get("status") != "ok":
        raise SystemExit(f"remote LIBERO service is not ready: {health}")

    spec = {
        "protocol_version": PROTOCOL_VERSION,
        "suite": args.suite,
        "task_id": args.task_id,
        "init_state_id": args.init_state_id,
        "seed": args.seed,
        "variant": "base",
        "control_mode": args.control_mode,
        "camera_names": ["agentview", "robot0_eye_in_hand"],
        "camera_height": args.camera_height,
        "camera_width": args.camera_width,
        "max_steps": args.steps,
        "observation_schema_version": "libero_standard_v1",
    }
    tolerances = {
        "state_rtol": args.state_rtol,
        "state_atol": args.state_atol,
        "image_max_abs": args.image_max_abs,
        "image_mean_abs": args.image_mean_abs,
        "image_mismatch_ratio": args.image_mismatch_ratio,
    }
    local_env = create_environment_adapter(args.local_backend)
    remote_env = RemoteLiberoEnv(args.base_url, timeout=args.timeout)
    try:
        local_created = local_env.create(spec)
        remote_observation, remote_info = remote_env.reset(
            suite=args.suite,
            task_id=args.task_id,
            init_state_id=args.init_state_id,
            seed=args.seed,
            variant="base",
            control_mode=args.control_mode,
            camera_names=spec["camera_names"],
            camera_height=args.camera_height,
            camera_width=args.camera_width,
            max_steps=args.steps,
            observation_schema_version="libero_standard_v1",
        )
        actions = _load_actions(
            args.actions,
            args.steps,
            local_created["action_schema"],
        )
        report = _evaluate(
            health=health,
            local_runtime=collect_runtime_manifest(),
            local_backend=args.local_backend,
            local_env=local_env,
            remote_env=remote_env,
            local_created=local_created,
            remote_observation=remote_observation,
            remote_info=remote_info,
            spec=spec,
            actions=actions,
            tolerances=tolerances,
        )
    finally:
        local_env.close()
        remote_env.close_transport()

    serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    print(serialized)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    if report["status"] != "passed":
        raise SystemExit(1)


def _evaluate(
    *,
    health: Dict[str, Any],
    local_runtime: Dict[str, Any],
    local_backend: str,
    local_env: Any,
    remote_env: RemoteLiberoEnv,
    local_created: Dict[str, Any],
    remote_observation: Dict[str, np.ndarray],
    remote_info: Dict[str, Any],
    spec: Dict[str, Any],
    actions: List[np.ndarray],
    tolerances: Dict[str, float],
) -> Dict[str, Any]:
    protocol = validate_messagepack_roundtrip(remote_observation)
    adapter = validate_xvla_adapter_mapping(remote_observation)
    initial = compare_observations(
        local_created["observation"], remote_observation, **tolerances
    )
    transitions = []
    for index, action in enumerate(actions):
        local_result = local_env.step(action)
        (
            next_remote_observation,
            remote_reward,
            remote_terminated,
            remote_truncated,
            remote_step_info,
        ) = remote_env.step(action, request_id=f"equivalence-step-{index}")
        observation = compare_observations(
            local_result["observation"], next_remote_observation, **tolerances
        )
        outcomes = {
            "reward_equal": bool(
                np.isclose(
                    float(local_result["reward"]),
                    remote_reward,
                    rtol=tolerances["state_rtol"],
                    atol=tolerances["state_atol"],
                )
            ),
            "success_equal": bool(local_result["success"])
            == bool(remote_step_info["success"]),
            "terminated_equal": bool(local_result["terminated"])
            == remote_terminated,
            "truncated_equal": bool(local_result["truncated"]) == remote_truncated,
            "step_index_equal": int(local_result["worker_step_index"])
            == remote_env.next_step_index,
        }
        local_outcome = {
            "reward": float(local_result["reward"]),
            "success": bool(local_result["success"]),
            "terminated": bool(local_result["terminated"]),
            "truncated": bool(local_result["truncated"]),
        }
        remote_outcome = {
            "reward": remote_reward,
            "success": bool(remote_step_info["success"]),
            "terminated": remote_terminated,
            "truncated": remote_truncated,
        }
        transitions.append(
            {
                "action_index": index,
                "local_worker_step_index": int(local_result["worker_step_index"]),
                "remote_step_index": int(remote_step_info["step_index"]),
                "remote_next_step_index": remote_env.next_step_index,
                "local_outcome": local_outcome,
                "remote_outcome": remote_outcome,
                "outcomes": outcomes,
                "observation": observation,
                "passed": observation["passed"] and all(outcomes.values()),
            }
        )
        if (
            local_result["terminated"]
            or local_result["truncated"]
            or remote_terminated
            or remote_truncated
        ):
            break

    environment = {
        "backend_equal": health.get("backend", {}).get("name") == local_backend,
        "language_instruction_equal": local_created["language_instruction"]
        == remote_info.get("language_instruction"),
        "local_action_schema": local_created["action_schema"],
        "remote_action_schema": remote_info.get("action_schema"),
        "action_schema_equal": local_created["action_schema"]
        == remote_info.get("action_schema"),
        "initial_observation": initial,
        "transitions": transitions,
    }
    environment["passed"] = bool(
        environment["backend_equal"]
        and environment["language_instruction_equal"]
        and environment["action_schema_equal"]
        and initial["passed"]
        and len(transitions) == len(actions)
        and all(transition["passed"] for transition in transitions)
    )
    passed = protocol["passed"] and adapter["passed"] and environment["passed"]
    return {
        "equivalence_report_schema_version": REPORT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if passed else "failed",
        "protocol_version": PROTOCOL_VERSION,
        "configuration": {**spec, "tolerances": tolerances},
        "action_sequence": {
            "count": len(actions),
            "float32_c_order_sha256": _actions_sha256(actions),
        },
        "server": health,
        "local_runtime": local_runtime,
        "layers": {
            "messagepack": protocol,
            "xvla_adapter": adapter,
            "environment": environment,
        },
    }


def _load_actions(
    path: Optional[Path], count: int, action_schema: Dict[str, Any]
) -> List[np.ndarray]:
    shape = tuple(int(value) for value in action_schema["shape"])
    if path is None:
        actions = [np.zeros(shape, dtype=np.float32) for _ in range(count)]
    else:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not raw:
            raise ValueError("Action file must contain a non-empty JSON array")
        actions = [np.ascontiguousarray(action, dtype=np.float32) for action in raw]

    low = np.asarray(action_schema["low"], dtype=np.float32)
    high = np.asarray(action_schema["high"], dtype=np.float32)
    for index, action in enumerate(actions):
        if action.shape != shape or not np.isfinite(action).all():
            raise ValueError(f"Action {index} does not match shape {shape}")
        if np.any(action < low) or np.any(action > high):
            raise ValueError(f"Action {index} is outside the action schema bounds")
    return actions


def _actions_sha256(actions: List[np.ndarray]) -> str:
    digest = hashlib.sha256()
    digest.update(len(actions).to_bytes(8, "big"))
    for action in actions:
        contiguous = np.ascontiguousarray(action, dtype=np.float32)
        digest.update(contiguous.size.to_bytes(8, "big"))
        digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _read_health(base_url: str) -> Dict[str, Any]:
    with urlopen(f"{base_url.rstrip('/')}/v1/health", timeout=5.0) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("health response must be a JSON object")
    return payload


if __name__ == "__main__":
    main()
