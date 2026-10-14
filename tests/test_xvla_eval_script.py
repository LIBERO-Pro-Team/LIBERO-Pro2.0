import io
import sys
from datetime import datetime, timezone

from scripts import run_xvla_remote_eval
from libero_remote.runner.xvla import EpisodeResult


def test_xvla_uses_manifest_default_step_limit(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_xvla_remote_eval.py"])

    args = run_xvla_remote_eval.parse_args()

    assert args.max_steps is None


def test_xvla_variant_reaches_step_resolution_manifest_and_episode(
    monkeypatch, tmp_path
) -> None:
    model_path = tmp_path / "model"
    tokenizer_path = tmp_path / "tokenizer"
    lerobot_root = tmp_path / "lerobot"
    for path in (model_path, tokenizer_path, lerobot_root):
        path.mkdir()
    output = tmp_path / "result.jsonl"
    captured = {}

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_xvla_remote_eval.py",
            "--model-path",
            str(model_path),
            "--tokenizer-path",
            str(tokenizer_path),
            "--lerobot-root",
            str(lerobot_root),
            "--suite",
            "libero_spatial",
            "--task-id",
            "3",
            "--variant",
            "D01",
            "--seed",
            "143",
            "--output",
            str(output),
        ],
    )
    monkeypatch.setattr(
        run_xvla_remote_eval,
        "read_health",
        lambda *_args, **_kwargs: {"status": "ok"},
    )
    monkeypatch.setattr(
        run_xvla_remote_eval,
        "read_json",
        lambda *_args, **_kwargs: {"control_modes": ["absolute"]},
    )

    def resolve_steps(catalog, suite, task_id, variant):
        captured["step_resolution"] = (catalog, suite, task_id, variant)
        return 500

    monkeypatch.setattr(
        run_xvla_remote_eval, "resolve_catalog_max_steps", resolve_steps
    )

    def build_manifest(**kwargs):
        captured["evaluation"] = kwargs["evaluation"]
        return object()

    monkeypatch.setattr(run_xvla_remote_eval, "build_run_manifest", build_manifest)
    monkeypatch.setattr(run_xvla_remote_eval, "append_run_manifest", lambda *_: None)
    monkeypatch.setattr(run_xvla_remote_eval, "append_episode_result", lambda *_: None)
    monkeypatch.setattr(
        run_xvla_remote_eval.XVLAPolicyAdapter,
        "load",
        lambda *_args, **_kwargs: object(),
    )

    class FakeEnv:
        def __init__(self, *_args, **_kwargs):
            pass

        def close_transport(self):
            pass

    monkeypatch.setattr(run_xvla_remote_eval, "RemoteLiberoEnv", FakeEnv)

    def run_episode(_env, _policy, spec):
        captured["spec"] = spec
        now = datetime.now(timezone.utc).isoformat()
        return EpisodeResult(
            status="completed",
            suite=spec.suite,
            task_id=spec.task_id,
            init_state_id=spec.init_state_id,
            seed=spec.seed,
            session_id="session",
            episode_id="episode",
            steps=1,
            total_reward=0.0,
            success=False,
            terminated=False,
            truncated=True,
            started_at=now,
            duration_seconds=0.1,
        )

    monkeypatch.setattr(run_xvla_remote_eval, "run_remote_episode", run_episode)

    run_xvla_remote_eval.main()

    assert captured["step_resolution"][1:] == ("libero_spatial", 3, "D01")
    assert captured["evaluation"]["variant"] == "D01"
    assert captured["spec"].variant == "D01"


def test_metadata_request_uses_configured_timeout(monkeypatch) -> None:
    requested = {}

    def fake_urlopen(url: str, timeout: float):
        requested.update(url=url, timeout=timeout)
        return io.BytesIO(b'{"status":"ok"}')

    monkeypatch.setattr(run_xvla_remote_eval, "urlopen", fake_urlopen)

    payload = run_xvla_remote_eval.read_json(
        "http://127.0.0.1:8000", "/v1/tasks", timeout=120.0
    )

    assert payload == {"status": "ok"}
    assert requested == {
        "url": "http://127.0.0.1:8000/v1/tasks",
        "timeout": 120.0,
    }
