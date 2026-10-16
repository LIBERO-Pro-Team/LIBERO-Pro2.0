import ast
import hashlib
import json
import shutil
import socket
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
DEPLOYMENT = ROOT / "deploy" / "customer-conda"


def _wsl_path(path: Path) -> str:
    return f"/mnt/{path.drive[0].lower()}/{path.as_posix()[3:]}"


def test_conda_delivery_locks_the_v100_runtime() -> None:
    baseline = json.loads((DEPLOYMENT / "SOURCE_BASELINE.json").read_text(encoding="utf-8"))

    assert baseline == {
        "reference_version": "1.0.0",
        "service_commit": "82c829c290bb011f828b80e117a5c7a0262337e1",
        "simulator_commit": "c02ee2c8255db1c36664fad978197c47e495f178",
        "reference_image": "libero-pro-server:1.0.0",
        "reference_image_digest": (
            "sha256:969cdf6bc1a3a9f50ce5529bfd7aab6e746d53f9b3d03333bbe793636ba4f933"
        ),
        "python_version": "3.8.10",
        "task_count": 1680,
    }

    requirements = (DEPLOYMENT / "requirements-lock.txt").read_text(
        encoding="utf-8"
    )
    requirement_lines = [
        line
        for line in requirements.splitlines()
        if line and not line.startswith("#") and not line.startswith("--")
    ]
    assert requirement_lines
    assert all("==" in line for line in requirement_lines)
    assert "torch==1.11.0+cpu" in requirement_lines
    assert "torchvision==0.12.0+cpu" in requirement_lines
    assert "mujoco==3.2.3" in requirement_lines
    assert "robosuite==1.4.0" in requirement_lines
    assert "numpy==1.22.4" in requirement_lines
    assert "fastapi==0.103.2" in requirement_lines
    assert "uvicorn==0.23.2" in requirement_lines
    assert "pip==24.3.1" in requirement_lines
    assert "setuptools==75.3.4" in requirement_lines
    assert "wheel==0.45.1" in requirement_lines
    assert not any(line.startswith(("libero==", "libero-remote==")) for line in requirement_lines)

    assert (DEPLOYMENT / "requirements.txt").read_text(encoding="utf-8") == (
        "-r requirements-lock.txt\n"
    )
    environment = (DEPLOYMENT / "environment.yml").read_text(encoding="utf-8")
    assert "  - nodefaults\n" in environment
    assert "python=3.8.10" in environment
    assert "pip=24.3.1" in environment
    assert "libegl" in environment
    assert "libglvnd" in environment
    assert "mesalib" in environment
    assert "openmpi" in environment


