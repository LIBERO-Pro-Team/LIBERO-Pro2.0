"""Select an environment adapter without importing MuJoCo in the API process."""

from .base import EnvironmentAdapter


def create_environment_adapter(backend: str) -> EnvironmentAdapter:
    if backend == "fake":
        from .fake import FakeEnvironmentAdapter

        return FakeEnvironmentAdapter()
    if backend == "libero":
        from .libero import LiberoEnvironmentAdapter

        return LiberoEnvironmentAdapter()
    raise ValueError(f"Unknown environment backend: {backend}")
