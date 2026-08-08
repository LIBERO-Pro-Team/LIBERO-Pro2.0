from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import traceback
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENVS_ROOT = ROOT / "libero" / "libero" / "envs"


def _load_local_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ENVS_ROOT / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PERTURBATION_CONFIG = _load_local_module(
    "libero_pro_validation_config", "perturbation_config.py"
)
PERTURBATION_RUNTIME = _load_local_module(
    "libero_pro_validation_runtime", "nonphysical_perturbations.py"
)
ALL_CASE_IDS = PERTURBATION_RUNTIME.ALL_CASE_IDS
build_execution_plan = PERTURBATION_RUNTIME.build_execution_plan
default_asset_root = PERTURBATION_RUNTIME.default_asset_root
parse_bddl_perturbation_config = PERTURBATION_CONFIG.parse_bddl_perturbation_config


def discover_bddls(dataset_root: Path) -> list[Path]:
    return sorted(dataset_root.rglob("*.bddl"))


def validate_static(dataset_root: Path) -> dict[str, object]:
    files = discover_bddls(dataset_root)
    errors: list[str] = []
    case_counts: dict[str, int] = {}
    for path in files:
        try:
            config = parse_bddl_perturbation_config(path)
            plan = build_execution_plan(config, default_asset_root())
            expected = path.name.split("__", 1)[0]
            if plan.case_id != expected:
                raise ValueError(f"filename case {expected} != config case {plan.case_id}")
            case_counts[plan.case_id] = case_counts.get(plan.case_id, 0) + 1
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    expected_cases = {"BASE", *ALL_CASE_IDS}
    if set(case_counts) != expected_cases:
        errors.append(
            f"case coverage mismatch: expected {sorted(expected_cases)}, got {sorted(case_counts)}"
        )
    return {
        "bddl_files": len(files),
        "case_counts": case_counts,
        "errors": errors,
    }


DEFAULT_SUITES = ("libero_spatial", "libero_object", "libero_goal", "libero_10")


def smoke_files(
    dataset_root: Path, case_ids: list[str], suites: list[str]
) -> list[Path]:
    paths = []
    for suite in suites:
        for case_id in case_ids:
            folder = "00_base" if case_id == "BASE" else (
                "01_static" if case_id.startswith("S") else "02_dynamic"
            )
            paths.append(next((dataset_root / suite / folder).glob(f"{case_id}__*.bddl")))
    return paths


def smoke_environment(path: Path, steps: int) -> dict[str, object]:
    # Keep schema and asset validation usable without the MuJoCo / robosuite stack.
    from libero.libero.envs import OffScreenRenderEnv

    env = None
    try:
        env = OffScreenRenderEnv(
            bddl_file_name=str(path),
            use_camera_obs=True,
            camera_names=["agentview", "robot0_eye_in_hand"],
            camera_heights=64,
            camera_widths=64,
        )
        observation = env.reset()
        reset_success = bool(env.check_success())
        case_id = env.env.perturbation_plan.case_id
        plan_assets = [asset.asset_id for asset in env.env.perturbation_plan.assets]
        injected_names = (
            list(env.env.perturbation_asset_injection.injected_names)
            if env.env.perturbation_asset_injection is not None
            else []
        )
        missing_injected = [
            name for name in injected_names if name not in env.env.obj_body_id
        ]
        if missing_injected:
            raise RuntimeError(
                f"Injected assets are absent from the compiled model: {missing_injected}"
            )

        staged_positions = {}
        if case_id.startswith("D"):
            for name in injected_names:
                body_id = int(env.env.obj_body_id[name])
                position = np.asarray(env.env.sim.data.body_xpos[body_id]).copy()
                staged_positions[name] = position.tolist()
                if position[2] > -4.0:
                    raise RuntimeError(
                        f"Dynamic asset {name!r} was not staged outside the workspace: "
                        f"{position.tolist()}"
                    )

        for _ in range(steps):
            action = np.zeros(env.env.action_dim, dtype=np.float64)
            if action.size:
                action[-1] = -1.0
            observation, _, done, info = env.step(action)
            if done:
                break
        diagnostics = env.env.perturbation_runtime.diagnostics()
        if case_id != "BASE" and not diagnostics["events"]:
            raise RuntimeError(
                f"Perturbation {case_id} produced no observable runtime event in {steps} steps"
            )
        return {
            "path": str(path),
            "case_id": case_id,
            "ok": True,
            "success_at_reset": reset_success,
            "assets": plan_assets,
            "injected_objects": injected_names,
            "staged_positions": staged_positions,
            "events": diagnostics["events"],
            "observation_key_count": len(observation),
        }
    except Exception as exc:
        return {
            "path": str(path),
            "case_id": path.name.split("__", 1)[0],
            "ok": False,
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        if env is not None:
            env.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--cases", default="BASE,S06,S12,D04,D14", help="comma-separated case IDs"
    )
    parser.add_argument(
        "--suites",
        default=",".join(DEFAULT_SUITES),
        help="comma-separated suite directory names",
    )
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    report = {"static": validate_static(dataset_root)}
    if args.smoke:
        case_ids = [
            case.strip().upper()
            for case in re.split(r"[,;]", args.cases)
            if case.strip()
        ]
        suites = [
            suite.strip()
            for suite in re.split(r"[,;]", args.suites)
            if suite.strip()
        ]
        unknown_suites = sorted(set(suites) - set(DEFAULT_SUITES))
        if unknown_suites:
            parser.error(f"unsupported suites: {unknown_suites}")
        report["smoke"] = [
            smoke_environment(path, args.steps)
            for path in smoke_files(dataset_root, case_ids, suites)
        ]
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    failed = bool(report["static"]["errors"])
    failed = failed or any(not item["ok"] for item in report.get("smoke", []))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
