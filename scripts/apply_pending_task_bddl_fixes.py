"""Apply only task-level BDDL fixes explicitly covered by ``待修改.md``.

This script deliberately does not touch simulator runtime code.  Every edit is
guarded by the review ledger's ``suite/task/case`` key and the manifest hash is
refreshed only for files that changed.
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


def update_case_params(text: str, case_id: str, values: dict[str, tuple[str, ...]]) -> str:
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
            params_text = params_text[: field_match.start()] + field + params_text[field_match.end() :]
        else:
            insertion = params_text.rfind(")")
            params_text = params_text[:insertion] + f"\n          {field}" + params_text[insertion:]
    case_text = case_text[:params_start] + params_text + case_text[params_end:]
    return text[: match.start()] + case_text + text[end:]


def replace_case_field(text: str, case_id: str, key: str, atoms: tuple[str, ...]) -> str:
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


def review_keys() -> set[tuple[str, int, str]]:
    with REVIEW.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            (row["suite"], int(row["task_id"]), row["扰动"].upper())
            for row in csv.DictReader(handle, delimiter="\t")
        }


def manifest_paths() -> dict[tuple[str, int, str], Path]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        (item["suite"], int(item["base_task_id"]), item["case_id"]): ROOT / "assets" / item["bddl_path"]
        for item in payload["tasks"]
    }


def overrides(suite: str, task_id: int, case_id: str) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    """Return (params, case fields) for one explicitly reviewed task case."""
    params: dict[str, tuple[str, ...]] = {}
    fields: dict[str, tuple[str, ...]] = {}

    if case_id == "D01" and suite == "libero_goal" and task_id in {0, 9}:
        params = {
            "offset_xy": ("0.10", "0.04") if task_id == 9 else ("-0.08", "0.06"),
            "trigger_distance_m": ("0.18",),
        }
    elif case_id == "D06":
        # D06 already consumes offset_xy.  Use a larger, task-local move only
        # for tasks that appear in the review ledger.
        if suite == "libero_goal" and task_id in range(10):
            params = {"offset_xy": (f"{0.11 + 0.01 * (task_id % 3):.2f}", f"{-0.09 - 0.01 * (task_id % 2):.2f}")}
        elif suite == "libero_object" and task_id in range(2, 10):
            params = {"offset_xy": (f"{0.10 + 0.01 * (task_id % 3):.2f}", f"{-0.08 - 0.01 * (task_id % 2):.2f}")}
        elif suite == "libero_spatial" and task_id in {1, 2, 3, 8, 9}:
            params = {"offset_xy": (f"{0.11 + 0.01 * (task_id % 2):.2f}", "-0.09")}
        elif suite == "libero_10" and task_id == 1:
            params = {"offset_xy": ("0.11", "-0.09")}
    elif case_id == "D15":
        # The baseline runtime consumes these fields.  Increase the stale
        # window only in reviewed tasks; unlisted tasks retain ec1aa8a values.
        if suite in {"libero_object", "libero_spatial", "libero_10"}:
            params = {"chunk_size": ("8",), "stale_chunk_steps": ("10",)}
    elif case_id == "S06":
        # Keep same-class replacements within a graspable size envelope.  The
        # task-specific asset identity remains unchanged unless the ledger
        # already specifies a compatible replacement.
        scale_map = {
            ("libero_10", 0): "0.55",
            ("libero_10", 1): "0.55",
            ("libero_10", 4): "0.55",
            ("libero_goal", 0): "0.55",
            ("libero_goal", 2): "0.55",
            ("libero_goal", 4): "0.55",
            ("libero_goal", 6): "0.55",
            ("libero_goal", 9): "0.55",
            ("libero_spatial", 5): "0.35",
            ("libero_spatial", 8): "0.35",
        }
        if (suite, task_id) in scale_map:
            params = {"asset_scale": (scale_map[(suite, task_id)],)}
    elif case_id == "S10" and suite == "libero_goal":
        # Static clutter is positioned relative to the declared reference.
        # Avoid self-anchoring on the target/handle and use another table item.
        refs = {
            0: "wine_bottle_1",
            1: "wine_bottle_1",
            2: "cream_cheese_1",
            5: "cream_cheese_1",
            6: "wine_bottle_1",
            7: "wine_bottle_1",
            8: "wine_bottle_1",
            9: "cream_cheese_1",
        }
        if task_id in refs:
            fields = {"references": (refs[task_id],)}
    elif case_id == "S10" and suite == "libero_spatial" and task_id in {1, 2, 3, 4, 6, 7, 9}:
        # The old reference could be on a cabinet/stove and caused a floating
        # clutter asset.  Anchor it to the table's cookie box instead.
        fields = {"references": ("cookies_1",)}

    return params, fields


def sync_hashes(paths: list[Path]) -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in paths:
        rel = path.relative_to(ROOT / "assets").as_posix()
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        pattern = rf'("bddl_path"\s*:\s*"{re.escape(rel)}"\s*,\s*\n\s*"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        manifest, count = re.subn(pattern, lambda m, value=digest: m.group(1) + value + m.group(2), manifest, count=1)
        if count != 1:
            raise ValueError(f"Missing manifest entry for {rel}")
    MANIFEST.write_text(manifest, encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    keys = review_keys()
    paths = manifest_paths()
    changed: list[Path] = []
    for key in sorted(keys):
        params, fields = overrides(*key)
        if not params and not fields:
            continue
        path = paths.get(key)
        if path is None:
            raise ValueError(f"Review key is absent from task manifest: {key}")
        original = path.read_text(encoding="utf-8")
        updated = original
        for field, atoms in fields.items():
            updated = replace_case_field(updated, key[2], field, atoms)
        if params:
            updated = update_case_params(updated, key[2], params)
        if updated != original:
            changed.append(path)
            if not args.check_only:
                path.write_text(updated, encoding="utf-8", newline="\n")
    if changed and not args.check_only:
        sync_hashes(changed)
    print(json.dumps({"review_keys": len(keys), "changed": len(changed), "paths": [str(p.relative_to(ROOT)) for p in changed]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
