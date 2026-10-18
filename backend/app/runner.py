"""gVisor-only bounded Python fixture runner; no host shell or protected tests exposed."""
import json
import re
import shutil
import tempfile
from pathlib import Path

from .agent_contracts import Fixture, RepositoryProfile
from .process import execute
from .provider_errors import AgentFailure
from .settings import Settings

CLEANUP_REQUIRED = "cleanup-required"

class CodeRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def cleanup(self, state: Path) -> None:
        """SIGKILL of the bwrap launcher does not destroy its OCI sandbox."""
        config = self.settings
        command = [str(config.runner_binary), "--rootless", "--root=" + str(state)]

        def containers() -> list[str]:
            raw = execute([*command, "list", "--format=json"], b"", config.runner_cleanup_timeout,
                          config.runner_output_bytes, {"PATH": "/usr/bin:/bin"})
            records = json.loads(raw)
            # runsc encodes its empty Go slice as JSON null.
            if records is None:
                return []
            if not isinstance(records, list) or len(records) > 1:
                raise ValueError("Unexpected job-scoped OCI inventory")
            identifiers = [record["id"] for record in records]
            if any(not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", identifier)
                   for identifier in identifiers):
                raise ValueError("Invalid OCI container identity")
            return identifiers

        try:
            for identifier in containers():
                execute([*command, "delete", "--force", identifier], b"", config.runner_cleanup_timeout,
                        config.runner_output_bytes, {"PATH": "/usr/bin:/bin"})
            if containers():
                raise ValueError("OCI sandbox remains after deletion")
        except (AgentFailure, OSError, ValueError, KeyError, TypeError) as exc:
            raise AgentFailure("runner_cleanup_failed") from exc

    def invoke(self, source: str | dict[str, str], value: object,
               entrypoint: str = "solution:solve") -> object:
        config = self.settings
        if not config.runner_binary or not config.runner_rootfs or not config.runner_directory:
            raise AgentFailure("runner_not_configured")
        if not (config.runner_rootfs / "app" / "harness.py").is_file():
            raise AgentFailure("runner_not_qualified")
        config.runner_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        if next(config.runner_directory.glob("job-*/" + CLEANUP_REQUIRED), None) is not None:
            raise AgentFailure("runner_cleanup_required")
        job = Path(tempfile.mkdtemp(prefix="job-", dir=config.runner_directory))
        started = False
        state = job / "state"
        try:
            project = job / "project"
            project.mkdir()
            files = {"solution.py": source} if isinstance(source, str) else source
            for name, content in files.items():
                # Defense in depth: validated profiles are the caller, but never
                # allow a direct adapter caller to write outside the scratch tree.
                path = project / name
                if not path.resolve().is_relative_to(project.resolve()) or path.is_absolute() and name.startswith("/"):
                    raise AgentFailure("invalid_runner_path")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            state.mkdir()
            command = [str(config.runner_binary), "--rootless", "--network=none", "--platform=systrap",
                       "--root=" + str(state), "bwrap", "--unshare-all", "--clearenv", "--cap-drop", "ALL",
                       "--die-with-parent", "--ro-bind", str(config.runner_rootfs), "/",
                       "--ro-bind", str(project), "/app/project", "--proc", "/proc",
                       "--tmpfs", "/scratch", "--chdir", "/app", "--", "/usr/bin/python3", "-I",
                       "/app/harness.py"]
            inputs = {"value": value, "entrypoint": entrypoint, "memory": config.runner_memory_bytes,
                      "cpu": config.runner_cpu_seconds, "processes": config.runner_process_limit,
                      "output": config.runner_output_bytes}
            started = True
            result = execute(command, json.dumps(inputs).encode(), config.runner_timeout,
                             config.runner_output_bytes, {"PATH": "/usr/bin:/bin"})
            try:
                return json.loads(result)
            except (ValueError, UnicodeError) as exc:
                raise AgentFailure("invalid_runner_output") from exc
        finally:
            if started:
                # A cleanup failure preserves the private job state for operator
                # recovery; do not erase the only handle to a surviving sandbox.
                try:
                    self.cleanup(state)
                except AgentFailure:
                    (job / CLEANUP_REQUIRED).touch(mode=0o600)
                    raise
            shutil.rmtree(job)

    def test(self, source: str, fixture: Fixture) -> dict[str, int | str]:
        return self.test_files({"solution.py": source}, fixture, "solution:solve")

    def test_files(self, files: dict[str, str], fixture: Fixture | RepositoryProfile,
                   entrypoint: str) -> dict[str, int | str]:
        passed = 0
        for case in fixture.cases:
            # Expectations never enter the sandbox or model context. A fresh process
            # is used for every case; candidate code cannot alter the host's verdict.
            actual = self.invoke(files, case.input, entrypoint)
            if json.dumps(actual, sort_keys=True) != json.dumps(case.expected, sort_keys=True):
                raise AgentFailure("protected_tests_failed")
            passed += 1
        return {"passed": passed, "total": len(fixture.cases), "runtime": "gvisor"}
