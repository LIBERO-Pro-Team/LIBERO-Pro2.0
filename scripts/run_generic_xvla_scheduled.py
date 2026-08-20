"""Run xVLA through the model-neutral scheduled evaluation interface.

The scheduled runner and recording adapter remain model-neutral.  All xVLA
observation mapping, preprocessing and action conversion live in the explicit
``libero_remote.runner.xvla`` reference adapter.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx

from libero_remote import RemoteRunClient
from libero_remote.runner import run_scheduled_run
from libero_remote.runner.recording import RecordingAgentAdapter, RolloutVideoRecorder
from libero_remote.runner.xvla import XVLAPolicyAdapter


def _http_json(base_url: str, api_key: str, path: str) -> Dict[str, Any]:
    response = httpx.get(
        base_url.rstrip("/") + path,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise TypeError(f"Expected object from {path}, got {type(payload).__name__}")
    return payload


def _load_policy(
    model_path: Path,
    tokenizer_path: Path,
    device: str,
    *,
    output_root: Path,
    fps: int = 20,
) -> RecordingAgentAdapter:
    policy = XVLAPolicyAdapter.load(
        str(Path(model_path).expanduser().resolve()),
        device=device,
        tokenizer_path=str(Path(tokenizer_path).expanduser().resolve()),
        local_files_only=True,
    )
    recorder = RolloutVideoRecorder(
        output_root=Path(output_root),
        image_field="agentview_image",
        fps=fps,
    )
    return RecordingAgentAdapter(policy, recorder)


def _episodes_from_manifest(
    path: Path, seed: int, camera_size: int
) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload["task_count"]) != 1680 or len(payload["tasks"]) != 1680:
        raise ValueError("The local manifest must contain exactly 1680 tasks")
    episodes = []
    for entry in payload["tasks"]:
        case_id = str(entry["case_id"]).upper()
        episodes.append(
            {
                "suite": str(entry["suite"]),
                "task_id": int(entry["base_task_id"]),
                "init_state_id": 0,
                "seed": int(seed),
                "variant": "base" if case_id == "BASE" else case_id,
                "control_mode": "absolute",
                "camera_names": ["agentview", "robot0_eye_in_hand"],
                "camera_height": int(camera_size),
                "camera_width": int(camera_size),
                "max_steps": int(entry.get("max_steps", 300)),
            }
        )
    return episodes


def _write_server_results(output_root: Path, payload: Dict[str, Any]) -> None:
    episodes = payload.get("episodes", [])
    for record in episodes:
        spec = record.get("spec", record.get("episode_spec", record))
        result = record.get("result", {})
        suite = str(spec.get("suite", result.get("suite", record.get("suite"))))
        case = str(
            spec.get("variant", result.get("variant", record.get("variant", "base")))
        ).upper()
        case = "BASE" if case == "BASE" else case
        seed = int(spec.get("seed", result.get("seed", record.get("seed", 142))))
        directory = output_root / suite / case / f"seed_{seed}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "result.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--tokenizer-path", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--runner-id", default="generic-xvla-gpu0")
    parser.add_argument("--seed", type=int, default=142)
    parser.add_argument("--camera-size", type=int, default=360)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    model_path = Path(args.model_path).expanduser().resolve()
    tokenizer_path = Path(args.tokenizer_path).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    health = _http_json(args.base_url, args.api_key, "/v1/health")
    catalog = _http_json(args.base_url, args.api_key, "/v1/tasks")
    if int(catalog.get("task_count", -1)) != 1680:
        raise RuntimeError(
            f"Server catalog is not the 1680-task release: {catalog.get('task_count')}"
        )
    episodes = _episodes_from_manifest(manifest_path, args.seed, args.camera_size)
    if args.limit:
        episodes = episodes[: args.limit]

    started = time.perf_counter()
    adapter = _load_policy(
        model_path,
        tokenizer_path,
        args.device,
        output_root=output_root,
    )
    with RemoteRunClient(args.base_url, api_key=args.api_key, timeout=120) as client:
        run_id = args.run_id
        if not run_id:
            run_id = client.submit_run(episodes)["run_id"]
        snapshot = run_scheduled_run(
            client,
            run_id=run_id,
            runner_id=args.runner_id,
            adapter=adapter,
            poll_interval_seconds=1.0,
        )
        records = client.get_episodes(run_id)

    _write_server_results(output_root, records)
    summary = {
        "kind": "generic_xvla_scheduled",
        "run_id": run_id,
        "task_count": len(episodes),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "server_health": health,
        "server_catalog": {
            "task_manifest_version": catalog.get("task_manifest_version"),
            "task_manifest_sha256": catalog.get("task_manifest_sha256"),
            "task_count": catalog.get("task_count"),
        },
        "server_run": snapshot,
        "episode_records": records,
    }
    (output_root / "batch_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "run_id": run_id,
                "task_count": len(episodes),
                "output_root": str(output_root),
            },
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
