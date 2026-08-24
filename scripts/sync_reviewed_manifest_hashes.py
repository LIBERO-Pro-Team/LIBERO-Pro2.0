"""Update manifest hashes for the explicitly reviewed BDDL files only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "task_manifest.json"
WEAK = ROOT / ".codex-workbook-audit-20260819" / "weak_rows.json"
REVIEWED = ROOT / ".codex-workbook-audit-20260819" / "reviewed_bddl.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Reconcile hashes for all 1680 manifest entries.",
    )
    parser.add_argument(
        "--d06",
        action="store_true",
        help="Reconcile hashes for the 40 D06 entries only.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Reconcile one or more repository-relative BDDL paths.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.path:
        weak_rows = []
        reviewed = []
    elif args.d06:
        weak_rows = []
        reviewed = []
    else:
        weak_rows = json.loads(WEAK.read_text(encoding="utf-8"))
        reviewed = json.loads(REVIEWED.read_text(encoding="utf-8"))
    keys = {
        (row["套件"], int(row["任务ID"].removeprefix("task")), row["扰动"])
        for row in weak_rows
    }
    paths = {
        str(row["path"]).replace("\\", "/").removeprefix("assets/")
        for row in reviewed
    }
    # Resolve weak keys through the generated task manifest instead of
    # duplicating task-name ordering here.
    manifest_text = MANIFEST.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    if args.d06:
        keys = {
            (str(entry["suite"]), int(entry["base_task_id"]), "D06")
            for entry in manifest["tasks"]
            if str(entry["case_id"]) == "D06"
        }
    if args.path:
        paths.update(
            str(Path(value).as_posix())[len("assets/") :]
            if str(Path(value).as_posix()).startswith("assets/")
            else str(Path(value).as_posix())
            for value in args.path
        )
        manifest_paths = {
            str(entry["bddl_path"]).replace("\\", "/")
            for entry in manifest["tasks"]
        }
        normalized = set()
        for requested in paths:
            matches = [
                candidate
                for candidate in manifest_paths
                if candidate.lower() == requested.lower()
            ]
            if len(matches) != 1:
                raise RuntimeError(f"manifest path is not unique: {requested}")
            normalized.add(matches[0])
        paths = normalized
    for entry in manifest["tasks"]:
        key = (str(entry["suite"]), int(entry["base_task_id"]), str(entry["case_id"]))
        if args.all or key in keys:
            paths.add(str(entry["bddl_path"]).replace("\\", "/"))
    for relative in sorted(paths):
        path = ROOT / "assets" / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        escaped = re.escape(relative.replace("assets/", "", 1))
        pattern = rf'("bddl_path"\s*:\s*"{escaped}"\s*,\s*\n\s*"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        replacement = lambda match, value=digest(path): match.group(1) + value + match.group(2)
        manifest_text, count = re.subn(pattern, replacement, manifest_text, count=1)
        if count != 1:
            raise RuntimeError(f"manifest entry not found: {relative}")
    MANIFEST.write_text(manifest_text, encoding="utf-8")
    print(
        json.dumps(
            {"scope": "all" if args.all else "reviewed", "updated": len(paths)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
