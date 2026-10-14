import io
import sys
from pathlib import Path

import pytest

from scripts import run_pi0_remote_eval


def test_metadata_request_uses_configured_timeout(monkeypatch) -> None:
    requested = {}

    def fake_urlopen(url: str, timeout: float):
        requested.update(url=url, timeout=timeout)
        return io.BytesIO(b'{"status":"ok"}')

    monkeypatch.setattr(run_pi0_remote_eval, "urlopen", fake_urlopen)

    payload = run_pi0_remote_eval.read_json(
        "http://127.0.0.1:8000", "/v1/tasks", timeout=120.0
    )

    assert payload == {"status": "ok"}
    assert requested == {
        "url": "http://127.0.0.1:8000/v1/tasks",
        "timeout": 120.0,
    }


def test_pi0_clean_evaluation_defaults(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_pi0_remote_eval.py"])

    args = run_pi0_remote_eval.parse_args()

    assert args.suite == "libero_spatial"
    assert args.task_id == 8
    assert args.init_state_id == 0
    assert args.seed == 142
    assert args.max_steps is None
    assert args.variant == "base"


def test_pi0_artifact_validation_rejects_incomplete_checkpoint(tmp_path: Path) -> None:
    model_path = tmp_path / "model"
    tokenizer_path = tmp_path / "tokenizer"
    model_path.mkdir()
    tokenizer_path.mkdir()
    (model_path / "config.json").write_text("{}", encoding="utf-8")
    (tokenizer_path / "tokenizer.json").write_text("{}", encoding="utf-8")
    (tokenizer_path / "tokenizer_config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit, match="model.safetensors"):
        run_pi0_remote_eval.validate_pi0_artifacts(model_path, tokenizer_path)
