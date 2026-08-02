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
