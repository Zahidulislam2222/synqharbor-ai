# SynqHarbor backend

FastAPI provides the same-origin `/api/v1` contract. PostgreSQL owns authenticated
collaboration, durable runs, scoped sources, artifact versions, approvals and
release receipts. A separately supervised worker uses installed local Ollama
models and rootless gVisor for bounded Python execution. Two distinct authorized
accounts approve exact content before operator-granted Git delivery.

Python 3.12 is required. Install `requirements.txt` in a virtual environment and
use the safe settings in the root `.env.example`; real values stay private.
Migration and runtime database identities are separate. Production self-enrollment
is operator-controlled; `python -m app.manage create-user --email USER_EMAIL
--name USER_NAME` prompts privately for a password.

```sh
python -m app.database
uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
# Separate process:
python -m app.worker
```

For verification install `requirements-dev.txt` and run `pytest -q`, `ruff check .`
and `mypy app --strict`. PostgreSQL parity uses the dedicated test database
configuration accepted by `tests/conftest.py`. Never point destructive parity
tests at application data.

Read [core workflows](../docs/core-engine.md), [API](../docs/api.md),
[configuration](../docs/configuration.md), [security](../docs/security.md),
[self-hosting](../docs/self-hosting.md) and [deployment templates](../infra/backend/README.md).

For PostgreSQL parity, keep the configuration private and specify the test root:

```sh
pytest -c pyproject.toml -q tests --database-test-config /path/to/private-postgres.json
```

Pinning the config and test directory prevents an external temporary configuration
path from changing pytest discovery. The config provides separate migration and
restricted runtime URLs; use a dedicated disposable qualification database.
