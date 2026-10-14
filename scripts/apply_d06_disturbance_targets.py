"""Parameterize D06 with up to three task-unrelated movable objects."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BDDL_ROOT = ROOT / "assets" / "bddl" / "libero-pro2.0-1680-v1"
MANIFEST = ROOT / "assets" / "task_manifest.json"


def _section(source: str, name: str, next_name: str) -> str:
    match = re.search(
        rf"\(:{re.escape(name)}\b(?P<body>.*?)\)\s*\r?\n\s*\(:{re.escape(next_name)}\b",
        source,
        flags=re.DOTALL,
    )
    if match is None:
        raise ValueError(f"Missing :{name} section")
    return match.group("body")


def _object_names(source: str) -> list[str]:
    names: list[str] = []
    for raw_line in _section(source, "objects", "obj_of_interest").splitlines():
        declaration = raw_line.strip()
        if not declaration or " - " not in declaration:
            continue
        names.extend(declaration.split(" - ", 1)[0].split())
    return names


def _goal_atoms(source: str) -> set[str]:
    goal = _section(source, "goal", "perturbation_config")
    return set(re.findall(r"[^\s()]+", goal))


def disturbance_targets(source: str) -> tuple[str, ...]:
    goal_atoms = _goal_atoms(source)
    unrelated = [
        name
        for name in _object_names(source)
        if not any(atom == name or atom.startswith(f"{name}_") for atom in goal_atoms)
    ]
    return tuple(unrelated[:3])


def update_d06(source: str, targets: tuple[str, ...]) -> str:
    newline = "\r\n" if "\r\n" in source else "\n"
    block_match = re.search(
        r"(?ms)^      \(D06\r?\n(?P<body>.*?)^      \)\r?\n      \(D07\r?$",
        source,
    )
    if block_match is None:
        raise ValueError("Missing D06 block")
    body = block_match.group("body")
    atoms = " ".join(targets) if targets else "none"
    target_line = f"        (:disturbance_targets {atoms})"
    target_pattern = r"(?m)^        \(:disturbance_targets[^\r\n]*\)(?P<cr>\r?)$"
    if re.search(target_pattern, body):
        body = re.sub(
            target_pattern,
            lambda match: target_line + match.group("cr"),
            body,
            count=1,
        )
    else:
        body = re.sub(
            r"(?m)^(        \(:targets[^\r\n]*\))(?P<cr>\r?)$",
            lambda match: match.group(1) + newline + target_line + match.group("cr"),
            body,
            count=1,
        )
    params = {
        "offset_xy": "0.12 -0.09",
        "minimum_displacement_m": "0.10",
    }
    for key, value in params.items():
        field = f"          (:{key} {value})"
        pattern = rf"(?m)^          \(:{re.escape(key)}[^\r\n]*\)(?P<cr>\r?)$"
        if re.search(pattern, body):
            body = re.sub(
                pattern,
                lambda match: field + match.group("cr"),
                body,
                count=1,
            )
        else:
            body = re.sub(
                r"(?m)^(          \(:interaction_mode[^\r\n]*\))(?P<cr>\r?)$",
                lambda match: match.group(1) + newline + field + match.group("cr"),
                body,
                count=1,
            )
    start, end = block_match.span("body")
    return source[:start] + body + source[end:]


def _canonical_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    """Replace one BDDL/manifest atomically, then verify the bytes we wrote."""
    encoded = text.encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        if path.read_bytes() != encoded:
            raise IOError(f"Atomic write verification failed for {path}")
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _sync_manifest(paths: list[Path]) -> None:
    source = MANIFEST.read_text(encoding="utf-8")
    for path in paths:
        relative = path.relative_to(ROOT / "assets").as_posix()
        digest = _canonical_hash(path)
        pattern = re.compile(
            rf'("bddl_path"\s*:\s*"{re.escape(relative)}"\s*,\s*\n\s*'
            rf'"bddl_sha256"\s*:\s*")[0-9a-f]+(")'
        )
        source, count = pattern.subn(rf"\g<1>{digest}\2", source, count=1)
        if count != 1:
            raise ValueError(f"Manifest entry not found exactly once: {relative}")
    _atomic_write_text(MANIFEST, source)


def apply(*, check: bool = False) -> list[tuple[Path, tuple[str, ...]]]:
    files = sorted(BDDL_ROOT.glob("*/02_dynamic/D06__*.bddl"))
    if len(files) != 40:
        raise ValueError(f"Expected 40 D06 BDDL files, found {len(files)}")
    results: list[tuple[Path, tuple[str, ...]]] = []
    changed: list[Path] = []
    for path in files:
        with path.open("r", encoding="utf-8", newline="") as handle:
            source = handle.read()
        targets = disturbance_targets(source)
        updated = update_d06(source, targets)
        results.append((path, targets))
        if updated != source:
            changed.append(path)
            if not check:
                _atomic_write_text(path, updated)
                with path.open("r", encoding="utf-8", newline="") as handle:
                    written = handle.read()
                if ":disturbance_targets" not in written or ":minimum_displacement_m 0.10" not in written:
                    raise IOError(f"D06 field verification failed for {path}")
    if changed and not check:
        _sync_manifest(changed)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    results = apply(check=args.check)
    for path, targets in results:
        print(f"{path.relative_to(BDDL_ROOT)}: {len(targets)} [{', '.join(targets)}]")


if __name__ == "__main__":
    main()
