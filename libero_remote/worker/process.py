"""Parent-side handle and child loop for isolated environment execution."""

import multiprocessing
from multiprocessing.connection import Connection
from typing import Any, Dict, Optional

import numpy as np

from libero_remote.environment import create_environment_adapter


class WorkerError(RuntimeError):
    pass


class WorkerTimeoutError(WorkerError):
    pass


class WorkerRemoteError(WorkerError):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(f"{error_type}: {message}")
        self.error_type = error_type
        self.remote_message = message


class EnvWorker:
    def __init__(
        self,
        process: Any,
        connection: Any,
        timeout_seconds: float,
    ) -> None:
        self._process = process
        self._connection = connection
        self._timeout_seconds = timeout_seconds
        self._closed = False

    @classmethod
    def start(cls, backend: str, timeout_seconds: float) -> "EnvWorker":
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe(duplex=True)
        process = context.Process(
            target=_worker_main,
            args=(child, backend),
            name="libero-env-worker",
            daemon=True,
        )
        process.start()
        child.close()
        return cls(process, parent, timeout_seconds)

    @property
    def is_alive(self) -> bool:
        return self._process.is_alive()

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid

    def create(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("create", spec=spec)

    def reset(self, init_state_id: int, seed: int) -> Dict[str, Any]:
        return self._call("reset", init_state_id=init_state_id, seed=seed)

    def step(self, action: np.ndarray) -> Dict[str, Any]:
        return self._call("step", action=np.ascontiguousarray(action, dtype=np.float32))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._process.is_alive():
            try:
                self._call("close")
            except Exception:
                pass
        try:
            self._connection.close()
        except (OSError, ValueError):
            pass
        self._process.join(timeout=2.0)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2.0)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=2.0)

    def terminate(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._connection.close()
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2.0)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=2.0)

    def _call(self, command: str, **payload: Any) -> Dict[str, Any]:
        if self._closed and command != "close":
            raise WorkerError("Worker is closed")
        if not self._process.is_alive():
            raise WorkerError("Worker process is not alive")
        try:
            self._connection.send({"command": command, "payload": payload})
        except (BrokenPipeError, EOFError, OSError) as error:
            raise WorkerError("Worker command could not be sent") from error

        if not self._connection.poll(self._timeout_seconds):
            self.terminate()
            raise WorkerTimeoutError(f"Worker command timed out: {command}")
        try:
            response = self._connection.recv()
        except (EOFError, OSError) as error:
            raise WorkerError("Worker exited before returning a response") from error

        if not response.get("ok"):
            raise WorkerRemoteError(
                str(response.get("error_type", "WorkerError")),
                str(response.get("message", "Unknown worker failure")),
            )
        result = response.get("result")
        return result if isinstance(result, dict) else {}


def _worker_main(connection: Connection, backend: str) -> None:
    adapter = create_environment_adapter(backend)
    try:
        while True:
            request = connection.recv()
            command = request.get("command")
            payload = request.get("payload", {})
            try:
                if command == "create":
                    result = adapter.create(payload["spec"])
                elif command == "reset":
                    result = adapter.reset(payload["init_state_id"], payload["seed"])
                elif command == "step":
                    result = adapter.step(payload["action"])
                elif command == "close":
                    adapter.close()
                    connection.send({"ok": True, "result": {}})
                    return
                else:
                    raise ValueError(f"Unknown worker command: {command}")
                connection.send({"ok": True, "result": result})
            except Exception as error:
                connection.send(
                    {
                        "ok": False,
                        "error_type": type(error).__name__,
                        "message": str(error),
                    }
                )
    except (EOFError, BrokenPipeError, OSError):
        pass
    finally:
        adapter.close()
        connection.close()
