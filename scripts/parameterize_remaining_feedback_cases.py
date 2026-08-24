"""Parameterize D17/S07/S13/S14 without changing unaffected task behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
TARGET_CASES = {"D17", "S07", "S13", "S14"}

DEFAULTS: dict[str, dict[str, tuple[str, ...]]] = {
    "D17": {
        "grasp_distance_m": ("0.12",),
        "grasp_initial_tolerance_m": ("0.035",),
        "contact_fallback_distance_m": ("0.055",),
        "wrapper_fallback_distance_m": ("0.12",),
        "articulation_grasp_distance_m": ("0.14",),
    },
    "S07": {
        "geometry_factors": ("1.0", "0.64", "1.20"),
        # Identity preserves the historical success-region behavior.
        "goal_region_scale": ("1.0", "1.0", "1.0"),
    },
    "S13": {"color_rgb": ("0.18", "0.72", "0.38")},
    "S14": {
        "scene_color_mix": ("0.48",),
        "scene_luminance_factors": ("0.72", "0.86", "1.18"),
        "light_factor": ("0.64",),
    },
}

OVERRIDES: dict[tuple[str, int, str], dict[str, tuple[str, ...]]] = {
    ("libero_goal", 2, "D17"): {"event_duration_steps": ("48",)},
    ("libero_goal", 7, "D17"): {
        "event_duration_steps": ("48",),
        "articulation_grasp_distance_m": ("0.16",),
    },
    ("libero_10", 5, "S07"): {
        "geometry_factors": ("1.0", "0.82", "1.05"),
        "goal_region_scale": ("1.0", "0.82", "1.05"),
    },
    ("libero_10", 9, "S07"): {
        "geometry_factors": ("1.0", "0.85", "1.05"),
        "goal_region_scale": ("1.0", "0.85", "1.05"),
    },
    ("libero_spatial", 1, "S07"): {
        "geometry_factors": ("1.0", "0.80", "1.05"),
        "goal_region_scale": ("1.0", "0.80", "1.05"),
    },
    ("libero_goal", 2, "S07"): {
        "geometry_factors": ("1.0", "0.82", "1.08"),
        "goal_region_scale": ("1.0", "0.82", "1.08"),
    },
    ("libero_spatial", 9, "S14"): {
        "scene_color_mix": ("0.32",),
        "light_factor": ("0.78",),
    },
}


def _group_end(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError(f"Unclosed BDDL group at offset {start}")


def _update_params(
    text: str, case_id: str, values: dict[str, tuple[str, ...]]
) -> tuple[str, dict[str, dict[str, str | None]]]:
    case_match = re.search(rf"\(\s*{re.escape(case_id)}\b", text)
    if case_match is None:
        raise ValueError(f"Missing perturbation case {case_id}")
    case_end = _group_end(text, case_match.start())
    block = text[case_match.start() : case_end]
    params_match = re.search(r"\(\s*:params\b", block)
    if params_match is None:
        raise ValueError(f"Perturbation case {case_id} has no params group")
    params_end = _group_end(block, params_match.start())
    params = block[params_match.start() : params_end]
    newline = "\r\n" if "\r\n" in text else "\n"
    changes: dict[str, dict[str, str | None]] = {}
    for key, atoms in values.items():
        replacement = f"(:{key} {' '.join(atoms)})"
        field_match = re.search(rf"\(\s*:{re.escape(key)}\b[^)]*\)", params)
        old = field_match.group(0) if field_match else None
        if old == replacement:
            continue
        if field_match:
            params = params[: field_match.start()] + replacement + params[field_match.end() :]
        else:
            insertion = params.rfind(")")
            params = (
                params[:insertion].rstrip()
                + newline
                + "          "
                + replacement
                + newline
                + "        "
                + params[insertion:]
            )
        changes[key] = {"old": old, "new": replacement}
    updated_block = block[: params_match.start()] + params + block[params_end:]
    return text[: case_match.start()] + updated_block + text[case_end:], changes


def _canonical_hash(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def _sync_manifest(paths: list[Path]) -> None:
    text = MANIFEST.read_bytes().decode("utf-8")
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        pattern = (
            rf'("bddl_path"\s*:\s*"{re.escape(relative)}"\s*,\s*'
            rf'"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        )
        digest = _canonical_hash(path)
        text, count = re.subn(
            pattern,
            lambda match, value=digest: match.group(1) + value + match.group(2),
            text,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Missing manifest entry for {relative}")
    MANIFEST.write_bytes(text.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entries = [item for item in payload["tasks"] if item["case_id"] in TARGET_CASES]
    if len(entries) != 160:
        raise ValueError(f"Expected 160 category tasks, found {len(entries)}")

    changed_paths: list[Path] = []
    report: list[dict[str, object]] = []
    for item in entries:
        key = (str(item["suite"]), int(item["base_task_id"]), str(item["case_id"]))
        path = ROOT / "assets" / item["bddl_path"]
        original = path.read_bytes().decode("utf-8")
        values = dict(DEFAULTS[key[2]])
        values.update(OVERRIDES.get(key, {}))
        updated, changes = _update_params(original, key[2], values)
        if updated == original:
            continue
        changed_paths.append(path)
        report.append(
            {
                "suite": key[0],
                "task_id": key[1],
                "case_id": key[2],
                "bddl": str(path.relative_to(ROOT)),
                "fields": changes,
            }
        )
        if not args.check_only:
            path.write_bytes(updated.encode("utf-8"))

    if changed_paths and not args.check_only:
        _sync_manifest(changed_paths)
    result = {
        "category_tasks": len(entries),
        "feedback_overrides": len(OVERRIDES),
        "changed": len(changed_paths),
        "changes": report,
    }
    if args.report and not args.check_only:
        output = args.report if args.report.is_absolute() else ROOT / args.report
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
