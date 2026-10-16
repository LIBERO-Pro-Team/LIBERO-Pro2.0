# Verification

Use Python 3.11 or 3.12 for the service/client test suite:

```bash
python -m pip install -e ".[server,dev]"
python -m pytest -q tests
python -m mypy libero_remote --python-version 3.12
```

Coverage includes manifest/BDDL checksums, train/test boundaries, task selection, protocol/transport, account isolation, session cleanup, scheduling, resume, result export, model adapters and video output. Tests use temporary data and do not require author-local experiment files.

Simulator tests require the compatible LIBERO, MuJoCo and robosuite dependencies:

```bash
python -m pytest -q simulator-source/tests
```

The runtime BDDL fixtures in `simulator-source/tests/fixtures/runtime_bddls/` are isolated test inputs and are not part of the published task catalogue. Windows deployment tests can require WSL. Run the environment smoke test on the target Linux/NVIDIA EGL host before policy evaluation; unit tests do not validate a GPU rollout.
