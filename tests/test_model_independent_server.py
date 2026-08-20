import subprocess
import sys
from pathlib import Path

SERVER_SIDE_PACKAGES = (
    "server",
    "scheduler",
    "environment",
    "protocol",
    "worker",
)
MODEL_MODULE_NAMES = ("xvla", "pi0")


def test_server_side_packages_do_not_import_model_adapters() -> None:
    package_root = Path(__file__).parents[1] / "libero_remote"

    violations = []
    for package_name in SERVER_SIDE_PACKAGES:
        for path in (package_root / package_name).rglob("*.py"):
            source = path.read_text(encoding="utf-8").lower()
            for model_name in MODEL_MODULE_NAMES:
                if f"runner.{model_name}" in source:
                    violations.append(f"{path.relative_to(package_root)} imports {model_name}")

    assert violations == []


def test_generic_runner_import_does_not_load_reference_model_adapters() -> None:
    script = """
import sys
import libero_remote.runner

loaded = sorted(
    name
    for name in sys.modules
    if name in {"libero_remote.runner.xvla", "libero_remote.runner.pi0"}
)
if loaded:
    raise SystemExit(f"generic runner loaded reference adapters: {loaded}")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_recording_adapter_import_does_not_load_model_or_vision_dependencies() -> None:
    script = """
import sys
import libero_remote.runner.recording

blocked = (
    "libero_remote.runner.xvla",
    "libero_remote.runner.pi0",
    "torch",
    "lerobot",
    "cv2",
)
loaded = sorted(
    name
    for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in blocked)
)
if loaded:
    raise SystemExit(f"recording adapter loaded specialized dependencies: {loaded}")
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
