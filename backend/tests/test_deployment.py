"""Offline release rendering fails before any remote host operation is needed."""

import importlib.util
import json
import sys
from pathlib import Path
from string import Template

import pytest


def test_every_backend_template_is_present_and_fully_renderable() -> None:
    root = Path(__file__).resolve().parents[2]
    directory = root / "infra/backend"
    spec = importlib.util.spec_from_file_location(
        "synqharbor_deployment", directory / "deployment.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    cfg = module.Deployment(**json.loads((directory / "deployment.example.json").read_text()))
    values = dict(
        POSTGRES_IMAGE=cfg.postgres_image,
        OLLAMA_IMAGE=cfg.ollama_image,
        STATE_ROOT=cfg.state,
        ADMIN_PASSWORD_FILE=cfg.backend + "/private/database-admin",
        NETWORK_SUBNET=cfg.network_subnet,
        DATABASE_ADDRESS=cfg.address(2),
        INFERENCE_ADDRESS=cfg.address(3),
        ROLE="api",
        SERVICE_USER=cfg.api_user,
        BACKEND_ROOT=cfg.backend,
        RUNTIME_ENV=cfg.backend + "/private/runtime.env",
        EXEC_START=cfg.backend + "/venv/bin/python -m app.worker",
        WRITABLE_PATHS=cfg.state + "/jobs",
        MEMORY_MAX=cfg.limits["api"]["memory"],
        CPU_QUOTA=cfg.limits["api"]["cpu"],
        TASKS_MAX=cfg.limits["api"]["tasks"],
        RUNSC_BINARY=cfg.backend + "/runtime/bin/runsc",
        PORT=cfg.api_port,
        PROXY_BINARY=cfg.proxy_binary,
        DESTINATION=cfg.address(2) + ":5432",
        SUBNET=cfg.network_subnet,
        EXTRA_ENVIRONMENT="",
    )
    for role in ["database", "inference"]:
        for name, value in cfg.containers[role].items():
            values[role.upper() + "_" + name.upper()] = value
    for name in [
        "services.compose.yaml",
        "service.unit.template",
        "runsc.apparmor.template",
        "proxy.socket.template",
        "proxy.service.template",
    ]:
        rendered = Template((directory / name).read_text()).substitute(values)
        assert "${" not in rendered, name
        assert rendered.strip(), name


@pytest.mark.parametrize("failure", ["install", "reload", "start", "verify"])
def test_failed_activation_restores_source_and_units_after_install_and_reload(failure: str) -> None:
    directory = Path(__file__).resolve().parents[2] / "infra/backend"
    spec = importlib.util.spec_from_file_location(
        "synqharbor_activation", directory / "activation.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    state = {
        "source": "old",
        "units": "old",
        "loaded_units": "old",
        "running": True,
        "failed": False,
    }

    def stop() -> None:
        state["running"] = False

    def install() -> None:
        state.update(source="new", units="new")
        if failure == "install":
            state["failed"] = True
            raise ValueError("Injected failure after unit installation")

    def reload() -> None:
        state["loaded_units"] = state["units"]
        if failure == "reload" and not state["failed"]:
            state["failed"] = True
            raise ValueError("Injected failure after daemon reload")

    def start() -> None:
        state["running"] = True
        if failure == "start" and not state["failed"]:
            state["failed"] = True
            raise ValueError("Injected startup failure")

    def verify() -> None:
        if failure == "verify":
            state["failed"] = True
            raise ValueError("Injected readiness failure")

    def restore() -> None:
        assert state["running"] is False
        state.update(source="old", units="old")

    def verify_restored() -> None:
        assert state["source"] == state["units"] == state["loaded_units"] == "old"
        assert state["running"] is True

    operations = module.ReleaseOperations(
        stop, install, reload, start, verify, restore, verify_restored
    )
    try:
        module.activate_release(operations)
    except ValueError:
        pass
    else:
        raise AssertionError("The activation failure must remain visible")
    verify_restored()


def test_one_active_service_cannot_hide_failed_api_after_start() -> None:
    directory = Path(__file__).resolve().parents[2] / "infra/backend"
    spec = importlib.util.spec_from_file_location(
        "synqharbor_readiness", directory / "activation.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    state = {"source": "old", "units": "old", "running": False}
    observed: list[str] = []
    tick = [0.0]

    def pause(seconds: float) -> None:
        tick[0] += seconds

    def active(service: str) -> bool:
        observed.append(service)
        return bool(state["running"]) and (service == "worker" or state["source"] == "old")

    def verify() -> None:
        module.wait_for_readiness(
            ["api", "worker"], active, lambda: True, 3.0, 1.0, clock=lambda: tick[0], pause=pause
        )

    def install() -> None:
        state.update(source="new", units="new")

    def restore() -> None:
        state.update(source="old", units="old")

    def stop() -> None:
        state["running"] = False

    def start() -> None:
        state["running"] = True

    operations = module.ReleaseOperations(
        stop, install, lambda: None, start, verify, restore, verify
    )
    with pytest.raises(RuntimeError, match="stable HTTP/schema readiness"):
        module.activate_release(operations)
    assert state == {"source": "old", "units": "old", "running": True}
    assert {"api", "worker"}.issubset(observed)


def test_repository_trust_renderer_preserves_exact_setup_and_upgrade_contract() -> None:
    import configparser

    directory = Path(__file__).resolve().parents[2] / "infra/backend"
    spec = importlib.util.spec_from_file_location("synqharbor_git_config", directory / "deployment.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    repository = "/srv/apps/synqharbor-example/backend/state/repositories/verification"
    rendered = module.git_read_configuration(repository)
    assert rendered == "[safe]\n    directory = " + repository + "\n[core]\n    fsmonitor = false\n"
    parsed = configparser.ConfigParser()
    parsed.read_string(rendered)
    assert parsed["safe"]["directory"] == repository
    assert parsed["core"].getboolean("fsmonitor") is False
    for unsafe in [repository + "\n[safe]\ndirectory = *", repository + "/../other"]:
        with pytest.raises(ValueError):
            module.git_read_configuration(unsafe)
