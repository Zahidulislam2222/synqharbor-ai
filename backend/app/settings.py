"""The sole owner of environment-dependent backend configuration."""
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SH_", env_file=".env", extra="ignore")
    database_url: SecretStr
    migration_database_url: SecretStr | None = None
    session_secret: SecretStr
    public_origin: str
    secure_cookies: bool = True
    registration_enabled: bool = True
    cookie_name: str = "__Host-synqharbor"
    session_hours: int = 24
    invite_hours: int = 24
    database_pool_size: int = 5
    database_max_overflow: int = 5
    database_pool_timeout: int = 15
    sqlite_timeout: int = 10
    api_prefix: str = "/api/v1"
    api_title: str = "SynqHarbor API"
    release: str = "0.3.0"
    max_body_bytes: int = 65536
    list_limit: int = 100
    max_tasks: int = 1000
    max_messages: int = 1000
    rate_window_seconds: int = 600
    auth_rate_limit: int = 30
    contact_rate_limit: int = 5
    session_rate_limit: int = 900
    write_rate_limit: int = 120
    retention_days: int = 30
    allowed_hosts: list[str] = []
    inference_url: str | None = None
    inference_bridge: Path | None = None
    model_digests: dict[str, str] = {}
    builder_model: str | None = None
    code_builder_model: str | None = None
    reviewer_model: str | None = None
    inference_timeout: int = 180
    inference_max_bytes: int = 131072
    inference_tokens: int = 2048
    inference_context: int = 8192
    inference_threads: int = 2
    inference_temperature: float = 0
    inference_think: bool = False
    run_lease_seconds: int = 900
    worker_poll_seconds: float = 2
    max_run_attempts: int = 2
    max_builder_iterations: int = 2
    max_runs: int = 1000
    max_sources: int = 100
    max_active_runs: int = 10
    source_context_bytes: int = 8000
    data_directory: Path = Path(__file__).resolve().parents[1] / "data"
    frontend_directory: Path | None = None
    runner_binary: Path | None = None
    runner_rootfs: Path | None = None
    runner_directory: Path | None = None
    runner_timeout: int = 15
    runner_cleanup_timeout: int = 10
    runner_memory_bytes: int = 268435456
    runner_output_bytes: int = 8192
    runner_cpu_seconds: int = 3
    runner_process_limit: int = 32
    git_binary: str = "git"
    release_repository: Path | None = None
    repository_targets: dict[str, Path] = {}
    repository_context_bytes: int = 12000
    git_timeout: int = 120

    def builder_for(self, mode: str) -> str | None:
        return self.code_builder_model if mode == "code" and self.code_builder_model else self.builder_model

    @field_validator("session_secret")
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("Session secret must contain at least 32 characters")
        return value

    @model_validator(mode="after")
    def validate_deployment(self) -> Self:
        from urllib.parse import urlsplit

        origin = urlsplit(self.public_origin)
        if (origin.scheme not in {"http", "https"} or not origin.hostname or origin.path
                or origin.username or origin.password or origin.query or origin.fragment):
            raise ValueError("Public origin must be an HTTP(S) origin without a path")
        if self.secure_cookies and origin.scheme != "https":
            raise ValueError("Secure deployment requires HTTPS")
        if self.cookie_name.startswith("__Host-") and not self.secure_cookies:
            raise ValueError("Host-prefixed cookies require Secure")
        if not self.allowed_hosts:
            self.allowed_hosts = [origin.hostname]
        if self.inference_url:
            import ipaddress

            endpoint = urlsplit(self.inference_url)
            try:
                local = ipaddress.ip_address(endpoint.hostname or "").is_loopback
            except ValueError:
                local = endpoint.hostname == "localhost"
            if (not local or endpoint.scheme != "http" or endpoint.username
                    or endpoint.password or endpoint.query or endpoint.fragment):
                raise ValueError("Only explicit loopback Ollama endpoints are supported")
        if self.run_lease_seconds <= 2 * self.inference_timeout + self.runner_timeout + 3 * self.runner_cleanup_timeout:
            raise ValueError("Run lease must exceed the bounded builder/reviewer execution")
        for name in ["session_hours", "invite_hours", "list_limit", "max_tasks", "max_messages",
                     "max_body_bytes", "database_pool_size", "database_pool_timeout", "runner_cleanup_timeout",
                     "rate_window_seconds", "auth_rate_limit", "contact_rate_limit",
                     "session_rate_limit", "write_rate_limit", "retention_days", "sqlite_timeout", "inference_timeout",
                     "inference_max_bytes", "inference_tokens", "inference_context", "inference_threads", "run_lease_seconds",
                     "max_run_attempts", "max_builder_iterations", "max_runs", "max_sources", "max_active_runs", "source_context_bytes", "runner_timeout", "runner_memory_bytes",
                     "runner_output_bytes", "runner_cpu_seconds", "runner_process_limit", "repository_context_bytes", "git_timeout"]:
            if int(getattr(self, name)) <= 0:
                raise ValueError("Limits must be positive")
        if self.worker_poll_seconds <= 0 or self.database_max_overflow < 0:
            raise ValueError("Invalid worker/pool configuration")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
