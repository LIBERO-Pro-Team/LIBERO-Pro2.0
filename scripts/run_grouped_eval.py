"""Plan, submit, and export grouped LIBERO-Pro evaluation runs."""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from libero_remote import RemoteRunClient
from libero_remote.benchmark import (
    VALID_GROUPS,
    BenchmarkPlan,
    build_benchmark_plan,
    export_benchmark_results,
    save_benchmark_plan,
    submit_benchmark_plan,
)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=os.environ.get("LIBERO_REMOTE_API_KEY"))
    parser.add_argument("--timeout", type=float, default=120.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", help="generate a plan without submitting it")
    _add_selection_arguments(plan_parser)

    submit_parser = subparsers.add_parser("submit", help="generate and submit a grouped run")
    _add_selection_arguments(submit_parser)
    submit_parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for external runners to finish, then export results",
    )
    submit_parser.add_argument("--poll-interval", type=float, default=2.0)

    export_parser = subparsers.add_parser(
        "export", help="export and summarize an existing persisted run"
    )
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def _add_selection_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--group", choices=VALID_GROUPS, default="base")
    parser.add_argument("--suite", dest="suites", action="append")
    parser.add_argument("--case", dest="cases", action="append")
    seed_group = parser.add_mutually_exclusive_group()
    seed_group.add_argument("--seeds", type=int, nargs="+")
    seed_group.add_argument("--seed", type=int)
    parser.add_argument("--num-seeds", type=int, default=1)
    parser.add_argument("--init-state-ids", type=int, nargs="+", default=[0])
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--control-mode", choices=("relative", "absolute"), default="relative")
    parser.add_argument(
        "--camera-names",
        nargs="+",
        default=["agentview", "robot0_eye_in_hand"],
    )
    parser.add_argument("--camera-height", type=int, default=256)
    parser.add_argument("--camera-width", type=int, default=256)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--output-dir", type=Path)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    with RemoteRunClient(
        args.base_url, timeout=args.timeout, api_key=args.api_key
    ) as client:
        if args.command == "export":
            exported = export_benchmark_results(client, args.run_id, args.output_dir)
            print(json.dumps(exported["summary"], indent=2, sort_keys=True))
            return

        catalog = _load_catalog(args.catalog, client)
        output_dir = args.output_dir or _default_output_dir()
        plan = _build_plan(catalog, args)
        plan_path = save_benchmark_plan(plan, output_dir)
        preview = {
            "plan_id": plan.plan_id,
            "group": plan.selection["group"],
            "selected_tasks": plan.selected_task_count,
            "rollouts": plan.rollout_count,
            "plan_path": str(plan_path),
        }
        if args.command == "plan":
            print(json.dumps(preview, indent=2, sort_keys=True))
            return

        submitted = submit_benchmark_plan(client, plan, output_dir)
        preview.update(
            {
                "run_id": submitted["run_id"],
                "status": submitted["status"],
                "output_dir": str(Path(output_dir).expanduser().resolve()),
            }
        )
        print(json.dumps(preview, indent=2, sort_keys=True))
        if args.wait:
            run_id = str(submitted["run_id"])
            _wait_for_terminal_run(client, run_id, args.poll_interval)
            exported = export_benchmark_results(client, run_id, output_dir)
            print(json.dumps(exported["summary"], indent=2, sort_keys=True))


def _build_plan(catalog: Dict[str, Any], args: argparse.Namespace) -> BenchmarkPlan:
    seeds = resolve_seeds(args.seeds, args.seed, args.num_seeds)
    return build_benchmark_plan(
        catalog,
        group=args.group,
        suites=args.suites,
        cases=args.cases,
        seeds=seeds,
        init_state_ids=args.init_state_ids,
        matrix=args.matrix,
        control_mode=args.control_mode,
        camera_names=args.camera_names,
        camera_height=args.camera_height,
        camera_width=args.camera_width,
        max_steps=args.max_steps,
    )


def resolve_seeds(
    seeds: Optional[Sequence[int]], seed: Optional[int], num_seeds: int
) -> List[int]:
    if num_seeds < 1:
        raise ValueError("--num-seeds must be at least 1")
    if seeds is not None:
        if num_seeds != 1:
            raise ValueError("--num-seeds can only be combined with --seed")
        return list(seeds)
    start = 142 if seed is None else seed
    return list(range(start, start + num_seeds))


def _load_catalog(path: Optional[Path], client: RemoteRunClient) -> Dict[str, Any]:
    if path is None:
        return client.get_task_catalog()
    payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("--catalog must contain a JSON object")
    return payload


def _wait_for_terminal_run(
    client: RemoteRunClient, run_id: str, poll_interval: float
) -> Dict[str, Any]:
    if poll_interval <= 0:
        raise ValueError("--poll-interval must be positive")
    while True:
        snapshot = client.get_run(run_id)
        if snapshot["status"] in {"completed", "failed", "cancelled"}:
            return snapshot
        time.sleep(poll_interval)


def _default_output_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("results") / f"grouped_eval_{timestamp}"


if __name__ == "__main__":
    main()
