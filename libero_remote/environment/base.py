"""Small interface hiding environment-specific initialization and state."""

from abc import ABC, abstractmethod
from typing import Any, Dict

import numpy as np


class EnvironmentAdapter(ABC):
    @abstractmethod
    def create(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Create the environment and return the first episode observation."""

    @abstractmethod
    def reset(self, init_state_id: int, seed: int) -> Dict[str, Any]:
        """Start another episode in the same environment."""

    @abstractmethod
    def step(self, action: np.ndarray) -> Dict[str, Any]:
        """Advance the environment exactly once."""

    @abstractmethod
    def close(self) -> None:
        """Release all simulator and rendering resources."""
