"""Lossless MessagePack encoding for protocol data and NumPy arrays."""

from typing import Any, Dict

import msgpack
import numpy as np

MESSAGEPACK_MEDIA_TYPE = "application/x-msgpack"
_NDARRAY_MARKER = "__libero_ndarray__"


class CodecError(ValueError):
    """Raised when a wire message cannot be encoded or decoded safely."""


def _encode_special(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        return {
            _NDARRAY_MARKER: True,
            "dtype": array.dtype.str,
            "shape": list(array.shape),
            "data": array.tobytes(order="C"),
        }
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Unsupported MessagePack value: {type(value)!r}")


def _decode_special(value: Dict[str, Any]) -> Any:
    if value.get(_NDARRAY_MARKER) is not True:
        return value

    try:
        dtype = np.dtype(value["dtype"])
        shape = tuple(int(dimension) for dimension in value["shape"])
        data = value["data"]
    except (KeyError, TypeError, ValueError) as error:
        raise CodecError("Invalid ndarray metadata") from error

    if any(dimension < 0 for dimension in shape) or not isinstance(data, bytes):
        raise CodecError("Invalid ndarray shape or data")

    expected_bytes = int(np.prod(shape, dtype=np.int64)) * dtype.itemsize
    if expected_bytes != len(data):
        raise CodecError("Ndarray byte length does not match its dtype and shape")

    return np.frombuffer(data, dtype=dtype).reshape(shape).copy(order="C")


def pack_message(message: Any) -> bytes:
    """Encode a protocol message without changing array values or layout."""

    try:
        return msgpack.packb(message, default=_encode_special, use_bin_type=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise CodecError("Message could not be encoded") from error


def unpack_message(payload: bytes) -> Any:
    """Decode a trusted-size protocol payload and validate array metadata."""

    if not isinstance(payload, bytes):
        raise CodecError("Message payload must be bytes")
    try:
        return msgpack.unpackb(
            payload,
            raw=False,
            object_hook=_decode_special,
            strict_map_key=False,
        )
    except (msgpack.UnpackException, ValueError, TypeError, OverflowError) as error:
        if isinstance(error, CodecError):
            raise
        raise CodecError("Message could not be decoded") from error
