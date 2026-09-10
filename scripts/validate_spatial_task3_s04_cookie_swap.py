"""Seed-143 rendering and passive-physics audit of the task3 cookie-box swap."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SIMULATOR = ROOT / "simulator-source"
MOVED = ("akita_black_bowl_1", "akita_black_bowl_2", "cookies_1")
OUTPUT = ROOT / "outputs" / "spatial_task3_s04_cookie_swap_seed143_20260910"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    config_dir = output / "libero_config"
    config_dir.mkdir(parents=True, exist_ok=True)
    benchmark = SIMULATOR / "libero" / "libero"
    (config_dir / "config.yaml").write_text(
        "\n".join(f"{key}: {value}" for key, value in {
            "assets": benchmark / "assets", "bddl_files": benchmark / "bddl_files",
            "benchmark_root": benchmark, "datasets": SIMULATOR / "libero" / "datasets",
            "init_states": benchmark / "init_files",
        }.items()) + "\n", encoding="utf-8",
    )
    sys.path[:0] = [str(ROOT), str(SIMULATOR)]
    os.environ["LIBERO_PRO_ROOT"] = str(SIMULATOR)
    os.environ["LIBERO_CONFIG_PATH"] = str(config_dir)
    os.environ["LIBERO_REMOTE_TASK_MANIFEST"] = str(ROOT / "assets" / "task_manifest.json")
    os.environ["MUJOCO_GL"] = "wgl"
    from libero.libero.envs import nonphysical_perturbations as runtime
    from libero_remote.environment.libero import LiberoEnvironmentAdapter

    def unwrap(adapter):
        env = adapter._env
        while not hasattr(env, "obj_body_id"):
            env = env.env
        return env

    def poses(env):
        return {name: runtime._entity_pose(env, name) for name in env.obj_body_id}

    def frame(env, name):
        env._update_observables(force=True)
        rgb = env._get_observations()["agentview_image"][::-1].copy()
        assert float(np.std(rgb)) > 1.0
        assert cv2.imwrite(str(output / f"{name}.png"), rgb[:, :, ::-1])
        return rgb

    def pair_contact(env, first, second):
        first_ids = set(runtime._entity_body_ids(env, first))
        second_ids = set(runtime._entity_body_ids(env, second))
        model, data = env.sim.model, env.sim.data
        for i in range(data.ncon):
            contact = data.contact[i]
            a, b = (int(model.geom_bodyid[g]) for g in (contact.geom1, contact.geom2))
            if ((a in first_ids and b in second_ids) or
                    (b in first_ids and a in second_ids)) and contact.dist <= 0.003:
                return True
        return False

    manifest = json.loads((ROOT / "assets" / "task_manifest.json").read_text(encoding="utf-8"))
    entry = next(i for i in manifest["tasks"] if
                 (i["suite"], i["base_task_id"], i["case_id"]) == ("libero_spatial", 3, "S04"))
    active = ROOT / "assets" / entry["bddl_path"]
    base = active.parent.parent / "00_base" / active.name.replace("S04__", "BASE__")
    digest = hashlib.sha256(active.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert digest == entry["bddl_sha256"]
    calls = []
    original = runtime._single_support_group_swap_transform

    def capture(env, targets, params):
        before = poses(env)
        result = original(env, targets, params)
        after = poses(env)
        unaffected = {
            name: max(float(np.max(np.abs(after[name][0] - pose[0]))),
                      float(np.max(np.abs(after[name][1] - pose[1]))))
            for name, pose in before.items() if name not in MOVED
        }
        calls.append({"event": result, "unaffected_pose_errors": unaffected,
                      "relative_error": float(np.linalg.norm(
                          (after[MOVED[0]][0] - after[MOVED[2]][0]) -
                          (before[MOVED[0]][0] - before[MOVED[2]][0]))),
                      "first_xy_error": float(np.linalg.norm(after[MOVED[0]][0][:2] - before[MOVED[1]][0][:2])),
                      "second_xy_error": float(np.linalg.norm(after[MOVED[1]][0][:2] - before[MOVED[0]][0][:2]))})
        return result

    runtime._single_support_group_swap_transform = capture
    snapshots, images = {}, {}
    for variant, path in (("base", base), ("S04", active)):
        random.seed(143)
        np.random.seed(143)
        adapter = LiberoEnvironmentAdapter()
        try:
            metadata = adapter.create({
                "suite": "libero_spatial", "task_id": 3, "variant": variant,
                "_bddl_path": str(path), "seed": 143, "init_state_id": 0,
                "camera_names": ["agentview"], "camera_height": 512, "camera_width": 512,
                "max_steps": 220,
            })
            env = unwrap(adapter)
            initial = poses(env)
            images[variant] = frame(env, variant + "_first_observation")
            deep, nonfinite = [], []
            for step in range(1001):
                if step % 10 == 0:
                    for name in MOVED:
                        contacts = runtime._entity_deep_contacts(env, name, tolerance=0.002)
                        if contacts:
                            deep.append({"step": step, "object": name, "contacts": contacts})
                    if not np.isfinite(env.sim.data.qpos).all() or not np.isfinite(env.sim.data.qvel).all():
                        nonfinite.append(step)
                if step < 1000:
                    env.sim.step()
            env.sim.forward()
            final = poses(env)
            frame(env, variant + "_settled")
            snapshots[variant] = {
                "language": metadata["language_instruction"],
                "initial": {n: p[0].tolist() for n, p in initial.items()},
                "final": {n: p[0].tolist() for n, p in final.items()},
                "deep_contacts": deep, "nonfinite_steps": nonfinite,
                "target_on_cookie_box": bool(env._eval_predicate(["on", MOVED[0], MOVED[2]])),
                "cookie_box_on_cabinet": bool(env._eval_predicate(["on", MOVED[2], "wooden_cabinet_1_top_side"])),
                "contacts": {
                    "target_box": pair_contact(env, MOVED[0], MOVED[2]),
                    "box_cabinet": pair_contact(env, MOVED[2], "wooden_cabinet_1"),
                    "second_table": pair_contact(env, MOVED[1], "main_table"),
                },
                "free_joints": {
                    name: [int(env.sim.model.jnt_type[env.sim.model.joint_name2id(j)])
                           for j in env.objects_dict[name].joints] for name in MOVED
                },
                "events": env.perturbation_runtime.diagnostics()["events"],
            }
        finally:
            adapter.close()

    active_result = snapshots["S04"]
    unrelated = {
        name: float(np.linalg.norm(np.array(position) - snapshots["base"]["final"][name]))
        for name, position in active_result["final"].items() if name not in MOVED
    }
    checks = {
        "exact_group_swap": bool(calls) and all(
            max(c["relative_error"], c["first_xy_error"], c["second_xy_error"]) < 1e-9 for c in calls),
        "unaffected_at_swap": all(max(c["unaffected_pose_errors"].values(), default=0) < 1e-12 for c in calls),
        "unaffected_after_physics": max(unrelated.values(), default=0) < 0.001,
        "language_unchanged": active_result["language"] == snapshots["base"]["language"],
        "source_semantics_preserved": active_result["target_on_cookie_box"],
        "box_supported_by_cabinet": active_result["cookie_box_on_cabinet"],
        "real_contacts": all(active_result["contacts"].values()),
        "movable_objects": all(types == [0] for types in active_result["free_joints"].values()),
        "no_deep_penetration": not active_result["deep_contacts"],
        "finite_scene": not active_result["nonfinite_steps"],
    }
    report = {"seed": 143, "init_state_id": 0, "policy_rollout": False,
              "passive_physics_steps": 1000, "bddl_sha256": digest,
              "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "swap_calls": calls, "unrelated_final_displacement_m": unrelated,
              "scenes": snapshots}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    comparison = np.hstack([images["base"], images["S04"]])
    assert cv2.imwrite(str(output / "comparison.png"), comparison[:, :, ::-1])
    print(json.dumps({"status": report["status"], "checks": checks,
                      "unrelated_final_displacement_m": unrelated, "output": str(output)}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
