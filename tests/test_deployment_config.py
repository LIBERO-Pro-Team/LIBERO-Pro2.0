import ast
import hashlib
import json
import shutil
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
    assert "gpus: all" not in compose
    assert "deploy:" in compose
    assert "reservations:" in compose
    assert "devices:" in compose
    assert "driver: nvidia" in compose
    assert "capabilities: [gpu]" in compose
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


def test_customer_bundle_includes_current_offline_operating_documents(
    tmp_path: Path,
) -> None:
    builder = (ROOT / "scripts" / "build_customer_bundle.ps1").read_text(
        encoding="utf-8"
    )
    required_documents = {
        "customer-local-deployment-technical-plan.md",
        "model-adapter-contract.md",
        "LIBERO-Pro2.0_远程评测可靠性与多用户并发修复方案.md",
        "remote-run-scheduler.md",
    }

    manifest_path = ROOT / "scripts" / "customer-documents.json"
    destination = tmp_path / "docs"
    powershell = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            (
                "$ErrorActionPreference='Stop';"
                f"$manifest=Get-Content -LiteralPath '{manifest_path}' "
                "-Raw -Encoding UTF8 | ConvertFrom-Json;"
                f"New-Item -ItemType Directory -Path '{destination}' | Out-Null;"
                "$manifest | ForEach-Object {"
                f"Copy-Item -LiteralPath (Join-Path '{ROOT / 'docs'}' $_) "
                f"-Destination (Join-Path '{destination}' $_)"
                "};"
                f"Get-ChildItem -LiteralPath '{destination}' -File | "
                "Select-Object -ExpandProperty Name | ConvertTo-Json -Compress"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
    )
    copied_documents = set(json.loads(powershell.stdout))

    for document in required_documents:
        assert (ROOT / "docs" / document).is_file()
    assert copied_documents == required_documents
    assert "Get-Content -LiteralPath $customerDocumentManifest" in builder
    assert "-Raw -Encoding UTF8 | ConvertFrom-Json" in builder
    assert "Copy-Item -LiteralPath $documentSource -Destination $documentDestination" in builder
    assert not any(line.rstrip().endswith("\\") for line in builder.splitlines())


def test_customer_bundle_checksum_manifest_supports_unicode_paths(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "普通文件.txt").write_text("unicode path", encoding="utf-8")
    manifest = bundle / "SHA256SUMS"
    writer = ROOT / "scripts" / "write_sha256_manifest.ps1"
    builder = (ROOT / "scripts" / "build_customer_bundle.ps1").read_text(
        encoding="utf-8"
    )

    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-File",
            str(writer),
            "-Root",
            str(bundle),
            "-OutputFile",
            str(manifest),
        ],
        check=True,
    )
    assert 'Join-Path $PSScriptRoot "write_sha256_manifest.ps1"' in builder
    assert '[IO.File]::WriteAllText(' in builder

    manifest_bytes = manifest.read_bytes()
    assert not manifest_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in manifest_bytes
    assert "普通文件.txt" in manifest_bytes.decode("utf-8")
    wsl_bundle = f"/mnt/{bundle.drive[0].lower()}/{bundle.as_posix()[3:]}"
    subprocess.run(
        [
            "wsl.exe",
            "--cd",
            wsl_bundle,
            "--",
            "sha256sum",
            "-c",
            "SHA256SUMS",
        ],
        check=True,
    )


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


def test_customer_healthcheck_waits_through_startup_failures(tmp_path: Path) -> None:
    healthcheck = tmp_path / "healthcheck.sh"
    shutil.copy2(ROOT / "deploy" / "customer-local" / "healthcheck.sh", healthcheck)
    wsl_dir = f"/mnt/{tmp_path.drive[0].lower()}/{tmp_path.as_posix()[3:]}"
    harness = f"""
set -euo pipefail
cd {wsl_dir!r}
cat > startup_server.py <<'PY'
import json
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    attempts = 0

    def do_GET(self):
        type(self).attempts += 1
        if type(self).attempts == 1:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        status = 503 if type(self).attempts == 2 else 200
        payload = json.dumps({{"status": "not_ready" if status == 503 else "ok"}}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        if status == 200:
            self.server.shutdown_requested = True

    def log_message(self, format, *args):
        return


server = HTTPServer(("127.0.0.1", 0), Handler)
with open("port", "w", encoding="utf-8") as output:
    output.write(str(server.server_port))
while not getattr(server, "shutdown_requested", False):
    server.handle_request()
PY
python3 startup_server.py &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true' EXIT
for _ in $(seq 1 50); do
  test -s port && break
  sleep 0.02
done
test -s port
cat > client.env <<EOF
LIBERO_REMOTE_URL=http://127.0.0.1:$(cat port)
LIBERO_REMOTE_API_KEY=test-key
EOF
LIBERO_REMOTE_HEALTHCHECK_TIMEOUT_SECONDS=5 \
LIBERO_REMOTE_HEALTHCHECK_INTERVAL_SECONDS=0.05 \
bash healthcheck.sh
wait "$server_pid"
"""

    result = subprocess.run(
        ["wsl.exe", "bash", "-s"],
        input=harness.encode("utf-8"),
        capture_output=True,
    )

    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    assert '"status": "ok"' in output


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


def test_customer_technical_plan_matches_the_released_bundle_workflow() -> None:
    technical_plan = (ROOT / "docs" / "customer-local-deployment-technical-plan.md").read_text(
        encoding="utf-8"
    )

    assert "版本：1.0.0（2026-08-03）" in technical_plan
    assert "libero-pro-bundle-1.0.0.tar.gz" in technical_plan
    assert "bash install.sh" in technical_plan
    assert "LIBERO_REMOTE_MAX_SESSIONS" in technical_plan
    assert "LIBERO_REMOTE_MAX_ACTIVE_SESSIONS_PER_OWNER" in technical_plan
    assert "bash add_account.sh team-b" in technical_plan
    assert "169 个有效任务组合" in technical_plan
    assert "AgentAdapter" in technical_plan
    assert "GitHub 不是客户部署来源" in technical_plan
    for obsolete in (
        "libero-pro-bundle-v1.0.0",
        "libero-pro-server-v1.0.0.tar",
        "LIBERO_MAX_SESSIONS",
        "LIBERO_API_TOKEN",
        "API_TOKEN=replace-with-random-token",
        "cp .env.example .env",
    ):
        assert obsolete not in technical_plan
