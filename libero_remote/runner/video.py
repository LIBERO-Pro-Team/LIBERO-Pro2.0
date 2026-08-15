"""Optional MP4 recording for camera observations returned by remote rollouts."""

from pathlib import Path
from typing import Any, Mapping, Optional

import numpy as np


class ObservationVideoWriter:
    """Write one camera stream to an MP4 without coupling recording to a model."""

    def __init__(self, path: Path, *, camera: str = "agentview", fps: float = 20.0) -> None:
        if fps <= 0:
            raise ValueError("video fps must be positive")
        normalized_camera = camera.strip()
        if not normalized_camera:
            raise ValueError("video camera must not be empty")
        self.path = Path(path).expanduser().resolve()
        self.camera = normalized_camera
        self.fps = float(fps)
        self._writer: Optional[Any] = None
        self._frame_shape: Optional[tuple] = None

    @property
    def observation_key(self) -> str:
        if self.camera.endswith("_image"):
            return self.camera
        return f"{self.camera}_image"

    def write(self, observation: Mapping[str, Any]) -> None:
        """Append the selected HWC uint8 camera frame from an observation."""

        if self.observation_key not in observation:
            raise ValueError(
                f"Cannot record video: observation is missing {self.observation_key!r}"
            )
        frame = np.asarray(observation[self.observation_key])
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(
                "Video frames must have HWC RGB shape, "
                f"got {frame.shape} from {self.observation_key!r}"
            )
        if frame.dtype != np.uint8:
            raise ValueError(
                f"Video frames must use uint8 pixels, got {frame.dtype}"
            )
        shape = tuple(int(value) for value in frame.shape)
        if self._frame_shape is not None and shape != self._frame_shape:
            raise ValueError(
                f"Video frame shape changed from {self._frame_shape} to {shape}"
            )
        if self._writer is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                import imageio.v2 as imageio
            except ImportError as exc:
                raise RuntimeError(
                    "Video recording requires the optional video dependencies; "
                    "install libero-remote[video]"
                ) from exc
            self._writer = imageio.get_writer(
                str(self.path),
                mode="I",
                fps=self.fps,
                codec="libx264",
                pixelformat="yuv420p",
                macro_block_size=None,
            )
            self._frame_shape = shape
        self._writer.append_data(np.ascontiguousarray(frame))

    def close(self) -> None:
        """Finalize the MP4. Calling close more than once is safe."""

        if self._writer is not None:
            writer = self._writer
            self._writer = None
            writer.close()

    def __enter__(self) -> "ObservationVideoWriter":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        del exc_type, exc, traceback
        self.close()


def episode_video_path(
    video_dir: Path,
    *,
    model_name: str,
    suite: str,
    task_id: int,
    variant: str,
    seed: int,
    init_state_id: int,
) -> Path:
    """Return a deterministic, collision-resistant filename for one rollout."""

    safe_suite = _safe_component(suite)
    safe_variant = _safe_component(variant)
    safe_model = _safe_component(model_name)
    filename = (
        f"{safe_model}_{safe_suite}_task{task_id}_{safe_variant}_"
        f"seed{seed}_init{init_state_id}.mp4"
    )
    return Path(video_dir).expanduser().resolve() / filename


def _safe_component(value: str) -> str:
    normalized = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in str(value).strip()
    )
    return normalized or "unknown"
