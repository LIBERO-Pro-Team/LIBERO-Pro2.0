"""Copy the approved 169 BDDLs and build their versioned manifest."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict

SUITE_TASK_IDS: Dict[str, int] = {
    "libero_spatial": 4,
    "libero_object": 0,
    "libero_goal": 9,
    "libero_10": 9,
}


def canonical_text_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--version", default="libero-pro2.0-169-v1")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    assets_root = args.assets_root.expanduser().resolve()
    destination = assets_root / "bddl" / args.version
    if destination.exists():
        raise SystemExit(f"Destination already exists: {destination}")

    source_files = sorted(source.glob("libero_*/*/*.bddl"))
    if len(source_files) != 169:
        raise SystemExit(f"Expected 169 approved BDDLs, found {len(source_files)}")

    tasks = []
    for source_path in source_files:
        suite = source_path.parents[1].name
        if suite not in SUITE_TASK_IDS:
            raise SystemExit(f"Unexpected suite: {suite}")
        case_id = source_path.name.split("__", 1)[0].upper()
        if case_id == "D20" and suite != "libero_10":
            raise SystemExit(f"Structurally inapplicable task is present: {suite}/{case_id}")
        case_kind = (
            "base" if case_id == "BASE" else "static" if case_id.startswith("S") else "dynamic"
        )
        relative = Path("bddl") / args.version / suite / source_path.parent.name / source_path.name
        target = assets_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target)
        tasks.append(
            {
                "suite": suite,
                "base_task_id": SUITE_TASK_IDS[suite],
                "case_id": case_id,
                "case_kind": case_kind,
                "bddl_path": relative.as_posix(),
                "bddl_sha256": hashlib.sha256(
                    canonical_text_bytes(target.read_bytes())
                ).hexdigest(),
                "task_version": args.version,
                "max_steps": 300,
                "reset_stabilization_steps": 10,
                "observation_schema_version": "libero_standard_v1",
                "action_schema_version": "libero_action_v1",
            }
        )

    tasks.sort(key=lambda item: (item["suite"], item["case_id"]))
    manifest = {
        "manifest_version": args.version,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    output = assets_root / "task_manifest.json"
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"manifest": str(output), "task_count": len(tasks)}))


if __name__ == "__main__":
    main()
