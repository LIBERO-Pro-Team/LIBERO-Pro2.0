"""Apply task-local fixes selected from the human feedback ledger.

This script deliberately scopes every edit to a ``suite/task/case`` key that
exists in ``待修改.md``.  Runtime defaults remain untouched; values here are
task-level overrides for the cases that received feedback.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path(r"C:\Users\racin\Desktop\待修改.md")
MANIFEST = ROOT / "assets" / "task_manifest.json"


def group_end(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unclosed BDDL group")


def case_slice(text: str, case_id: str) -> tuple[int, int, str]:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"missing case {case_id}")
    end = group_end(text, match.start())
    return match.start(), end, text[match.start() : end]


def replace_field(block: str, field: str, atoms: tuple[str, ...], *, params: bool) -> str:
    scope = block
    if params:
        match = re.search(r"\(\s*:params\b", block)
        if not match:
            raise ValueError("case has no params group")
        start = match.start()
        end = group_end(block, start)
        scope = block[start:end]
        prefix = block[:start]
        suffix = block[end:]
    else:
        prefix, suffix = "", ""
    replacement = f"(:{field} {' '.join(atoms)})"
    match = re.search(rf"\(\s*:{re.escape(field)}\b[^)]*\)", scope)
    if match:
        scope = scope[: match.start()] + replacement + scope[match.end() :]
    else:
        insertion = scope.rfind(")")
        scope = scope[:insertion].rstrip() + f"\n          {replacement}\n        " + scope[insertion:]
    return prefix + scope + suffix


def update_case(
    text: str,
    case_id: str,
    params: dict[str, tuple[str, ...]] | None = None,
    fields: dict[str, tuple[str, ...]] | None = None,
) -> str:
    start, end, block = case_slice(text, case_id)
    for field, atoms in (fields or {}).items():
        block = replace_field(block, field, atoms, params=False)
    for field, atoms in (params or {}).items():
        block = replace_field(block, field, atoms, params=True)
    return text[:start] + block + text[end:]


def review_keys() -> set[tuple[str, int, str]]:
    with REVIEW.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row["suite"], int(row["task_id"]), row["扰动"].upper())
            for row in csv.DictReader(handle, delimiter="\t")
            if row["扰动"].upper() != "BASE"
        }


def task_params(suite: str, task_id: int, case_id: str) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    params: dict[str, tuple[str, ...]] = {}
    fields: dict[str, tuple[str, ...]] = {}

    if case_id == "D01":
        params.update(trigger_distance_m=("0.17",), offset_xy=("0.10", "-0.08"), yaw_rad=("0.28",))
    elif case_id == "D02":
        # Keep the previously validated receiver displacement.  It is larger
        # than the old weak value and avoids the basket/rack-specific collision
        # direction used by the task-safe runtime fallback.
        params.update(offset_xy=("-0.12", "0.09"), yaw_rad=("-0.24",))
        if suite == "libero_10" and task_id == 2:
            # Trigger while the moka pot is still approaching the stove so a
            # successful placement cannot end the episode first.
            params["receiver_trigger_distance_m"] = ("0.24",)
    elif case_id == "D03":
        # The finalization pass owns the complete persistent D03 contract.
        # Do not reintroduce the obsolete temporary-obstacle duration here.
        pass
    elif case_id == "D04":
        params.update(
            event_duration_steps=("50",),
            occlusion_fraction=("0.72",),
            occlusion_offset_xyz=("0.0", "0.0", "0.02"),
            asset_scale=("1.15",),
        )
        if suite == "libero_goal" and task_id == 3:
            # This cabinet path already has a validated 1.25x screen that
            # clears the drawer geometry; retain it while extending duration.
            params["asset_scale"] = ("1.25",)
    elif case_id == "D05":
        params.update(
            lateral_offset_m=("0.075",),
            barrier_height_m=("0.05",),
            asset_scale=("1.10",),
            visual_only_asset=("false",),
            physical_collision=("true",),
        )
        if suite == "libero_10" and task_id == 2:
            params["lateral_offset_m"] = ("0.105",)
        if suite == "libero_goal" and task_id in {5, 8}:
            params["lateral_offset_m"] = ("0.11",)
        if suite == "libero_object" and task_id == 0:
            params.update(
                lateral_offset_m=("0.0",),
                barrier_height_m=("0.08",),
                asset_scale=("1.35",),
                visual_only_asset=("false",),
                physical_collision=("true",),
            )
    elif case_id == "D06":
        params.update(minimum_clearance_m=("0.16",))
        if suite == "libero_10" and task_id == 8:
            params.update(
                asset_id=("libero/red_coffee_mug",),
                asset_scale=("1.0",),
                asset_initial_anchor=("moka_pot_2",),
                asset_initial_offset_xy=("0.134437", "0.194625"),
                asset_initial_clearance_m=("0.10",),
                support_surface=("kitchen_table",),
                minimum_clearance_m=("0.10",),
                minimum_displacement_m=("0.10",),
                offset_xy=("0.12", "-0.09"),
            )
            fields["disturbance_targets"] = ("none",)
        if suite == "libero_goal" and task_id in {1, 3, 4, 6, 8}:
            params["minimum_clearance_m"] = ("0.20",)
        if suite == "libero_object" and task_id == 6:
            params["minimum_clearance_m"] = ("0.20",)
        if suite == "libero_spatial" and task_id in {3, 4, 7}:
            fields["disturbance_targets"] = (
                "cookies_1",
                "glazed_rim_porcelain_ramekin_1",
            )
    elif case_id == "D08":
        params["event_duration_steps"] = ("50",)
    elif case_id == "D09":
        params.update(event_duration_steps=("50",), lighting_factor=("0.38",))
    elif case_id == "D10":
        params.update(event_duration_steps=("36",), dropout_mode=("zero",))
    elif case_id == "D11":
        params.update(
            event_duration_steps=("36",),
            freeze_modalities=("rgb",),
        )
    elif case_id == "D12":
        params.update(delay_steps=("10",), event_duration_steps=("36",))
    elif case_id == "D13":
        params.update(
            arm_delay_steps=("8",),
            gripper_delay_steps=("8",),
            event_duration_steps=("36",),
        )
    elif case_id == "D14":
        params.update(drop_count=("2",), repeat_count=("8",), event_duration_steps=("8",))
    elif case_id == "D15":
        params.update(chunk_size=("12",), stale_chunk_steps=("8",), event_duration_steps=("8",))
    elif case_id == "D16":
        params.update(takeover_action=("0.18", "-0.08"), takeover_duration_steps=("12",))
        if suite == "libero_object" and task_id == 1:
            params["takeover_action"] = ("-0.18", "0.08")
    elif case_id == "D18":
        params.update(offset_xy=("-0.08", "0.06"), minimum_clearance_m=("0.12",))
    elif case_id == "D19":
        params.update(
            event_duration_steps=("24",),
            misplace_minimum_gap_m=("0.08",),
            preserve_support_z=("true",),
        )
    elif case_id == "D20":
        if suite == "libero_10" and task_id in {0, 1, 3}:
            params.update(
                trigger_eef_motion_m=("0.01",),
                trigger_action_norm=("0.01",),
            )
    elif case_id == "S01":
        params.update(offset_xy=("0.055", "0.035"), yaw_rad=("0.28",))
    elif case_id == "S02":
        params.update(offset_xy=("-0.065", "0.045"), yaw_rad=("-0.24",))
    elif case_id == "S04":
        params["swap_xy"] = ("0.0", "0.0")
        params["grounded_swap"] = ("true",)
        params["ground_support_from_declared_surface"] = ("true",)
        params["swap_cluster_radius_m"] = ("0.18",)
        params["support_surface"] = ("table",)
        if (suite, task_id) == ("libero_spatial", 5):
            params["preserve_swapped_support_heights"] = ("true",)
        if (suite, task_id) in {
            ("libero_10", 7),
            ("libero_10", 8),
            ("libero_10", 9),
        }:
            params.pop("swap_cluster_radius_m")
            params["strict_swap_xy"] = ("true",)
        elif (suite, task_id) == ("libero_goal", 0) or (suite, task_id) == ("libero_goal", 7):
            fields["targets"] = (
                ("wine_bottle_1", "cream_cheese_1")
                if task_id == 0
                else ("flat_stove_1", "cream_cheese_1")
            )
        elif (suite, task_id) == ("libero_10", 8):
            params["swap_xy"] = ("0.06", "0.0")
    elif case_id == "S05":
        params.update(lateral_offset_m=("0.055",), barrier_height_m=("-0.015",), visual_only_asset=("true",))
        if suite == "libero_object" and task_id == 0:
            params = {
                "barrier_scale": ("1.35",),
                "barrier_path_fraction": ("0.50",),
                "barrier_lateral_offset_m": ("-0.07",),
                "visual_only_asset": ("false",),
            }
        elif suite == "libero_10" and task_id == 0:
            params = {
                "barrier_scale": ("1.15",),
                "barrier_path_fraction": ("0.50",),
                "barrier_lateral_offset_m": ("0.04",),
                "visual_only_asset": ("false",),
            }
    elif case_id == "S06":
        params["asset_quat"] = ("1.0", "0.0", "0.0", "0.0")
        if suite == "libero_goal" and task_id in {2, 6, 9}:
            params["asset_scale"] = ("0.58",)
        elif suite == "libero_goal":
            params["asset_scale"] = ("0.38",)
        elif suite == "libero_spatial":
            params["asset_scale"] = ("0.26",)
        elif suite == "libero_10" and task_id in {6, 7, 9}:
            params["asset_scale"] = ("0.58",)
        elif suite == "libero_10":
            # Preserve the already-published task-local scale for other
            # LIBERO-10 S06 tasks when this fixer is rerun.
            params.pop("asset_scale", None)
        elif suite == "libero_object" and task_id == 9:
            params.update(
                asset_id=("prl/cracker_box",),
                asset_scale=("0.7",),
                sampler_compatible=("true",),
                grounded_replacement=("true",),
                support_surface=("floor",),
            )
        else:
            params["asset_scale"] = ("0.58",)
    elif case_id == "S08":
        params["geometry_factors"] = ("1.18", "1.18", "0.82")
        if suite == "libero_goal" and task_id == 7:
            fields["targets"] = ("flat_stove_1",)
        elif suite == "libero_goal" and task_id == 9:
            params["geometry_factors"] = ("1.28", "1.28", "0.72")
        elif suite == "libero_spatial" and task_id == 1:
            params["geometry_factors"] = ("1.08", "1.08", "0.88")
    elif case_id == "S09":
        params.update(
            target_geometry_factors=("1.20", "1.20", "1.20"),
            receiver_geometry_factors=("0.80", "0.80", "0.80"),
        )
    elif case_id == "S10":
        params.update(
            asset_count=("2",),
            clutter_minimum_gap_m=("0.055",),
            support_surface=("table",),
            clutter_offsets_xy=("0.09", "-0.08", "-0.09", "-0.08"),
        )
        if suite == "libero_object":
            params["asset_count"] = ("3",)
            params["clutter_offsets_xy"] = (
                "0.11", "-0.10", "0.11", "0.10", "-0.11", "0.10"
            )
        if suite == "libero_goal":
            params["clutter_offsets_xy"] = ("0.08", "-0.07", "-0.08", "-0.07")
        if suite == "libero_spatial":
            params["clutter_offsets_xy"] = ("0.075", "-0.065", "-0.075", "-0.065")
    elif case_id == "S11":
        params.update(
            asset_count=("1",),
            clutter_minimum_gap_m=("0.055",),
            support_surface=("table",),
            asset_scale=("0.30",),
            clutter_offsets_xy=("0.075", "0.055"),
        )
        if suite == "libero_goal" and task_id == 0:
            fields.update(
                targets=("wooden_cabinet_1",), references=("wooden_cabinet_1",)
            )
            params.update(
                asset_id=("libero/yellow_cabinet",),
                asset_scale=("1.0",),
                asset_count=("1",),
                asset_quat=("1.0", "0.0", "0.0", "0.0"),
                weld_asset_joints=("true",),
                clutter_minimum_gap_m=("0.080",),
                clutter_offsets_xy=("-0.067791", "0.639295"),
                support_surface=("main_table",),
                clear_of_task_entities=("true",),
            )
        elif suite == "libero_10" and task_id == 6:
            params["asset_count"] = ("2",)
            params["clutter_offsets_xy"] = ("0.075", "0.055", "-0.075", "0.055")
    elif case_id == "S12":
        params.update(asset_scale=("1.20",), occlusion_fraction=("0.72",))
    elif case_id == "S20":
        params["delay_steps"] = ("7",)
    elif case_id == "S03":
        params["height_delta_m"] = ("0.10",)
    elif case_id == "S18":
        params.update(
            eef_offset_xyz=("0.050", "-0.040", "0.030"),
            joint_zero_offset_rad=("0.050", "-0.040", "0.030"),
            grasp_center_offset_xyz=("0.0", "0.0", "0.0"),
        )
    return params, fields


def sync_hashes(paths: list[Path]) -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        pattern = (
            rf'("bddl_path"\s*:\s*"{re.escape(relative)}"\s*,\s*\n'
            rf'\s*"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        )
        manifest, count = re.subn(
            pattern, lambda match, value=digest: match.group(1) + value + match.group(2), manifest, count=1
        )
        if count != 1:
            raise ValueError(f"manifest entry missing for {relative}")
    MANIFEST.write_text(manifest, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    paths = {
        (item["suite"], int(item["base_task_id"]), item["case_id"]): ROOT / "assets" / item["bddl_path"]
        for item in manifest["tasks"]
    }
    changed: list[Path] = []
    changes: list[dict[str, object]] = []
    for key in sorted(review_keys()):
        path = paths[key]
        original = path.read_text(encoding="utf-8")
        params, fields = task_params(*key)
        updated = update_case(original, key[2], params, fields)
        if updated == original:
            continue
        changed.append(path)
        changes.append({"suite": key[0], "task_id": key[1], "case_id": key[2], "bddl": str(path.relative_to(ROOT)), "params": params, "fields": fields})
        if not args.check_only:
            path.write_text(updated, encoding="utf-8", newline="\n")
    if changed and not args.check_only:
        sync_hashes(changed)
    payload = {"feedback_keys": len(review_keys()), "changed": len(changed), "changes": changes}
    if args.report and not args.check_only:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
