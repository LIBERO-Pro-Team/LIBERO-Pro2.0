"""Acceptance checks for local and remote evaluation equivalence."""

from .equivalence import (
    compare_observations,
    validate_messagepack_roundtrip,
    validate_xvla_adapter_mapping,
)

__all__ = [
    "compare_observations",
    "validate_messagepack_roundtrip",
    "validate_xvla_adapter_mapping",
]
