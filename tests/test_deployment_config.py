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
    assert "cudnn" not in dockerfile
    assert "torch==1.11.0+cpu" in dockerfile
    assert "torchvision==0.12.0+cpu" in dockerfile
    assert "python3-distutils" in dockerfile
    assert "cmake" in dockerfile
    bddl_setting = (
        "libero_remote_bddl_root="
        "/opt/libero-remote/assets/bddl/libero-pro2.0-169-v1"
    )
    assert bddl_setting in dockerfile


def test_customer_local_compose_enables_authenticated_direct_sessions() -> None:
    compose = (ROOT / "deploy" / "customer-local" / "compose.yaml").read_text(
        encoding="utf-8"
    )

    assert "LIBERO_REMOTE_AUTHENTICATION_REQUIRED: \"true\"" in compose
    assert "LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS: \"true\"" in compose
    assert "127.0.0.1:${LIBERO_REMOTE_PUBLIC_PORT:-8000}:8000" in compose
    assert "libero-pro-server:1.0.0" in compose
    assert "gpus: all" in compose
    assert "./assets:/opt/libero-remote/assets:ro" in compose


def test_customer_bundle_scripts_do_not_fetch_runtime_files_from_github() -> None:
    deployment = ROOT / "deploy" / "customer-local"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in deployment.rglob("*")
        if path.is_file()
    ).lower()

    assert "git clone" not in sources
    assert "github.com/zxy-mllab/libero-pro" not in sources


def test_customer_install_checks_container_gpu_and_uses_bash_entrypoints() -> None:
    deployment = ROOT / "deploy" / "customer-local"
    install = (deployment / "install.sh").read_text(encoding="utf-8")
    readme = (deployment / "README.md").read_text(encoding="utf-8")

    assert "docker run --rm --gpus all" in install
    assert "--entrypoint nvidia-smi" in install
    assert "bash configure.sh" in install
    assert "bash healthcheck.sh" in install
    assert "bash install.sh" in readme
    assert "bash add_account.sh team-b" in readme
