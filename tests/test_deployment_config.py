import ast
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import tomllib

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


def test_sdk_metadata_separates_client_and_server_dependencies() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]

    assert metadata["requires-python"] == ">=3.8,<3.13"
    assert metadata["dependencies"] == [
        "httpx==0.24.1",
        "msgpack==1.0.8",
        "numpy==1.22.4; python_version < '3.10'",
        "numpy==1.26.4; python_version >= '3.10'",
        "pydantic==1.10.22",
    ]
    assert metadata["optional-dependencies"]["server"] == [
        "fastapi==0.103.2",
        "uvicorn[standard]==0.23.2",
    ]
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert 'pip install ".[server]"' in dockerfile


def test_server_commit_metadata_does_not_invalidate_dependency_layers() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8").lower()

    dependency_install = dockerfile.index('pip install -r "${libero_pro_root}/requirements.txt"')
    service_install = dockerfile.index('pip install ".[server]"')
    commit_argument = dockerfile.index("arg libero_remote_commit=unknown")
    revision_label = dockerfile.index("org.opencontainers.image.revision")
    commit_environment = dockerfile.index("env libero_remote_commit=")
    assert (
        dependency_install
        < service_install
        < commit_argument
        < commit_environment
        < revision_label
    )


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


def test_customer_bundle_export_preserves_manifest_bddl_bytes(tmp_path: Path) -> None:
    builder = (ROOT / "scripts" / "build_customer_bundle.ps1").read_text(
        encoding="utf-8"
    )

    assert "git -c core.autocrlf=false" in builder
    assert builder.count("Assert-ManifestBddlHashes $manifest") == 2
    assert 'Assert-ManifestBddlHashes $manifest (Join-Path $sourceRoot "assets")' in builder

    archive = tmp_path / "service.zip"
    subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "archive",
            "--format=zip",
            f"--output={archive}",
            "HEAD",
        ],
        cwd=ROOT,
        check=True,
    )
    with zipfile.ZipFile(archive) as exported:
        manifest = json.loads(exported.read("assets/task_manifest.json"))
        for task in manifest["tasks"]:
            content = exported.read(f"assets/{task['bddl_path']}")
            assert hashlib.sha256(content).hexdigest() == task["bddl_sha256"]


def test_customer_bundle_records_built_image_digest() -> None:
    builder = (ROOT / "scripts" / "build_customer_bundle.ps1").read_text(
        encoding="utf-8"
    )

    assert 'docker image inspect `' in builder
    assert "image_digest = $imageDigest" in builder


def test_customer_bundle_builds_an_offline_linux_sdk_wheelhouse() -> None:
    builder = (ROOT / "scripts" / "build_customer_bundle.ps1").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "deploy" / "customer-local" / "README.md").read_text(
        encoding="utf-8"
    )
    installer = (ROOT / "deploy" / "customer-local" / "install.sh").read_text(
        encoding="utf-8"
    )

    assert '$clientPythonVersions = @("38", "39", "310", "311", "312")' in builder
    assert '"--platform", "manylinux2014_x86_64"' in builder
    assert '"--no-deps"' in builder
    assert '"--only-binary=:all:"' in builder
    assert '"--python-version", $pythonVersion' in builder
    assert '"numpy==1.22.4"' in builder
    assert '"numpy==1.26.4"' in builder
    assert '"anyio==3.7.1"' in builder
    assert '"httpcore==0.17.3"' in builder
    offline_install = (
        "python3 -m pip install --no-index --find-links wheels "
        "wheels/libero_remote-1.0.0-py3-none-any.whl"
    )
    assert offline_install in readme
    assert offline_install in installer


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


def test_customer_examples_use_a_published_manifest_task() -> None:
    deployment = ROOT / "deploy" / "customer-local"
    smoke_path = deployment / "smoke_test.py"
    smoke_tree = ast.parse(smoke_path.read_text(encoding="utf-8"))
    reset_calls = [
        node
        for node in ast.walk(smoke_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reset"
    ]
    assert len(reset_calls) == 1
    reset_arguments = {
        keyword.arg: ast.literal_eval(keyword.value)
        for keyword in reset_calls[0].keywords
        if keyword.arg is not None
    }
    assert (reset_arguments["suite"], reset_arguments["task_id"], reset_arguments["variant"]) == (
        "libero_goal",
        9,
        "base",
    )

    customer_readme = (deployment / "README.md").read_text(encoding="utf-8")
    technical_plan = (ROOT / "docs" / "customer-local-deployment-technical-plan.md").read_text(
        encoding="utf-8"
    )
    assert 'suite="libero_goal",\n    task_id=9,' in customer_readme
    assert 'suite="libero_goal",\n    task_id=9,' in technical_plan