def test_conda_installer_creates_a_regular_user_environment(tmp_path: Path) -> None:
    deployment = tmp_path / "bundle"
    fake_bin = tmp_path / "fake-bin"
    deployment.mkdir()
    fake_bin.mkdir()
    shutil.copy2(DEPLOYMENT / "install.sh", deployment)
    for source_name in ("service-source", "simulator-source"):
        source = deployment / source_name
        source.mkdir()
        (source / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    for filename in ("environment.yml", "requirements-lock.txt"):
        shutil.copy2(DEPLOYMENT / filename, deployment)

    fake_conda = fake_bin / "conda"
    fake_conda.write_bytes(
        b"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$FAKE_CONDA_LOG"
if [[ "$1 $2" == "env create" ]]; then
  while (($#)); do
    if [[ "$1" == "--prefix" ]]; then
      mkdir -p "$2/bin"
      exit 0
    fi
    shift
  done
fi
""",
    )

    wsl_root = _wsl_path(tmp_path)
    harness = f"""
set -euo pipefail
chmod +x {wsl_root!r}/fake-bin/conda
export PATH={wsl_root!r}/fake-bin:$PATH
export FAKE_CONDA_LOG={wsl_root!r}/conda.log
bash {wsl_root!r}/bundle/install.sh {wsl_root!r}/envs/libero-pro2
"""
    result = subprocess.run(
        ["wsl.exe", "bash", "-s"],
        input=harness.encode("utf-8"),
        capture_output=True,
    )

    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    calls = (tmp_path / "conda.log").read_text(encoding="utf-8").splitlines()
    prefix = f"{wsl_root}/envs/libero-pro2"
    assert calls == [
        (
            f"env create --solver classic --yes --prefix {prefix} --file "
            f"{wsl_root}/bundle/environment.yml"
        ),
        (
            f"run --prefix {prefix} python -m pip install --requirement "
            f"{wsl_root}/bundle/requirements-lock.txt"
        ),
        (
            f"run --prefix {prefix} python -m pip install --no-build-isolation "
            f"--no-deps --editable "
            f"{wsl_root}/bundle/simulator-source"
        ),
        (
            f"run --prefix {prefix} python -m pip install --no-build-isolation "
            f"--no-deps --editable "
            f"{wsl_root}/bundle/service-source"
        ),
    ]
    installer = (DEPLOYMENT / "install.sh").read_text(encoding="utf-8").lower()
    assert "conda_no_plugins=true" in installer
    assert "sudo" not in installer
    assert "docker" not in installer


def test_conda_configuration_separates_server_and_client_secrets(
    tmp_path: Path,
) -> None:
    deployment = tmp_path / "bundle"
    deployment.mkdir()
    shutil.copy2(DEPLOYMENT / "configure.sh", deployment)
    shutil.copy2(DEPLOYMENT / "SOURCE_BASELINE.json", deployment)
    for relative in (
        "service-source/assets/bddl/libero-pro2.0-1680-v1",
        "simulator-source",
    ):
        (deployment / relative).mkdir(parents=True)
    (deployment / "service-source/assets/task_manifest.json").write_text(
        "{}\n", encoding="utf-8"
    )

    wsl_root = _wsl_path(tmp_path)
    harness = f"""
set -euo pipefail
cd {wsl_root!r}/bundle
mkdir -p {wsl_root!r}/conda/bin
ln -s /usr/bin/python3 {wsl_root!r}/conda/bin/python
LIBERO_REMOTE_PORT=18000 \\
LIBERO_REMOTE_PUBLIC_URL=http://127.0.0.1:18000 \\
bash configure.sh {wsl_root!r}/conda
(
  set -a
  source server.env
  set +a
  python3 - <<'PY'
import json
import os

values = {{
    key: value
    for key, value in os.environ.items()
    if key.startswith("LIBERO_") or key in {{"MUJOCO_GL", "PYOPENGL_PLATFORM"}}
}}
with open("server.resolved.json", "w", encoding="utf-8") as output:
    json.dump(values, output, sort_keys=True)
PY
)
(
  set -a
  source client.env
  set +a
  python3 - <<'PY'
import json
import os

values = {{key: value for key, value in os.environ.items() if key.startswith("LIBERO_")}}
with open("client.resolved.json", "w", encoding="utf-8") as output:
    json.dump(values, output, sort_keys=True)
PY
)
cp server.env server.before
cp client.env client.before
if bash configure.sh {wsl_root!r}/conda; then
  echo 'configure unexpectedly replaced credentials' >&2
  exit 1
fi
cmp server.before server.env
cmp client.before client.env
permission_dir="$(mktemp -d)"
trap 'rm -rf "$permission_dir"' EXIT
cp configure.sh SOURCE_BASELINE.json "$permission_dir/"
mkdir -p \
  "$permission_dir/service-source/assets/bddl/libero-pro2.0-1680-v1" \
  "$permission_dir/simulator-source"
printf '{{}}\n' > "$permission_dir/service-source/assets/task_manifest.json"
(
  cd "$permission_dir"
  bash configure.sh {wsl_root!r}/conda >/dev/null
  printf 'MODES=%s %s\n' "$(stat -c '%a' server.env)" "$(stat -c '%a' client.env)"
)
"""
    result = subprocess.run(
        ["wsl.exe", "bash", "-s"],
        input=harness.encode("utf-8"),
        capture_output=True,
    )

    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    assert "MODES=600 600" in output
    server = json.loads((deployment / "server.resolved.json").read_text(encoding="utf-8"))
    client = json.loads((deployment / "client.resolved.json").read_text(encoding="utf-8"))
    api_key = client["LIBERO_REMOTE_API_KEY"]
    api_hashes = json.loads(server["LIBERO_REMOTE_API_KEY_HASHES"])
    assert api_hashes == {
        hashlib.sha256(api_key.encode("utf-8")).hexdigest(): "local-account"
    }
    assert api_key not in (deployment / "server.env").read_text(encoding="utf-8")
    assert client["LIBERO_REMOTE_URL"] == "http://127.0.0.1:18000"
    assert server["LIBERO_REMOTE_HOST"] == "127.0.0.1"
    assert server["LIBERO_REMOTE_PORT"] == "18000"
    assert server["LIBERO_REMOTE_BACKEND"] == "libero"
    assert server["LIBERO_REMOTE_AUTHENTICATION_REQUIRED"] == "true"
    assert server["LIBERO_REMOTE_ALLOW_DIRECT_SESSIONS"] == "true"
    assert server["MUJOCO_GL"] == "egl"
    assert server["PYOPENGL_PLATFORM"] == "egl"
    assert server["LIBERO_REMOTE_COMMIT"] == (
        "82c829c290bb011f828b80e117a5c7a0262337e1"
    )
    assert server["LIBERO_PRO_COMMIT"] == (
        "c02ee2c8255db1c36664fad978197c47e495f178"
    )
    assert server["LIBERO_PRO_CONDA_PREFIX"] == f"{wsl_root}/conda"
    assert server["LIBERO_PRO_ROOT"] == f"{wsl_root}/bundle/simulator-source"
    assert server["LIBERO_REMOTE_TASK_MANIFEST"] == (
        f"{wsl_root}/bundle/service-source/assets/task_manifest.json"
    )
    assert server["LIBERO_REMOTE_BDDL_ROOT"] == (
        f"{wsl_root}/bundle/service-source/assets/bddl/libero-pro2.0-1680-v1"
    )
    assert server["LIBERO_CONFIG_PATH"] == f"{wsl_root}/bundle/runtime/libero-config"
    assert server["LIBERO_REMOTE_SCHEDULER_DB_PATH"] == (
        f"{wsl_root}/bundle/runtime/scheduler.sqlite3"
    )
    assert server["LIBERO_REMOTE_IMAGE_DIGEST"] == ""


def test_conda_credential_scripts_are_python_38_compatible() -> None:
    for filename in ("configure.sh", "add_account.sh"):
        source = (DEPLOYMENT / filename).read_text(encoding="utf-8")
        assert "write_text(" not in source
        assert "newline=\"\\n\"" in source


def test_conda_service_lifecycle_runs_without_privileged_tools(tmp_path: Path) -> None:
    deployment = tmp_path / "bundle"
    conda_bin = tmp_path / "conda" / "bin"
    deployment.mkdir()
    conda_bin.mkdir(parents=True)
    for filename in ("_runtime.sh", "start.sh", "stop.sh", "status.sh", "healthcheck.sh"):
        shutil.copy2(DEPLOYMENT / filename, deployment)

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    fake_server = conda_bin / "libero-remote-server"
    fake_server.write_bytes(
        b"""#!/usr/bin/python3
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        payload = json.dumps({"status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return


HTTPServer(
    (os.environ["LIBERO_REMOTE_HOST"], int(os.environ["LIBERO_REMOTE_PORT"])),
    Handler,
).serve_forever()
"""
    )
    (conda_bin / "python").write_bytes(b"#!/usr/bin/env bash\nexec /usr/bin/python3 \"$@\"\n")

    wsl_root = _wsl_path(tmp_path)
    (deployment / "server.env").write_bytes(
        "\n".join(
            (
                f"LIBERO_PRO_CONDA_PREFIX={wsl_root}/conda",
                "LIBERO_REMOTE_HOST=127.0.0.1",
                f"LIBERO_REMOTE_PORT={port}",
                "",
            )
        ).encode("utf-8"),
    )
    (deployment / "client.env").write_bytes(
        "\n".join(
            (
                f"LIBERO_REMOTE_URL=http://127.0.0.1:{port}",
                "LIBERO_REMOTE_API_KEY=test-key",
                "",
            )
        ).encode("utf-8"),
    )
    harness = f"""
set -euo pipefail
cd {wsl_root!r}/bundle
chmod +x {wsl_root!r}/conda/bin/python {wsl_root!r}/conda/bin/libero-remote-server
bash start.sh
bash status.sh
LIBERO_REMOTE_HEALTHCHECK_TIMEOUT_SECONDS=5 \\
LIBERO_REMOTE_HEALTHCHECK_INTERVAL_SECONDS=0.05 \\
bash healthcheck.sh
bash stop.sh
if bash status.sh; then
  echo 'service remained running after stop' >&2
  exit 1
fi
test ! -e runtime/server.pid
test ! -e runtime/server.starttime
"""
    result = subprocess.run(
        ["wsl.exe", "bash", "-s"],
        input=harness.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )

    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    assert '"status": "ok"' in output
    assert "Service is running" in output
    assert "Service stopped" in output
    scripts = "\n".join(
        (DEPLOYMENT / filename).read_text(encoding="utf-8").lower()
        for filename in ("start.sh", "stop.sh", "status.sh", "healthcheck.sh")
    )
    assert "sudo" not in scripts
    assert "docker" not in scripts


def test_conda_smoke_test_uses_the_reproducible_published_base_case() -> None:
    smoke_path = DEPLOYMENT / "smoke_test.py"
    source = smoke_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    reset_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "reset"
    ]
    assert len(reset_calls) == 1
    arguments = {
        keyword.arg: ast.literal_eval(keyword.value)
        for keyword in reset_calls[0].keywords
        if keyword.arg is not None
    }
    assert arguments == {
        "suite": "libero_goal",
        "task_id": 9,
        "init_state_id": 0,
        "seed": 142,
        "variant": "base",
        "camera_height": 64,
        "camera_width": 64,
        "max_steps": 1,
    }
    assert 'os.environ["LIBERO_REMOTE_API_KEY"]' in source
    assert "RemoteLiberoEnv" in source
    assert "np.zeros" in source
    assert "xvla" not in source.lower()
    assert "pi0" not in source.lower()


def _commit(repository: Path, message: str) -> str:
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Conda Bundle Test",
            "-c",
            "user.email=conda-bundle@example.invalid",
            "commit",
            "-q",
            "-m",
            message,
        ],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _assert_hash_manifest(root: Path, manifest_name: str) -> None:
    lines = (root / manifest_name).read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        digest, relative = line.split("  ", 1)
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest




def test_conda_docs_cover_regular_user_operation_and_headless_egl() -> None:
    readme = (DEPLOYMENT / "README.md").read_text(encoding="utf-8")
    egl_guide = (DEPLOYMENT / "EGL_HEADLESS.md").read_text(encoding="utf-8")

    for command in (
        "bash install.sh /data/user/envs/libero-pro2",
        "bash configure.sh /data/user/envs/libero-pro2",
        "bash start.sh",
        "bash status.sh",
        "bash healthcheck.sh",
        "bash stop.sh",
        "/data/user/envs/libero-pro2/bin/python smoke_test.py",
    ):
        assert command in readme
    assert "SOURCE_BASELINE.json" in readme
    assert "service_commit" in readme
    assert "c02ee2c8255db1c36664fad978197c47e495f178" in readme
    assert "sha256:969cdf6bc1a3a9f50ce5529bfd7aab6e746d53f9b3d03333bbe793636ba4f933" in readme
    assert "seed 142" in readme
    assert "AgentAdapter" in readme
    assert "root" in readme
    assert "Docker" in readme

    for variable in (
        "MUJOCO_GL=egl",
        "PYOPENGL_PLATFORM=egl",
        "CUDA_VISIBLE_DEVICES",
        "MUJOCO_EGL_DEVICE_ID",
        "LIBERO_PRO_ROOT",
        "LIBERO_CONFIG_PATH",
    ):
        assert variable in egl_guide
    for package_version in (
        "| `libegl1` | `1.3.2-1~ubuntu0.20.04.2` |",
        "| `libgl1` | `1.3.2-1~ubuntu0.20.04.2` |",
        "| `libglib2.0-0` | `2.64.6-1~ubuntu20.04.9` |",
        "| `libglvnd0` | `1.3.2-1~ubuntu0.20.04.2` |",
        "| `libopenmpi-dev` | `4.0.3-0ubuntu1` |",
        "| `libosmesa6` / `libosmesa6-dev` | `21.2.6-0ubuntu0.1~20.04.2` |",
        "| `libx11-6` | `2:1.6.9-2ubuntu1.6` |",
        "| `libxext6` | `2:1.3.4-0ubuntu1` |",
    ):
        assert package_version in egl_guide
    requirements = (DEPLOYMENT / "requirements-lock.txt").read_text(encoding="utf-8")
    assert "setuptools==75.3.4" in requirements
    assert "wheel==0.45.1" in requirements


def test_conda_account_provisioning_keeps_plaintext_keys_client_side(
    tmp_path: Path,
) -> None:
    deployment = tmp_path / "bundle"
    deployment.mkdir()
    for filename in ("_runtime.sh", "configure.sh", "add_account.sh", "SOURCE_BASELINE.json"):
        shutil.copy2(DEPLOYMENT / filename, deployment)
    for relative in (
        "service-source/assets/bddl/libero-pro2.0-1680-v1",
        "simulator-source",
    ):
        (deployment / relative).mkdir(parents=True)
    (deployment / "service-source/assets/task_manifest.json").write_text(
        "{}\n", encoding="utf-8"
    )

    wsl_root = _wsl_path(tmp_path)
    harness = f"""
set -euo pipefail
cd {wsl_root!r}/bundle
mkdir -p {wsl_root!r}/conda/bin
ln -s /usr/bin/python3 {wsl_root!r}/conda/bin/python
LIBERO_REMOTE_MAX_SESSIONS=2 bash configure.sh {wsl_root!r}/conda
bash add_account.sh team-b
cp server.env server.before-duplicate
cp client-team-b.env client-team-b.before-duplicate
if bash add_account.sh team-b; then
  echo 'duplicate account unexpectedly succeeded' >&2
  exit 1
fi
cmp server.before-duplicate server.env
cmp client-team-b.before-duplicate client-team-b.env
(
  set -a
  source server.env
  source client-team-b.env
  set +a
  python3 - <<'PY'
import json
import os

with open("accounts.resolved.json", "w", encoding="utf-8") as output:
    json.dump(
        {{
            "hashes": json.loads(os.environ["LIBERO_REMOTE_API_KEY_HASHES"]),
            "new_key": os.environ["LIBERO_REMOTE_API_KEY"],
            "url": os.environ["LIBERO_REMOTE_URL"],
        }},
        output,
        sort_keys=True,
    )
PY
)
"""
    result = subprocess.run(
        ["wsl.exe", "bash", "-s"],
        input=harness.encode("utf-8"),
        capture_output=True,
    )

    output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    assert result.returncode == 0, output
    accounts = json.loads(
        (deployment / "accounts.resolved.json").read_text(encoding="utf-8")
    )
    assert set(accounts["hashes"].values()) == {"local-account", "team-b"}
    assert accounts["hashes"][
        hashlib.sha256(accounts["new_key"].encode("utf-8")).hexdigest()
    ] == "team-b"
    assert accounts["url"] == "http://127.0.0.1:8000"
    assert accounts["new_key"] not in (deployment / "server.env").read_text(
        encoding="utf-8"
    )
