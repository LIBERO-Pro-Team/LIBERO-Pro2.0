"""Collect reproducibility metadata without importing simulator packages."""

import os
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Optional


def collect_runtime_manifest() -> Dict[str, Any]:
    service_root = Path(__file__).resolve().parents[2]
    libero_root_value = os.environ.get("LIBERO_PRO_ROOT")
    libero_root = Path(libero_root_value).resolve() if libero_root_value else None
    devices = _gpu_devices()
    service_state = _git_state(service_root)
    libero_state = _git_state(libero_root) if libero_root else _unknown_git_state()
    if service_state["commit"] is None:
        service_state["commit"] = _optional_env("LIBERO_REMOTE_COMMIT")
    if libero_state["commit"] is None:
        libero_state["commit"] = _optional_env("LIBERO_PRO_COMMIT")
    return {
        "service": service_state,
        "libero": {
            "root": str(libero_root) if libero_root else None,
            **libero_state,
        },
        "packages": {
            "libero": _package_version("libero"),
            "mujoco": _package_version("mujoco"),
            "mujoco_py": _package_version("mujoco-py"),
            "robosuite": _package_version("robosuite"),
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
        "egl": {
            "MUJOCO_GL": os.environ.get("MUJOCO_GL"),
            "MUJOCO_EGL_DEVICE_ID": os.environ.get("MUJOCO_EGL_DEVICE_ID"),
            "PYOPENGL_PLATFORM": os.environ.get("PYOPENGL_PLATFORM"),
        },
    }


def _optional_env(name: str) -> Optional[str]:
    value = os.environ.get(name, "").strip()
    return value or None


def _package_version(distribution: str) -> Optional[str]:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _unknown_git_state() -> Dict[str, Any]:
    return {"commit": None, "tracked_dirty": None}


def _git_state(root: Path) -> Dict[str, Any]:
    commit = _run(["git", "-C", str(root), "rev-parse", "HEAD"])
    if commit is None:
        return _unknown_git_state()
    dirty_code = _return_code(
        ["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"]
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
        if len(parts) != 3:
            continue
        try:
            index = int(parts[0])
        except ValueError:
            continue
        devices.append(
            {"index": index, "name": parts[1], "driver_version": parts[2]}
        )
    return devices


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
