from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_production_compose_enforces_isolation_and_versioned_tasks() -> None:
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "LIBERO_REMOTE_AUTHENTICATION_REQUIRED:-true" in compose
    assert "LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS:-false" in compose
    assert "LIBERO_REMOTE_RESULT_SIGNING_KEY:?" in compose
    assert "/opt/libero-remote/assets/task_manifest.json" in compose
    assert "/opt/libero-remote/assets/bddl/libero-pro2.0-169-v1" in compose


def test_server_image_has_no_model_runtime_configuration() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8").lower()
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8").lower()
    deployment = dockerfile + compose

    assert "xvla" not in deployment
    assert "pi0" not in deployment
    assert "model_path" not in deployment
    assert "checkpoint" not in deployment
    bddl_setting = (
        "libero_remote_bddl_root="
        "/opt/libero-remote/assets/bddl/libero-pro2.0-169-v1"
    )
    assert bddl_setting in dockerfile
