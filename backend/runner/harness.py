"""Runs inside an empty gVisor rootfs; no expected answers or host credentials."""
import json
import resource
import sys
from collections.abc import Iterable
from importlib import import_module
from importlib.machinery import FrozenImporter, ModuleSpec, PathFinder
from pathlib import Path
from typing import Any


def project_roots(files: Iterable[str]) -> set[str]:
    """One protocol definition for roots that cannot replace Python's loader."""
    roots = {name.split("/", 1)[0].removesuffix(".py") for name in files}
    for name in roots:
        if (name in {"encodings", "importlib"} or name in sys.builtin_module_names
                or FrozenImporter.find_spec(name) is not None):
            raise ValueError("Python runtime module names are reserved")
    return roots


class ProjectFinder:
    def __init__(self, root: Path, roots: set[str]) -> None:
        self.root, self.roots = root, roots

    def find_spec(self, fullname: str, path: object = None, target: object = None) -> ModuleSpec | None:
        if fullname.split(".", 1)[0] not in self.roots:
            return None
        # Restrict this root to approved project files, including namespace
        # packages that would otherwise lose to a stdlib regular package.
        parent = self.root.joinpath(*fullname.split(".")[:-1])
        spec = PathFinder.find_spec(fullname, [str(parent)])
        if spec is None:
            raise ModuleNotFoundError(fullname)
        return spec


def invoke_project(directory: str, entrypoint: str, value: Any) -> Any:
    root = Path(directory).resolve()
    roots = project_roots(str(path.relative_to(root)) for path in root.rglob("*.py"))
    module_name, function = entrypoint.split(":")
    if module_name.split(".", 1)[0] not in roots:
        raise ValueError("Entrypoint is outside the project")
    sys.path.insert(0, str(root))
    sys.meta_path.insert(0, ProjectFinder(root, roots))
    # Each case has a fresh process. Evict overlapping cache entries for the
    # entire project graph; absolute and relative imports retain canonical names.
    # The harness keeps its own serializer callable, never reimports it here.
    for name in tuple(sys.modules):
        if name.split(".", 1)[0] in roots:
            del sys.modules[name]
    module = import_module(module_name)
    return getattr(module, function)(value)


def main() -> None:
    inputs = json.load(sys.stdin)
    for limit, value in [(resource.RLIMIT_AS, inputs["memory"]),
                         (resource.RLIMIT_CPU, inputs["cpu"]),
                         (resource.RLIMIT_NPROC, inputs["processes"]),
                         (resource.RLIMIT_FSIZE, inputs["output"])]:
        resource.setrlimit(limit, (value, value))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    encode, write = json.dumps, sys.stdout.write
    result = invoke_project("/app/project", inputs["entrypoint"], inputs["value"])
    write(encode(result))


if __name__ == "__main__":
    main()
