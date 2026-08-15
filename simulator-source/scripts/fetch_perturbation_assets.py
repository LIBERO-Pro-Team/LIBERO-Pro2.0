from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    REPO_ROOT / "libero" / "libero" / "assets" / "perturbation_assets"
)


@dataclass(frozen=True)
class Source:
    key: str
    repository: str
    commit: str
    license_id: str
    source_paths: tuple[str, ...]
    destination: str


SOURCES = (
    Source(
        key="prl_assets",
        repository="https://github.com/personalrobotics/prl_assets.git",
        commit="c7c474e74961c773f6adc44249ed33599fbf510a",
        license_id="MIT",
        source_paths=("LICENSE", "README.md", "src/prl_assets/objects"),
        destination="vendor/prl_assets",
    ),
    Source(
        key="pybullet_ycb",
        repository="https://github.com/eleramp/pybullet-object-models.git",
        commit="57cc4007607f6bcbb0a5364ccab7636faf7a91e4",
        license_id="LGPL-2.1-only",
        source_paths=("LICENSE", "README.md", "pybullet_object_models/ycb_objects"),
        destination="vendor/pybullet_ycb",
    ),
    Source(
        key="robocasa_fixtures",
        repository="https://github.com/robocasa/robocasa.git",
        commit="b4684e6ee37d377cc392e98302a6b916d588b415",
        license_id="CC-BY-4.0",
        source_paths=(
            "LICENSE",
            "README.md",
            "robocasa/models/assets/fixtures/handles",
        ),
        destination="vendor/robocasa_fixtures",
    ),
)


def run(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def copy_source_path(checkout: Path, relative: str, destination: Path) -> None:
    source = checkout / Path(PurePosixPath(relative))
    if not source.exists():
        raise FileNotFoundError(f"Pinned source path does not exist: {relative}")
    target = destination / Path(PurePosixPath(relative))
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)


def fetch_source(source: Source, output: Path, temp_root: Path) -> None:
    checkout = temp_root / source.key
    run(
        "git",
        "clone",
        "--filter=blob:none",
        "--no-checkout",
        source.repository,
        str(checkout),
    )
    run("git", "checkout", "--detach", source.commit, cwd=checkout)
    destination = output / source.destination
    if output not in destination.resolve().parents:
        raise ValueError(f"Destination escapes output root: {destination}")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for source_path in source.source_paths:
        copy_source_path(checkout, source_path, destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(output: Path) -> None:
    files = []
    for path in sorted((output / "vendor").rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": path.relative_to(output).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    manifest = {
        "format_version": 1,
        "sources": [
            {
                "key": source.key,
                "repository": source.repository,
                "commit": source.commit,
                "license": source.license_id,
                "destination": source.destination,
            }
            for source in SOURCES
        ],
        "files": files,
    }
    (output / "vendor_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch pinned external assets used by LIBERO-Pro perturbations."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="libero-pro-assets-") as temp_dir:
        temp_root = Path(temp_dir)
        for source in SOURCES:
            print(f"Fetching {source.key} at {source.commit}...", flush=True)
            fetch_source(source, output, temp_root)
    write_manifest(output)
    print(f"Assets and manifest written to {output}")


if __name__ == "__main__":
    main()
