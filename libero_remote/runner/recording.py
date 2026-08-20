"""Model-neutral recording helpers for scheduled agent adapters."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

import numpy as np

from .scheduled import AgentAdapter, AgentContext


class EpisodeRecorder(Protocol):
    def reset(self, context: AgentContext) -> None:
        """Prepare to record one independently reset episode."""

    def record(self, observation: Dict[str, Any]) -> None:
        """Record one platform observation without changing it."""

    def close(self) -> None:
        """Flush resources owned by the recorder."""


class RecordingAgentAdapter:
    """Add observation recording around any model-neutral AgentAdapter."""

    def __init__(self, adapter: AgentAdapter, recorder: EpisodeRecorder) -> None:
        self._adapter = adapter
        self._recorder = recorder

    def reset(self, context: AgentContext) -> None:
        self._recorder.reset(context)
        self._adapter.reset(context)

    def act(self, observation: Dict[str, Any]) -> np.ndarray:
        self._recorder.record(observation)
        return self._adapter.act(observation)

    def close(self) -> None:
        try:
            self._recorder.close()
        finally:
            self._adapter.close()


class RolloutVideoRecorder:
    """Persist one configured RGB observation field and generic episode metadata."""

    def __init__(
        self,
        output_root: Path,
        image_field: str = "agentview_image",
        fps: int = 20,
    ) -> None:
        if not image_field:
            raise ValueError("image_field must not be empty")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.output_root = Path(output_root)
        self.image_field = image_field
        self.fps = int(fps)
        self._writer: Optional[Any] = None
        self._last_frame_bgr: Optional[np.ndarray] = None
        self._frame_count = 0
        self._episode_dir: Optional[Path] = None
        self._context: Optional[AgentContext] = None

    def reset(self, context: AgentContext) -> None:
        self.close()
        spec = context.episode_spec
        case_id = str(spec.get("variant", "base")).upper()
        self._episode_dir = (
            self.output_root
            / str(spec["suite"])
            / f"task_{int(spec['task_id']):02d}"
            / case_id
            / f"init_{int(spec.get('init_state_id', 0)):03d}"
            / f"seed_{int(spec['seed'])}"
        )
        self._episode_dir.mkdir(parents=True, exist_ok=True)
        self._context = context
        self._writer = None
        self._last_frame_bgr = None
        self._frame_count = 0

    def record(self, observation: Dict[str, Any]) -> None:
        if self.image_field not in observation:
            raise ValueError(f"Observation is missing recorded image field {self.image_field!r}")
        rgb = np.ascontiguousarray(observation[self.image_field], dtype=np.uint8)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise ValueError(f"Expected HWC RGB frame, got {rgb.shape}")

        import cv2

        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        if self._writer is None:
            if self._episode_dir is None:
                raise RuntimeError("Recorder has not been reset")
            height, width = bgr.shape[:2]
            self._writer = cv2.VideoWriter(
                str(self._episode_dir / "rollout.mp4"),
                cv2.VideoWriter_fourcc(*"mp4v"),
                self.fps,
                (width, height),
            )
            if not self._writer.isOpened():
                raise RuntimeError("Could not open MP4 writer")
            cv2.imwrite(str(self._episode_dir / "initial.png"), bgr)
        self._writer.write(bgr)
        self._last_frame_bgr = bgr
        self._frame_count += 1

    def close(self) -> None:
        if self._writer is None:
            return
        if self._last_frame_bgr is not None:
            self._writer.write(self._last_frame_bgr)
        self._writer.release()
        self._writer = None
        self._write_metadata()

    def _write_metadata(self) -> None:
        if self._episode_dir is None or self._context is None:
            return
        payload = {
            "run_id": self._context.run_id,
            "job_id": self._context.job_id,
            "job_index": self._context.job_index,
            "episode_spec": self._context.episode_spec,
            "language_instruction": self._context.language_instruction,
            "action_schema": self._context.action_schema,
            "observation_schema_version": self._context.observation_schema_version,
            "recorded_observation_field": self.image_field,
            "frame_count_before_terminal_duplicate": self._frame_count,
            "video_fps": self.fps,
        }
        (self._episode_dir / "adapter.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
