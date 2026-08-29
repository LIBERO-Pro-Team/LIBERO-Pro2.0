"""Apply the explicit weak-perturbation fixes from ``libero-goal.csv``.

This is intentionally scoped to the 10 ``libero_goal`` base tasks.  The
review's pixel/encoding observations are excluded: every key below has an
explicit request that the perturbation be larger, longer, visible, or reliably
triggered.  Re-running the tool is idempotent and refreshes only the hashes of
the BDDL files it owns.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1" / "libero_goal"
MANIFEST = ROOT / "assets" / "task_manifest.json"

TASKS = (
    "open_the_middle_drawer_of_the_cabinet",
    "put_the_bowl_on_the_stove",
    "put_the_wine_bottle_on_top_of_the_cabinet",
    "open_the_top_drawer_and_put_the_bowl_inside",
    "put_the_bowl_on_top_of_the_cabinet",
    "push_the_plate_to_the_front_of_the_stove",
    "put_the_cream_cheese_in_the_bowl",
    "turn_on_the_stove",
    "put_the_bowl_on_the_plate",
    "put_the_wine_bottle_on_the_rack",
)

# Keys with an explicit weak, invisible, short-duration, or missed-trigger
# finding in the reviewed CSV.  D11, D13, D18, D19, and D21 were deliberately
# excluded: their feedback is video/log evidence or a hard safety issue rather
# than a request to amplify the perturbation.
WEAK_TASKS: dict[str, tuple[int, ...]] = {
    "D01": (0, 9),
    "D04": (0, 2, 3, 7),
    "D05": (0, 5),
    "D06": tuple(range(10)),
    "D07": tuple(range(10)),
    "D08": (0, 2),
    "D09": (0, 1, 2),
    "D10": (0,),
    "D12": tuple(range(10)),
    "D14": (0, 1),
    "D15": (0, 1),
    "D16": (0, 3, 4, 6, 9),
    "D17": (2, 7),
    "S03": (0, 1, 2, 4, 7),
    "S04": (0, 7),
    "S05": (7,),
    "S06": (0, 4, 7),
    "S08": (0, 2, 3, 7),
    "S09": tuple(range(9)),
    "S10": (0, 1, 4, 5),
    "S15": tuple(range(10)),
    "S16": tuple(range(10)),
    "S17": tuple(range(10)),
    "S18": tuple(range(10)),
}

# These CSV findings require a safer geometry or anchor rather than a larger
# perturbation. They remain separate from the explicit weak-effect ledger.
HARD_SAFETY_TASKS: dict[str, tuple[int, ...]] = {
    "D05": (1, 2, 3, 4, 8),
}

# Existing hard-event regressions remain in the dynamic renderer even though
# they are not weak-effect findings from the current CSV.
LEGACY_DYNAMIC_SAFETY_TASKS: dict[str, tuple[int, ...]] = {
    "D18": (0,),
    "D19": (1, 2, 4, 5, 8),
}


def dynamic_validation_cases() -> tuple[tuple[int, str], ...]:
    pairs = {
        (task_id, case_id)
        for ledger in (
            WEAK_TASKS,
            HARD_SAFETY_TASKS,
            LEGACY_DYNAMIC_SAFETY_TASKS,
        )
        for case_id, task_ids in ledger.items()
        if case_id.startswith("D")
        for task_id in task_ids
    }
    return tuple(sorted(pairs, key=lambda item: (item[1], item[0])))


def group_end(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError(f"Unclosed BDDL group at offset {start}")


def update_case(
    text: str, case_id: str, values: dict[str, tuple[str, ...]]
) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    case_end = group_end(text, match.start())
    case_text = text[match.start() : case_end]
    params_match = re.search(r"\(\s*:params\b", case_text)
    if not params_match:
        raise ValueError(f"Case {case_id} has no :params group")
    params_start = params_match.start()
    params_end = group_end(case_text, params_start)
    params_text = case_text[params_start:params_end]
    for key, atoms in values.items():
        field = f"(:{key} {' '.join(atoms)})"
        field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", params_text)
        if field_match:
            params_text = (
                params_text[: field_match.start()]
                + field
                + params_text[field_match.end() :]
            )
        else:
            insertion = params_text.rfind(")")
            params_text = (
                params_text[:insertion].rstrip()
                + f"\n          {field}\n        "
                + params_text[insertion:].lstrip()
            )
    # Older runs appended fields before the closing paren without preserving its
    # indentation. Normalize only simple BDDL parameter fields owned here.
    params_text = re.sub(r"\n[ \t]+\n(?=[ \t]*\(:)", "\n", params_text)
    params_text = re.sub(
        r"(\(:[^\s()]+(?:\s+[^()]*)?\))\)", r"\1\n        )", params_text
    )
    case_text = case_text[:params_start] + params_text + case_text[params_end:]
    return text[: match.start()] + case_text + text[case_end:]


def replace_case_field(
    text: str, case_id: str, key: str, atoms: tuple[str, ...]
) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    end = group_end(text, match.start())
    block = text[match.start() : end]
    field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", block)
    if not field_match:
        raise ValueError(f"Missing {case_id} field {key}")
    field = f"(:{key} {' '.join(atoms)})"
    block = block[: field_match.start()] + field + block[field_match.end() :]
    return text[: match.start()] + block + text[end:]


def replace_declaration(text: str, source: str, replacement: str) -> str:
    if replacement in text:
        return text
    if source not in text:
        raise ValueError(f"Missing declaration {source!r}")
    return text.replace(source, replacement, 1)


def overrides(task_id: int, case_id: str) -> dict[str, tuple[str, ...]]:
    common: dict[str, dict[str, tuple[str, ...]]] = {
        "D06": {
            "trigger_distance_m": ("0.22",),
            "offset_xy": ("0.18", "-0.14"),
            "secondary_offset_xy": ("-0.17", "0.15"),
            "tertiary_offset_xy": ("0.14", "0.19"),
        },
        "D07": {
            "trigger_distance_m": ("0.22",),
            "camera_offset_m": ("0.08", "-0.065", "0.045"),
        },
        "D08": {"event_duration_steps": ("72",)},
        "D09": {"event_duration_steps": ("72",), "lighting_factor": ("0.25",)},
        "D10": {"event_duration_steps": ("72",)},
        "D12": {
            "trigger_distance_m": ("0.22",),
            "event_duration_steps": ("72",),
            "observation_delay_steps": ("12",),
            "delay_steps": ("10",),
        },
        "D14": {
            "trigger_distance_m": ("0.22",),
            "event_duration_steps": ("8",),
            "repeat_count": ("8",),
        },
        "D15": {
            "trigger_distance_m": ("0.22",),
            "chunk_size": ("12",),
            "stale_chunk_steps": ("8",),
        },
        "D16": {
            "trigger_distance_m": ("0.22",),
            "event_duration_steps": ("16",),
            "takeover_action_value": ("0.26",),
        },
        "S03": {
            "height_delta_m": ("0.10",),
            "asset_scale": ("1.0",),
            "asset_geometry_factors": ("0.75", "0.75", "2.0"),
        },
        "S09": {
            "target_geometry_factors": ("1.20", "1.20", "1.20"),
            "receiver_geometry_factors": ("0.80", "0.80", "0.80"),
        },
        "S10": {
            "asset_scale": ("1.80",),
            "clutter_radius_m": ("0.16",),
            "clutter_minimum_gap_m": ("0.10",),
        },
        "S15": {"camera_offset_m": ("0.10", "-0.08", "0.055")},
        "S16": {"fov_scale": ("1.30",), "image_shift_fraction": ("0.14",)},
        "S17": {
            "joint_offset": ("0.09", "-0.07", "0.05", "0", "0", "0", "0")
        },
        "S18": {
            "eef_offset_xyz": ("0.050", "-0.040", "0.030"),
            "joint_zero_offset_rad": ("0.050", "-0.040", "0.030"),
            "grasp_center_offset_xyz": ("0.0", "0.0", "0.0"),
        },
    }
    values = dict(common.get(case_id, {}))
    if case_id == "D01":
        values.update({"approach_trigger_distance_m": ("0.20",), "joint_offset": ("-0.06",)})
    elif case_id == "D04":
        values.update({"trigger_distance_m": ("0.22",), "event_duration_steps": ("72",)})
        if task_id == 0:
            values["occlusion_part"] = ("handle",)
        elif task_id == 7:
            values["occlusion_part"] = ("button",)
    elif case_id == "D05":
        values.update(
            {
                "event_duration_steps": ("72",),
                "visual_only_asset": ("false",),
                "physical_collision": ("true",),
            }
        )
        if task_id == 0:
            values.update(
                {
                    "asset_scale": ("0.85",),
                    "obstacle_part": ("handle",),
                    "articulation_obstacle_offset_xy": ("0.0", "-0.14"),
                }
            )
        else:
            scale, lateral = {
                1: ("0.75", "0.08"),
                2: ("0.65", "0.08"),
                3: ("0.65", "0.08"),
                4: ("0.75", "0.08"),
                5: ("1.10", "0.06"),
                8: ("0.65", "0.08"),
            }[task_id]
            values.update({"asset_scale": (scale,), "lateral_offset_m": (lateral,)})
    elif case_id == "D17":
        values.update(
            {
                "grasp_trigger_distance_m": ("0.20",),
                "event_duration_steps": ("48",),
                "recovery_retreat_m": ("0.07",),
            }
        )
    elif case_id == "S04":
        values.update({"layout_offset_xy": ("0.20", "0.14")})
    elif case_id == "S05":
        values.update(
            {
                "asset_scale": ("1.10",),
                "obstacle_part": ("button",),
                "articulation_obstacle_offset_xy": ("0.0", "-0.14"),
            }
        )
    elif case_id == "S06":
        if task_id == 0:
            values.update(
                {
                    "fixture_variant": ("true",),
                    "geometry_factors": ("1.10", "0.92", "1.05"),
                }
            )
        elif task_id == 4:
            values.update(
                {
                    "asset_id": ("libero/red_akita_black_bowl",),
                    "asset_scale": ("1.0",),
                }
            )
        else:
            values.update(
                {
                    "fixture_variant": ("true",),
                    "geometry_factors": ("1.10", "0.90", "1.0"),
                }
            )
    elif case_id == "S08":
        values.update(
            {
                "geometry_factors": {
                    0: ("1.50", "0.62", "1.10"),
                    2: ("1.35", "1.35", "0.70"),
                    3: ("1.45", "0.68", "1.12"),
                    7: ("1.30", "0.76", "1.0"),
                }[task_id]
            }
        )
    return values


def apply_structural_fixes(text: str, task_id: int, case_id: str) -> str:
    if case_id == "D15":
        text = replace_case_field(text, case_id, "trigger", ("task_phase",))
    if (task_id, case_id) == (0, "S04"):
        text = replace_case_field(text, case_id, "targets", ("wine_bottle_1", "cream_cheese_1"))
        text = update_case(text, case_id, {"interaction_mode": ("placement",)})
    elif (task_id, case_id) == (7, "S04"):
        text = replace_case_field(
            text, case_id, "targets", ("flat_stove_1", "cream_cheese_1")
        )
        text = update_case(
            text,
            case_id,
            {"interaction_mode": ("placement",), "allow_fixture_swap": ("true",)},
        )
    elif (task_id, case_id) == (0, "S06"):
        text = replace_case_field(text, case_id, "targets", ("wooden_cabinet_1",))
        text = replace_declaration(
            text,
            "wooden_cabinet_1 - wooden_cabinet",
            "wooden_cabinet_1 - yellow_cabinet",
        )
    elif (task_id, case_id) == (7, "S06"):
        text = replace_case_field(text, case_id, "targets", ("flat_stove_1",))
        text = replace_declaration(
            text, "flat_stove_1 - flat_stove", "flat_stove_1 - yellow_stove"
        )
    elif (task_id, case_id) == (7, "S08"):
        text = replace_case_field(text, case_id, "targets", ("flat_stove_1",))
    return text


def bddl_path(task_id: int, case_id: str) -> Path:
    directory = "01_static" if case_id.startswith("S") else "02_dynamic"
    path = BDDL_ROOT / directory / f"{case_id}__{TASKS[task_id]}.bddl"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def sync_manifest_hashes(paths: list[Path]) -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        pattern = (
            rf'("bddl_path"\s*:\s*"{re.escape(relative)}"\s*,\s*\n\s*'
            rf'"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        )
        manifest, count = re.subn(
            pattern,
            lambda match, value=digest: match.group(1) + value + match.group(2),
            manifest,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Missing manifest entry for {relative}")
    MANIFEST.write_text(manifest, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    changed: list[Path] = []
    reviewed_cases = {
        (task_id, case_id)
        for case_id, task_ids in WEAK_TASKS.items()
        for task_id in task_ids
    } | {
        (task_id, case_id)
        for case_id, task_ids in HARD_SAFETY_TASKS.items()
        for task_id in task_ids
    }
    for task_id, case_id in sorted(reviewed_cases, key=lambda item: (item[1], item[0])):
            path = bddl_path(task_id, case_id)
            original = path.read_text(encoding="utf-8")
            updated = apply_structural_fixes(original, task_id, case_id)
            updated = update_case(updated, case_id, overrides(task_id, case_id))
            if updated != original:
                changed.append(path)
                if not args.check_only:
                    path.write_text(updated, encoding="utf-8", newline="\n")
    if changed and not args.check_only:
        sync_manifest_hashes(changed)
    print(
        {
            "reviewed_weak_task_cases": sum(len(ids) for ids in WEAK_TASKS.values()),
            "reviewed_safety_task_cases": sum(
                len(ids) for ids in HARD_SAFETY_TASKS.values()
            ),
            "changed": len(changed),
            "paths": [str(path.relative_to(ROOT)) for path in changed],
        }
    )


if __name__ == "__main__":
    main()
