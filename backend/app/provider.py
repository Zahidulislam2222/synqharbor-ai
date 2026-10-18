"""Bounded Ollama structured-chat adapter. No paid routes or tool execution."""
import json
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ValidationError

from .provider_errors import AgentFailure
from .settings import Settings

# Ollama wire syntax is fixed here, independently of deployment configuration.
CHAT_PATH = "/api/chat"
TAGS_PATH = "/api/tags"


class Provider(Protocol):
    def generate(self, model: str, system: str, data: dict[str, Any],
                 schema: type[BaseModel]) -> str: ...


class OllamaProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, model: str, system: str, data: dict[str, Any],
                 schema: type[BaseModel]) -> str:
        config = self.settings
        expected_digest = config.model_digests.get(model)
        if not expected_digest or "cloud" in model.lower():
            raise AgentFailure("local_model_not_qualified")
        if not config.inference_url:
            raise AgentFailure("inference_not_configured")
        payload = {"model": model, "stream": False, "think": config.inference_think,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": json.dumps(data)}],
                   "format": schema.model_json_schema(),
                   "options": {"temperature": config.inference_temperature,
                               "num_predict": config.inference_tokens,
                               "num_ctx": config.inference_context,
                               "num_thread": config.inference_threads}}
        if config.inference_bridge:
            catalog = self.bridge("GET", TAGS_PATH)
            installed = catalog.get("models", [])
            if not any(m.get("name") == model and m.get("digest") == expected_digest
                       and not m.get("remote_host") and not m.get("remote_model") for m in installed):
                raise AgentFailure("local_model_not_qualified")
            result = self.bridge("POST", CHAT_PATH, payload)
            return self.validated_content(result, schema)
        try:
            with httpx.Client(timeout=config.inference_timeout, trust_env=False,
                              follow_redirects=False) as client:
                inventory = client.get(config.inference_url.rstrip("/") + TAGS_PATH)
                if inventory.status_code != 200:
                    raise AgentFailure("inference_unavailable")
                installed = inventory.json().get("models", [])
                if not any(m.get("name") == model and m.get("digest") == expected_digest
                           and not m.get("remote_host") and not m.get("remote_model") for m in installed):
                    raise AgentFailure("local_model_not_qualified")
                with client.stream("POST", config.inference_url.rstrip("/") + CHAT_PATH,
                                   json=payload) as response:
                    if response.status_code != 200:
                        raise AgentFailure("inference_unavailable")
                    raw = bytearray()
                    for block in response.iter_bytes():
                        raw.extend(block)
                        if len(raw) > config.inference_max_bytes:
                            raise AgentFailure("inference_output_limit")
            result = json.loads(raw)
            return self.validated_content(result, schema)
        except (httpx.HTTPError, TimeoutError) as exc:
            raise AgentFailure("inference_unavailable") from exc
        except (ValueError, KeyError, TypeError, ValidationError) as exc:
            raise AgentFailure("invalid_model_output") from exc

    @staticmethod
    def validated_content(result: dict[str, Any], schema: type[BaseModel]) -> str:
        try:
            if result.get("done") is not True or result.get("done_reason") == "length":
                raise AgentFailure("inference_incomplete")
            content = result["message"]["content"]
            schema.model_validate_json(content)
            return str(content)
        except (ValueError, KeyError, TypeError) as exc:
            raise AgentFailure("invalid_model_output") from exc

    def bridge(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Optional curl stdio bridge to a loopback service in a different OS namespace."""
        import os

        from .process import execute

        config = self.settings
        assert config.inference_bridge is not None and config.inference_url is not None
        # stdin keeps task content out of command arguments and shell history.
        environment = {k: v for k, v in os.environ.items() if k in {"PATH", "SystemRoot", "WINDIR", "WSL_INTEROP", "WSL_DISTRO_NAME"}}
        try:
            command = [str(config.inference_bridge), "--silent", "--show-error", "--fail",
                       "--noproxy", "*", "--max-time", str(config.inference_timeout),
                       "--request", method, config.inference_url.rstrip("/") + path]
            if payload is not None:
                command.extend(["--header", "Content-Type: application/json", "--data-binary", "@-"])
            output = execute(command, json.dumps(payload).encode() if payload else b"",
                             config.inference_timeout, config.inference_max_bytes, environment)
            result = json.loads(output)
            if not isinstance(result, dict):
                raise AgentFailure("invalid_model_output")
            return result
        except (ValueError, UnicodeError) as exc:
            raise AgentFailure("invalid_model_output") from exc
