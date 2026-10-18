"""Regressions for configuration ownership, bounded execution and paid-route denial."""
import ast
import math
import re
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr

from app.agent_contracts import Draft
from app.process import execute
from app.provider import OllamaProvider
from app.provider_errors import AgentFailure
from app.settings import Settings


def test_every_backend_setting_is_documented() -> None:
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "backend/app/settings.py").read_text())
    names = {node.target.id for node in ast.walk(tree) if isinstance(node, ast.AnnAssign)
             and isinstance(node.target, ast.Name)}
    example = (root / ".env.example").read_text()
    for name in names:
        assert "SH_" + name.upper() + "=" in example, name


def test_default_session_budget_supports_identity_checked_ui_polling() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "src/config/control.ts").read_text()
    milliseconds = re.search(r"pollMilliseconds:\s*(\d+)", source)
    assert milliseconds is not None
    settings = Settings(_env_file=None, database_url=SecretStr("sqlite://"),
                        session_secret=SecretStr("test-key" * 8), public_origin="https://example.com")
    # A full refresh checks identity before, between, and after private batches.
    polling_budget = math.ceil(settings.rate_window_seconds * 1000 / int(milliseconds[1])) * 3
    assert settings.session_rate_limit > polling_budget


def test_no_secrets_or_provider_defaults_in_feature_modules() -> None:
    root = Path(__file__).resolve().parents[1] / "app"
    secret = re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|(?:sk-|Bearer )[A-Za-z0-9_-]{20,}")
    for path in root.glob("*.py"):
        source = path.read_text()
        assert not secret.search(source), path.name
        if path.name != "settings.py":
            assert not re.search(r"https?://|(?:qwen|gemma|gpt|claude)[\w.:-]*\d", source), path.name


def test_cloud_models_cannot_be_invoked_even_on_a_loopback_server() -> None:
    settings = Settings(_env_file=None, database_url=SecretStr("sqlite://"),
                        session_secret=SecretStr("test-key" * 8), public_origin="https://example.com",
                        inference_url="http://127.0.0.1:1", model_digests={"test-cloud": "test-digest"})
    with pytest.raises(AgentFailure, match="local_model_not_qualified"):
        OllamaProvider(settings).generate("test-cloud", "test prompt", {}, Draft)


def test_process_stdin_and_output_are_bounded() -> None:
    # A child which never reads stdin must still reach the configured deadline.
    with pytest.raises(AgentFailure, match="process_timeout"):
        execute([sys.executable, "-I", "-c", "import time; time.sleep(10)"], b"x" * 100000, 1, 100)
    with pytest.raises(AgentFailure, match="process_output_limit"):
        execute([sys.executable, "-I", "-c", "print('x' * 10000)"], b"", 5, 100)


def test_configured_cpu_thread_budget_reaches_local_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    import json

    import httpx
    actual_client = httpx.Client
    seen = []
    def response(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith('/tags'):
            return httpx.Response(200, json={'models': [{'name': 'test-model', 'digest': 'test-digest'}]})
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={'done': True, 'done_reason': 'stop', 'message': {'content': Draft(content='Accepted output', summary='Checked').model_dump_json()}})
    def client(**kwargs: object) -> httpx.Client:
        return actual_client(transport=httpx.MockTransport(response), **kwargs)
    monkeypatch.setattr('app.provider.httpx.Client', client)
    config = Settings(_env_file=None, database_url=SecretStr('sqlite://'),
                      session_secret=SecretStr('test-key'*8), public_origin='https://example.com',
                      inference_url='http://127.0.0.1:1', inference_threads=3,
                      model_digests={'test-model': 'test-digest'})
    OllamaProvider(config).generate('test-model', 'Test instructions', {}, Draft)
    assert seen[0]['options']['num_thread'] == 3
