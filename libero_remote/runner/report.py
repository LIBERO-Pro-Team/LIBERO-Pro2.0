"""Build reproducible evaluation manifests for JSONL reports."""

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional

from libero_remote.protocol.models import PROTOCOL_VERSION

from .xvla import RunManifest


def build_run_manifest(
    health: Dict[str, Any],
    repo_root: Path,
    lerobot_root: Path,
    model_path: Path,
    tokenizer_path: Path,
    evaluation: Dict[str, Any],
) -> RunManifest:
    devices = _gpu_devices()
    return RunManifest(
        created_at=datetime.now(timezone.utc).isoformat(),
        protocol_version=PROTOCOL_VERSION,
        server={
            "status": health.get("status"),
            "service_version": health.get("version"),
            "backend": health.get("backend"),
            "runtime": health.get("runtime"),
        },
        client={
            "repo": {"root": str(repo_root.resolve()), **_git_state(repo_root)},
            "lerobot": {"root": str(lerobot_root.resolve()), **_git_state(lerobot_root)},
            "packages": {
                "torch": _package_version("torch"),
                "transformers": _package_version("transformers"),
                "lerobot": _package_version("lerobot"),
                "numpy": _package_version("numpy"),
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "executable": sys.executable,
            },
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
            },
            "gpu": {
                "visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                "driver_version": devices[0]["driver_version"] if devices else None,
                "devices": devices,
            },
        },
        model={
            "weights": _artifact_manifest(model_path),
            "tokenizer": _artifact_manifest(tokenizer_path),
        },
        evaluation=dict(evaluation),
    )


def _artifact_manifest(root: Path) -> Dict[str, Any]:
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"Artifact directory does not exist: {resolved}")
    files = sorted(
        path
        for path in resolved.rglob("*")
        if path.is_file() and ".cache" not in path.relative_to(resolved).parts
    )
    digest = hashlib.sha256()
    total_bytes = 0
    for path in files:
        relative = path.relative_to(resolved).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        size = path.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        total_bytes += size
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    return {
        "root": str(resolved),
        "sha256": digest.hexdigest(),
        "file_count": len(files),
        "total_bytes": total_bytes,
    }


def _package_version(distribution: str) -> Optional[str]:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _git_state(root: Path) -> Dict[str, Any]:
    commit = _run(["git", "-C", str(root.resolve()), "rev-parse", "HEAD"])
    if commit is None:
        return {"commit": None, "tracked_dirty": None}
    dirty_code = _return_code(
        ["git", "-C", str(root.resolve()), "diff", "--quiet", "HEAD", "--"]
    )
    tracked_dirty = dirty_code == 1 if dirty_code in {0, 1} else None
    return {"commit": commit, "tracked_dirty": tracked_dirty}


def _gpu_devices() -> List[Dict[str, Any]]:
    output = _run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,driver_version",
            "--format=csv,noheader,nounits",
        ]
    )
    if output is None:
        return []
    devices = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) == 3:
            try:
                index = int(parts[0])
            except ValueError:
                continue
            devices.append(
                {"index": index, "name": parts[1], "driver_version": parts[2]}
            )
    return devices


def _return_code(command: List[str]) -> Optional[int]:
    try:
        return subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3.0,
            check=False,
        ).returncode
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None


def _run(command: List[str]) -> Optional[str]:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3.0,
            check=False,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()
