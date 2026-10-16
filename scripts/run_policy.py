"""Run a user-supplied policy adapter against a resumable evaluation queue."""

import argparse
import importlib
import json
import os
from pathlib import Path
import socket

from libero_remote import RemoteRunClient
from libero_remote.benchmark import export_benchmark_results
from libero_remote.runner import run_scheduled_run


def load_adapter(factory_name, kwargs):
    module_name, separator, attribute = factory_name.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError("--adapter-factory must be module:function")
    factory = getattr(importlib.import_module(module_name), attribute)
    adapter = factory(**kwargs)
    for name in ("reset", "act", "close"):
        if not callable(getattr(adapter, name, None)):
            raise TypeError("Adapter must implement reset(context), act(observation), close()")
    return adapter


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.environ.get("LIBERO_REMOTE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--runner-id", default="{}-{}".format(socket.gethostname(), os.getpid()))
    parser.add_argument("--adapter-factory", required=True)
    parser.add_argument("--adapter-kwargs", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    kwargs = {}
    if args.adapter_kwargs:
        kwargs = json.loads(args.adapter_kwargs.read_text(encoding="utf-8"))
        if not isinstance(kwargs, dict):
            raise ValueError("Adapter kwargs file must contain a JSON object")
    adapter = load_adapter(args.adapter_factory, kwargs)
    with RemoteRunClient(args.base_url, api_key=os.environ.get("LIBERO_REMOTE_API_KEY")) as client:
        snapshot = run_scheduled_run(client, args.run_id, args.runner_id, adapter)
        export_benchmark_results(client, args.run_id, args.output_dir)
    print(json.dumps({"run_id": args.run_id, "status": snapshot["status"], "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
