"""Canonical import identity with fixed fixtures in fresh Python interpreters."""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.agent_contracts import RepositoryProfile


def invoke(tmp_path: Path, files: dict[str, str], entrypoint: str, value: Any) -> Any:
    for name, source in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
    harness = Path(__file__).resolve().parents[1] / "runner/harness.py"
    # Only these maintained fixture strings execute here. Model-generated code
    # always uses CodeRunner/gVisor. Keep module-cache changes out of pytest.
    launcher = ("import json,runpy,sys; protocol=json; "
                "harness=runpy.run_path(sys.argv[1]); "
                "result=harness['invoke_project'](sys.argv[2],sys.argv[3],protocol.loads(sys.stdin.read())); "
                "sys.stdout.write(protocol.dumps(result))")
    result = subprocess.run([sys.executable, "-I", "-B", "-c", launcher, str(harness), str(tmp_path), entrypoint],
                            input=json.dumps(value), text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def test_absolute_and_relative_imports_share_state(tmp_path: Path) -> None:
    files = {"store/main.py": "from store.state import STATE\nfrom .helper import read\ndef solve(value):\n    STATE['value'] = value\n    return read()\n",
             "store/state.py": "STATE = {}\n",
             "store/helper.py": "from .state import STATE\ndef read():\n    return STATE.get('value')\n"}
    assert invoke(tmp_path, files, "store.main:solve", 7) == 7


@pytest.mark.parametrize("entrypoint,files", [
    ("json:loads", {"json.py": "def loads(value):\n    return None\n"}),
    ("solution:solve", {"solution.py": "from json import loads\ndef solve(value):\n    return loads(value)\n",
                        "json.py": "def loads(value):\n    return None\n"})])
def test_cached_entrypoint_and_dependency_execute_approved_source(tmp_path: Path, entrypoint: str,
                                                                 files: dict[str, str]) -> None:
    assert invoke(tmp_path, files, entrypoint, '{"safe":1}') is None


def test_project_namespace_package_precedes_stdlib_package(tmp_path: Path) -> None:
    assert invoke(tmp_path, {"email/custom.py": "def solve(value):\n    return value + 1\n"}, "email.custom:solve", 2) == 3


@pytest.mark.parametrize("root", ["sys", "os", "_io", "importlib", "encodings"])
def test_runtime_infrastructure_names_are_rejected_before_dispatch(root: str) -> None:
    with pytest.raises(ValueError, match="reserved"):
        RepositoryProfile(name="Invalid", specification="Reserved module", files=[root + ".py"],
                          entrypoint=root + ":solve", cases=[{"input": 1, "expected": 1}])
