from pathlib import Path

import pytest

from libero_remote.environment import readiness


def _make_suite_directories(root: Path) -> None:
    for suite in ("libero_goal", "libero_spatial", "libero_object", "libero_10"):
        (root / suite).mkdir(parents=True)


def _make_runtime_sources(root: Path, *, compatible: bool) -> None:
    envs = root / "envs"
    envs.mkdir(parents=True, exist_ok=True)
    methods = (
        "def set_perturbation_seed(self, seed):\n        pass\n"
        "    def begin_perturbation_rollout(self):\n        pass\n"
        "    def get_perturbation_plan(self):\n        return {}\n"
        if compatible
        else ""
    )
    (envs / "env_wrapper.py").write_text(
        f"class ControlEnv:\n    {methods or 'pass'}\n", encoding="utf-8"
    )
    (envs / "bddl_utils.py").write_text(
        "def robosuite_parse_problem(path):\n"
        + (
            "    perturbation_config = {}\n"
            "    if ':perturbation_config':\n"
            "        return {'perturbation_config': perturbation_config}\n"
            if compatible
            else "    return {}\n"
        ),
        encoding="utf-8",
    )
    if compatible:
        (envs / "perturbation_config.py").write_text(
            "def parse_perturbation_config_group(group):\n    return {}\n",
            encoding="utf-8",
        )
        (envs / "nonphysical_perturbations.py").write_text(
            "class NonPhysicalPerturbationRuntime:\n    pass\n",
            encoding="utf-8",
        )


def test_readiness_checks_configured_bddl_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "libero"
    (package_root / "assets").mkdir(parents=True)
    _make_suite_directories(package_root / "init_files")
    bddl_root = tmp_path / "central-bddl"
    _make_suite_directories(bddl_root)
    _make_runtime_sources(package_root, compatible=True)
    monkeypatch.setattr(readiness, "_find_libero_package_root", lambda: package_root)
    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(bddl_root))

    result = readiness.check_backend_readiness("libero")

    assert result["ready"] is True
    assert result["bddl_root"] == str(bddl_root.resolve())


def test_readiness_reports_missing_configured_bddl_suite(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "libero"
    (package_root / "assets").mkdir(parents=True)
    _make_suite_directories(package_root / "init_files")
    bddl_root = tmp_path / "central-bddl"
    bddl_root.mkdir()
    _make_runtime_sources(package_root, compatible=True)
    monkeypatch.setattr(readiness, "_find_libero_package_root", lambda: package_root)
    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(bddl_root))

    result = readiness.check_backend_readiness("libero")

    assert result["ready"] is False
    assert result["reason"] == "required_data_missing"
    assert str(bddl_root / "libero_goal") in result["missing_paths"]


def test_readiness_reports_valid_task_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "libero"
    (package_root / "assets").mkdir(parents=True)
    _make_suite_directories(package_root / "init_files")
    _make_suite_directories(package_root / "bddl_files")
    _make_runtime_sources(package_root, compatible=True)
    monkeypatch.setattr(readiness, "_find_libero_package_root", lambda: package_root)
    manifest = Path(__file__).resolve().parents[1] / "assets" / "task_manifest.json"

    result = readiness.check_backend_readiness("libero", str(manifest))

    assert result["ready"] is True
    assert result["task_manifest"]["task_count"] == 1688


def test_readiness_rejects_a_runtime_without_perturbation_support(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "libero"
    (package_root / "assets").mkdir(parents=True)
    _make_suite_directories(package_root / "init_files")
    _make_suite_directories(package_root / "bddl_files")
    _make_runtime_sources(package_root, compatible=False)
    monkeypatch.setattr(readiness, "_find_libero_package_root", lambda: package_root)

    result = readiness.check_backend_readiness("libero")

    assert result["ready"] is False
    assert result["reason"] == "runtime_capabilities_missing"
    assert result["missing_capabilities"] == [
        "begin_perturbation_rollout",
        "get_perturbation_plan",
        "nonphysical_perturbation_runtime",
        "perturbation_config_parser",
        "set_perturbation_seed",
    ]
