"""Cheap backend configuration checks that do not initialize MuJoCo."""

import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .task_manifest import TaskManifest


def check_backend_readiness(
    backend: str, task_manifest_path: Optional[str] = None
) -> Dict[str, Any]:
    if backend == "fake":
        return {"name": backend, "ready": True}
    if backend != "libero":
        return {
            "name": backend,
            "ready": False,
            "reason": "unsupported_backend",
        }

    package_root = _find_libero_package_root()
    if package_root is None:
        return {
            "name": backend,
            "ready": False,
            "reason": "libero_package_not_found",
        }

    configured_bddl_root = os.environ.get("LIBERO_REMOTE_BDDL_ROOT")
    bddl_root = (
        Path(configured_bddl_root).resolve()
        if configured_bddl_root
        else package_root / "bddl_files"
    )
    required_paths = [
        package_root / "assets",
        *(bddl_root / suite for suite in _base_suites()),
        *(package_root / "init_files" / suite for suite in _base_suites()),
    ]
    missing = [str(path) for path in required_paths if not path.is_dir()]
    result: Dict[str, Any] = {
        "name": backend,
        "ready": not missing,
        "package_root": str(package_root),
        "bddl_root": str(bddl_root),
    }
    if missing:
        result["reason"] = "required_data_missing"
        result["missing_paths"] = missing
    if not missing and task_manifest_path:
        try:
            manifest = TaskManifest.load(task_manifest_path)
        except Exception as error:
            result["ready"] = False
            result["reason"] = "task_manifest_invalid"
            result["task_manifest_error"] = str(error)
        else:
            result["task_manifest"] = {
                "version": manifest.version,
                "sha256": manifest.sha256,
                "task_count": len(manifest.entries),
            }
    return result


def _find_libero_package_root() -> Optional[Path]:
    configured_root = os.environ.get("LIBERO_PRO_ROOT")
    if configured_root:
        return Path(configured_root).resolve() / "libero" / "libero"

    try:
        spec = importlib.util.find_spec("libero.libero")
    except (ImportError, ModuleNotFoundError, ValueError):
        return None
    if spec is None or spec.origin is None:
        return None
    return Path(spec.origin).resolve().parent


def _base_suites() -> tuple:
    return ("libero_goal", "libero_spatial", "libero_object", "libero_10")
