"""Build an unprivileged minimal Python rootfs from the installed interpreter.

No host home, mount points, configuration, tests or credentials are included.
Run with the system Python. Destination is an explicit operator argument.
"""
import argparse
import shutil
from pathlib import Path


def prepare(destination: Path) -> None:
    if destination.exists():
        raise ValueError("Choose a new empty rootfs destination")
    destination.mkdir(parents=True)
    # Ubuntu 24.04 Python runtime and its dynamic linker closure. This preparation
    # tool is platform-specific; feature/business code never owns these paths.
    paths = ["/usr/bin/python3.12", "/usr/lib/python3.12", "/bin/sleep",
             "/lib/x86_64-linux-gnu/libm.so.6", "/lib/x86_64-linux-gnu/libc.so.6",
             "/lib/x86_64-linux-gnu/libz.so.1", "/lib/x86_64-linux-gnu/libexpat.so.1",
             "/lib64/ld-linux-x86-64.so.2"]
    for source_name in paths:
        source = Path(source_name)
        target = destination / source_name.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns(
                "site-packages", "dist-packages", "__pycache__", "test", "tests", "ensurepip"))
        else:
            shutil.copyfile(source, target)
            shutil.copymode(source, target)
    (destination / "usr/bin/python3").symlink_to("python3.12")
    for name in ("proc", "dev", "scratch", "app"):
        (destination / name).mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("harness.py"), destination / "app/harness.py")
    (destination / "app/solution.py").touch()
    (destination / "app/project").mkdir()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    prepare(parser.parse_args().destination)
