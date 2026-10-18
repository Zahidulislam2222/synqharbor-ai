"""Bounded, shell-free subprocess I/O for trusted runtime executables only."""
import os
import selectors
import signal
import subprocess
import time
from collections.abc import Mapping, Sequence

from .provider_errors import AgentFailure


def execute(command: Sequence[str], data: bytes, timeout: int, output_limit: int,
            environment: Mapping[str, str] | None = None) -> bytes:
    # Executable/flags are operator configuration or fixed protocol syntax, never model output.
    with subprocess.Popen(list(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, env=environment,
                          start_new_session=True) as child:
        assert child.stdin is not None and child.stdout is not None
        output = bytearray()
        deadline = time.monotonic() + timeout
        try:
            # Input is bounded before this function; nonblocking writes avoid a child
            # which never reads stdin turning a bounded job into an indefinite wait.
            os.set_blocking(child.stdin.fileno(), False)
            os.set_blocking(child.stdout.fileno(), False)
            offset = 0
            with selectors.DefaultSelector() as selector:
                selector.register(child.stdout, selectors.EVENT_READ)
                selector.register(child.stdin, selectors.EVENT_WRITE)
                while selector.get_map():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise AgentFailure("process_timeout")
                    ready = selector.select(remaining)
                    for key, _ in ready:
                        if key.fileobj is child.stdin:
                            try:
                                offset += os.write(child.stdin.fileno(), data[offset:])
                            except BrokenPipeError:
                                offset = len(data)
                            if offset == len(data):
                                selector.unregister(child.stdin)
                                child.stdin.close()
                        else:
                            block = os.read(child.stdout.fileno(), output_limit + 1)
                            if not block:
                                selector.unregister(child.stdout)
                            else:
                                output.extend(block)
                                if len(output) > output_limit:
                                    raise AgentFailure("process_output_limit")
            child.wait(timeout=max(0.001, deadline - time.monotonic()))
            if child.returncode:
                raise AgentFailure("process_failed")
            return bytes(output)
        except subprocess.TimeoutExpired as exc:
            raise AgentFailure("process_timeout") from exc
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
