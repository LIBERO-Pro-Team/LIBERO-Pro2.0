import io

from scripts import run_xvla_remote_eval


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
