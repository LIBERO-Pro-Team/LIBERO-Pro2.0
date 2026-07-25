"""Cheap backend configuration checks that do not initialize MuJoCo."""

import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, Optional


def check_backend_readiness(backend: str) -> Dict[str, Any]:
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

    required_paths = [
        package_root / "assets",
        *(package_root / "bddl_files" / suite for suite in _base_suites()),
        *(package_root / "init_files" / suite for suite in _base_suites()),
    ]
    missing = [str(path) for path in required_paths if not path.is_dir()]
    result: Dict[str, Any] = {
        "name": backend,
        "ready": not missing,
        "package_root": str(package_root),
    }
    if missing:
        result["reason"] = "required_data_missing"
        result["missing_paths"] = missing
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
