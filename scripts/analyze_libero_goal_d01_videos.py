from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


VIDEO_ROOT = Path(r"C:\Users\racin\Desktop\general\data\videos")
OUT = Path(r"D:\LIBERO-PRO\outputs\libero_goal_D01_video_check_20260819")


def read_frames(path: Path) -> list[np.ndarray]:
    capture = cv2.VideoCapture(str(path))
    frames: list[np.ndarray] = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(frame)
    capture.release()
    return frames


def make_contact(task: int, seed: int, init: int, base: Path, d01: Path) -> dict[str, object]:
    base_frames = read_frames(base)
    d01_frames = read_frames(d01)
    if not base_frames or not d01_frames:
        return {
            "task": task,
            "seed": seed,
            "init": init,
            "base_video": str(base),
            "d01_video": str(d01),
            "base_frames": len(base_frames),
            "d01_frames": len(d01_frames),
            "status": "unreadable",
        }
    rows = []
    for label, frames in (("BASE", base_frames), ("D01", d01_frames)):
        indices = np.linspace(0, len(frames) - 1, 8, dtype=int)
        samples = []
        for index in indices:
            frame = frames[int(index)].copy()
            cv2.putText(
                frame,
                f"{label} f{index}/{len(frames)-1}",
                (5, 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 0, 0),
                1,
                cv2.LINE_AA,
            )
            samples.append(frame)
        rows.append(np.concatenate(samples, axis=1))
    sheet = np.concatenate(rows, axis=0)
    contact_path = OUT / f"task{task}_seed{seed}_contact.jpg"
    cv2.imwrite(str(contact_path), sheet)

    timeline_samples = []
    for index in np.linspace(0, len(d01_frames) - 1, 25, dtype=int):
        frame = d01_frames[int(index)].copy()
        cv2.putText(
            frame,
            f"D01 f{index}",
            (5, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 0, 0),
            1,
            cv2.LINE_AA,
        )
        timeline_samples.append(frame)
    timeline_rows = [
        np.concatenate(timeline_samples[start : start + 5], axis=1)
        for start in range(0, len(timeline_samples), 5)
    ]
    timeline = np.concatenate(timeline_rows, axis=0)
    timeline_path = OUT / f"task{task}_seed{seed}_timeline.jpg"
    cv2.imwrite(str(timeline_path), timeline)

    paired = min(len(base_frames), len(d01_frames))
    frame_delta = np.asarray(
        [
            float(np.mean(cv2.absdiff(base_frames[index], d01_frames[index])))
            for index in range(paired)
        ],
        dtype=float,
    )
    summary = {
        "task": task,
        "seed": seed,
        "init": init,
        "base_video": str(base),
        "d01_video": str(d01),
        "base_frames": len(base_frames),
        "d01_frames": len(d01_frames),
        "paired_frames": paired,
        "mean_aligned_frame_delta": round(float(frame_delta.mean()), 4),
        "max_aligned_frame_delta": round(float(frame_delta.max()), 4),
        "max_delta_frame": int(frame_delta.argmax()),
        "contact_sheet": str(contact_path),
        "timeline_sheet": str(timeline_path),
    }
    return summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    skipped = []
    for task in range(10):
        for seed, init in ((142, 0), (143, 1)):
            base = VIDEO_ROOT / "success" / f"pi0_libero_goal_task{task}_base_seed{seed}_init{init}.mp4"
            if not base.exists():
                base = VIDEO_ROOT / "failure" / base.name
            d01_name = base.name.replace("_base_", "_D01_")
            d01 = base.parent / d01_name
            if not d01.exists():
                d01 = (VIDEO_ROOT / "failure" / d01_name)
            if base.exists() and d01.exists():
                result = make_contact(task, seed, init, base, d01)
                if result.get("status") == "unreadable":
                    skipped.append(result)
                else:
                    results.append(result)
    (OUT / "video_metrics.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "unreadable_videos.json").write_text(
        json.dumps(skipped, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
