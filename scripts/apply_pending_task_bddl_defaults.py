"""Write baseline-equivalent runtime parameters to reviewed task BDDLs.

The review ledger selects the task/case keys.  Values here are the defaults
already used by ``nonphysical_perturbations.py``; this script does not amplify
or otherwise tune the feedback cases.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
MANIFEST = ROOT / "assets" / "task_manifest.json"
REVIEW = Path(r"C:\Users\racin\Desktop\待修改.md")

TARGET_CASES = {
    "S15",
    "S16",
    "S17",
    "S18",
    "S20",
    "D07",
    "D12",
    "D13",
    "D14",
    "D16",
    "D19",
    "D21",
}


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


def case_block(text: str, case_id: str) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    return text[match.start() : group_end(text, match.start())]


def update_case_params(
    text: str, case_id: str, values: dict[str, tuple[str, ...]]
) -> str:
    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    end = group_end(text, match.start())
    case_text = text[match.start() : end]
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
            continue
        insertion = params_text.rfind(")")
        params_text = (
            params_text[:insertion].rstrip()
            + f"\n          {field}\n        "
            + params_text[insertion:]
        )
    params_prefix = case_text[:params_start]
    line_start = params_prefix.rfind("\n") + 1
    params_prefix = params_prefix[:line_start] + "        "
    case_text = params_prefix + params_text + case_text[params_end:]
    return text[: match.start()] + case_text + text[end:]


def normalize_case_params(text: str, case_id: str) -> str:
    """Keep inserted params in the same line-oriented shape as generated BDDL."""

    match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if not match:
        raise ValueError(f"Missing perturbation case {case_id}")
    end = group_end(text, match.start())
    case_text = text[match.start() : end]
    params_match = re.search(r"\(\s*:params\b", case_text)
    if not params_match:
        raise ValueError(f"Case {case_id} has no :params group")
    params_start = params_match.start()
    params_end = group_end(case_text, params_start)
    params_text = case_text[params_start:params_end]
    params_text = re.sub(r"\n[ \t]*\n[ \t]*(?=\(:)", "\n          ", params_text)
    params_lines = params_text.splitlines()
    if params_lines:
        params_lines[0] = params_lines[0].lstrip()
    for index in range(1, len(params_lines)):
        if params_lines[index].startswith("(:"):
            params_lines[index] = "          " + params_lines[index]
    params_text = "\n".join(params_lines)
    params_text = re.sub(r"(\(:[^\n()]+\))\)", r"\1\n        )", params_text)
    case_text = case_text[:params_start] + params_text + case_text[params_end:]
    return text[: match.start()] + case_text + text[end:]


def review_keys() -> set[tuple[str, int, str]]:
    with REVIEW.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row["suite"], int(row["task_id"]), row["扰动"].upper())
            for row in csv.DictReader(handle, delimiter="\t")
            if row["扰动"].upper() in TARGET_CASES
        }


def parameterization_keys() -> set[tuple[str, int, str]]:
    """Include every S18/D19 task so Runtime no longer owns their defaults."""

    keys = review_keys()
    keys.update(
        key for key in manifest_paths() if key[2] in {"S18", "D19"}
    )
    return keys


def manifest_paths() -> dict[tuple[str, int, str], Path]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (item["suite"], int(item["base_task_id"]), item["case_id"]): ROOT
        / "assets"
        / item["bddl_path"]
        for item in payload["tasks"]
    }


def defaults(case_id: str, text: str) -> dict[str, tuple[str, ...]]:
    """Return only baseline-equivalent fields absent from a case's params."""

    values: dict[str, dict[str, tuple[str, ...]]] = {
        "S15": {
            "camera_offset_xyz": ("0.045", "-0.035", "0.025"),
            "camera_rotation_rpy": ("0.0", "0.0", "0.0"),
        },
        "S16": {
            "fov_scale": ("1.12",),
            "image_shift_xy": ("0.05", "-0.05"),
            "crop_ratio": ("0.0",),
            "distortion_strength": ("0.0",),
        },
        "S17": {
            "joint_offset_rad": (
                "0.035",
                "-0.025",
                "0.020",
                "0.0",
                "0.0",
                "0.0",
                "0.0",
            ),
        },
        "S18": {
            "eef_offset_xyz": ("0.006", "-0.004", "0.003"),
            "joint_zero_offset_rad": ("0.006", "-0.004", "0.003"),
            "grasp_center_offset_xyz": ("0.0", "0.0", "0.0"),
        },
        "S20": {"delay_steps": ("1",)},
        "D07": {
            "camera_offset_xyz": ("0.025", "-0.018", "0.012"),
            "camera_rotation_rpy": ("0.0", "0.0", "0.0"),
            "event_duration_steps": ("24",),
        },
        "D12": {"delay_steps": ("2",), "event_duration_steps": ("24",)},
        "D13": {
            "arm_delay_steps": ("1",),
            "gripper_delay_steps": ("0",),
            "event_duration_steps": ("24",),
        },
        "D14": {
            "drop_count": ("1",),
            "repeat_count": ("8",),
            "event_duration_steps": ("8",),
        },
        "D16": {
            "takeover_action": ("0.12",),
            "takeover_duration_steps": ("6",),
        },
        "D19": {
            "misplace_offset_xy": ("0.065", "0.0"),
            "misplace_height_m": ("0.035",),
            "event_duration_steps": ("24",),
        },
        "D21": {"value": ("Please_continue",), "event_duration_steps": ("24",)},
    }[case_id]
    if case_id == "D19" and re.search(
        r"\(:interaction_mode\s+articulation\b", case_block(text, case_id)
    ):
        values = dict(values)
        values["misplace_offset_xy"] = ("0.045", "-0.040")
    return values


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
            pattern,
            lambda match, value=digest: match.group(1) + value + match.group(2),
            manifest,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Missing manifest entry for {relative}")
    MANIFEST.write_text(manifest, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    paths = manifest_paths()
    changed: list[Path] = []
    for key in sorted(parameterization_keys()):
        path = paths.get(key)
        if path is None:
            raise ValueError(f"Review key is absent from task manifest: {key}")
        original = path.read_text(encoding="utf-8")
        updated = update_case_params(original, key[2], defaults(key[2], original))
        updated = normalize_case_params(updated, key[2])
        if updated != original:
            changed.append(path)
            if not args.check_only:
                path.write_text(updated, encoding="utf-8", newline="\n")
    if changed and not args.check_only:
        sync_hashes(changed)
    print(
        json.dumps(
            {
                "review_keys": len(review_keys()),
                "parameterization_keys": len(parameterization_keys()),
                "target_cases": sorted(TARGET_CASES),
                "changed": len(changed),
                "paths": [str(path.relative_to(ROOT)) for path in changed],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
