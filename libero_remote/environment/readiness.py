"""Cheap backend configuration checks that do not initialize MuJoCo."""

import ast
import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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
    missing_capabilities = _missing_runtime_capabilities(package_root)
    if not missing and missing_capabilities:
        result["ready"] = False
        result["reason"] = "runtime_capabilities_missing"
        result["missing_capabilities"] = missing_capabilities
    if not missing and not missing_capabilities and task_manifest_path:
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


def _missing_runtime_capabilities(package_root: Path) -> List[str]:
    envs_root = package_root / "envs"
    wrapper = _parse_python(envs_root / "env_wrapper.py")
    bddl_utils = _parse_python(envs_root / "bddl_utils.py")
    parser = _parse_python(envs_root / "perturbation_config.py")
    runtime = _parse_python(envs_root / "nonphysical_perturbations.py")

    wrapper_methods = _class_methods(wrapper, "ControlEnv")
    parser_functions = _module_functions(parser)
    runtime_classes = _module_classes(runtime)
    bddl_literals = {
        node.value
        for node in ast.walk(bddl_utils)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    capabilities = {
        "set_perturbation_seed": "set_perturbation_seed" in wrapper_methods,
        "begin_perturbation_rollout": "begin_perturbation_rollout" in wrapper_methods,
        "get_perturbation_plan": "get_perturbation_plan" in wrapper_methods,
        "perturbation_config_parser": (
            "parse_perturbation_config_group" in parser_functions
            and ":perturbation_config" in bddl_literals
            and "perturbation_config" in bddl_literals
        ),
        "nonphysical_perturbation_runtime": (
            "NonPhysicalPerturbationRuntime" in runtime_classes
        ),
    }
    return sorted(name for name, available in capabilities.items() if not available)


def _parse_python(path: Path) -> ast.AST:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError):
        return ast.Module(body=[], type_ignores=[])


def _class_methods(tree: ast.AST, class_name: str) -> Set[str]:
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    return set()


def _module_functions(tree: ast.AST) -> Set[str]:
    return {
        node.name
        for node in getattr(tree, "body", [])
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _module_classes(tree: ast.AST) -> Set[str]:
    return {
        node.name for node in getattr(tree, "body", []) if isinstance(node, ast.ClassDef)
    }


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
