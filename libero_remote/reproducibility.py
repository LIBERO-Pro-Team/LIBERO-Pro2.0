"""Canonical hashes shared by environment and scheduler boundaries."""

import hashlib
import json
from typing import Any

import numpy as np


def canonical_fingerprint(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def numerical_state_fingerprint(value: Any) -> str:
    state = np.ascontiguousarray(value, dtype="<f8")
    descriptor = json.dumps(
        {"dtype": "<f8", "shape": list(state.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(descriptor + b"\0" + state.tobytes(order="C")).hexdigest()
