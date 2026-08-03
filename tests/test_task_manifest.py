import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from libero_remote.environment.task_manifest import TaskManifest
from libero_remote.server.app import create_app
from libero_remote.server.settings import Settings

ASSETS_ROOT = Path(__file__).resolve().parents[1] / "assets"
MANIFEST_PATH = ASSETS_ROOT / "task_manifest.json"


def test_published_manifest_contains_exactly_169_approved_tasks() -> None:
    manifest = TaskManifest.load(str(MANIFEST_PATH))

    assert manifest.version == "libero-pro2.0-169-v1"
    assert len(manifest.entries) == 169
    assert sum(entry["case_id"] == "BASE" for entry in manifest.entries) == 4
    assert sum(str(entry["case_id"]).startswith("S") for entry in manifest.entries) == 84
    assert sum(str(entry["case_id"]).startswith("D") for entry in manifest.entries) == 81
    assert [
        (entry["suite"], entry["case_id"])
        for entry in manifest.entries
        if entry["case_id"] == "D20"
    ] == [("libero_10", "D20")]


def test_manifest_rejects_a_tampered_bddl(tmp_path: Path) -> None:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entry = dict(payload["tasks"][0])
    copied = tmp_path / "task.bddl"
    copied.write_bytes((ASSETS_ROOT / entry["bddl_path"]).read_bytes() + b"\n")
    entry["bddl_path"] = copied.name
    payload["tasks"] = [entry]
    payload["task_count"] = 1
    manifest_path = tmp_path / "task_manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        TaskManifest.load(str(manifest_path))


def test_manifest_rejects_unpublished_suite_task_case() -> None:
    manifest = TaskManifest.load(str(MANIFEST_PATH))

    with pytest.raises(ValueError, match="not published"):
        manifest.require("libero_goal", 9, "D20")


def test_api_rejects_unpublished_task_with_stable_client_error() -> None:
    app = create_app(
        Settings(
            environment_backend="fake",
            task_manifest_path=str(MANIFEST_PATH),
        )
    )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/v1/sessions",
            json={
                "protocol_version": "1.0",
                "suite": "libero_goal",
                "task_id": 0,
                "variant": "base",
                "camera_height": 16,
                "camera_width": 16,
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "protocol_version": "1.0",
        "error_code": "INVALID_TASK",
        "message": (
            "The requested suite, task_id, and variant are not published; "
            "query /v1/tasks for valid combinations"
        ),
        "request_id": None,
        "details": {
            "suite": "libero_goal",
            "task_id": 0,
            "variant": "base",
        },
    }
