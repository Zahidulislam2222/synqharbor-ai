"""Typed renderer for portable, centrally owned service deployment settings."""

import ipaddress
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from string import Template
from typing import Any


@dataclass(frozen=True)
class Deployment:
    root: str
    release: str
    api_port: int
    database_port: int
    inference_port: int
    postgres_image: str
    ollama_image: str
    api_user: str
    worker_user: str
    network_subnet: str
    limits: dict[str, dict[str, str]]
    containers: dict[str, dict[str, str | int | float]]
    proxy_binary: str
    models: dict[str, str]
    git_author_name: str
    git_author_email: str
    readiness_timeout: float
    readiness_poll: float

    def __post_init__(self) -> None:
        if (
            not self.root.startswith("/srv/apps/synqharbor")
            or ".." in PurePosixPath(self.root).parts
            or not re.fullmatch(r"[a-zA-Z0-9_./-]+", self.root)
            or not re.fullmatch(r"[a-z0-9-]+", self.release)
        ):
            raise ValueError("Invalid project deployment path/identity")
        ports = [self.api_port, self.database_port, self.inference_port]
        if not 0 < self.readiness_poll < self.readiness_timeout <= 120:
            raise ValueError("A bounded readiness interval is required")
        if len(set(ports)) != 3 or not all(1024 < port < 65536 for port in ports):
            raise ValueError("Distinct private unprivileged ports required")
        for image in [self.postgres_image, self.ollama_image]:
            if not re.fullmatch(r"[a-z0-9/.-]+@sha256:[a-f0-9]{64}", image):
                raise ValueError("Images must be digest-pinned")
        for role in ["builder", "code_builder", "reviewer"]:
            if (
                not re.fullmatch(r"[a-zA-Z0-9._:/-]+", self.models[role])
                or "cloud" in self.models[role].lower()
            ):
                raise ValueError("An explicit local model binding is required")
        if "\n" in self.git_author_name or not re.fullmatch(
            r"[^\s@]+@[^\s@]+", self.git_author_email
        ):
            raise ValueError("Invalid Git author identity")
        for user in [self.api_user, self.worker_user]:
            if not re.fullmatch(r"synqharbor[a-z0-9-]+", user):
                raise ValueError("Project-scoped service identities required")
        network = ipaddress.ip_network(self.network_subnet)
        if not network.is_private or network.version != 4 or network.prefixlen != 28:
            raise ValueError("A bounded private IPv4 network is required")
        for role in ["api", "worker"]:
            limits = self.limits[role]
            if not re.fullmatch(r"[0-9]+[MG]", limits["memory"]):
                raise ValueError("Bounded memory required")
            if (
                not re.fullmatch(r"[0-9]+%", limits["cpu"])
                or not limits["tasks"].isdigit()
            ):
                raise ValueError("Bounded CPU/tasks required")
        for role in ["database", "inference"]:
            container_limits = self.containers[role]
            if not re.fullmatch(r"[0-9]+[mg]", str(container_limits["memory"])):
                raise ValueError("Bounded container memory required")
            if (
                not 0 < float(container_limits["cpus"]) <= 8
                or not 0 < int(container_limits["pids"]) <= 512
            ):
                raise ValueError("Bounded container CPU/tasks required")

    @property
    def backend(self) -> str:
        return self.root + "/backend"

    @property
    def state(self) -> str:
        return self.backend + "/state"

    def address(self, offset: int) -> str:
        return str(ipaddress.ip_network(self.network_subnet).network_address + offset)


def render(source: str, values: dict[str, Any]) -> str:
    """Missing template values fail rather than silently reaching production."""
    return Template(source).substitute(values)


def git_read_configuration(repository: str) -> str:
    """Exact operator-owned trust for one read-only API repository."""
    if (not repository.startswith("/") or ".." in PurePosixPath(repository).parts
            or not re.fullmatch(r"[a-zA-Z0-9_./-]+", repository)):
        raise ValueError("A canonical repository path is required")
    return "[safe]\n    directory = " + repository + "\n[core]\n    fsmonitor = false\n"
