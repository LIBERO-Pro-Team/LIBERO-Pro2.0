from pathlib import Path

import pytest

from libero_remote.environment import readiness


def _make_suite_directories(root: Path) -> None:
    for suite in ("libero_goal", "libero_spatial", "libero_object", "libero_10"):
        (root / suite).mkdir(parents=True)


def test_readiness_checks_configured_bddl_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    package_root = tmp_path / "libero"
    (package_root / "assets").mkdir(parents=True)
    _make_suite_directories(package_root / "init_files")
    bddl_root = tmp_path / "central-bddl"
    _make_suite_directories(bddl_root)
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
    monkeypatch.setattr(readiness, "_find_libero_package_root", lambda: package_root)
    monkeypatch.setenv("LIBERO_REMOTE_BDDL_ROOT", str(bddl_root))

    result = readiness.check_backend_readiness("libero")

    assert result["ready"] is False
    assert result["reason"] == "required_data_missing"
    assert str(bddl_root / "libero_goal") in result["missing_paths"]
