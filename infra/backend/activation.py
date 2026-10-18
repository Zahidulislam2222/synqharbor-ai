"""A release switches source and service configuration as one recoverable operation."""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass


def wait_for_readiness(
    services: Sequence[str],
    active: Callable[[str], bool],
    healthy: Callable[[], bool],
    timeout: float,
    poll: float,
    clock: Callable[[], float] = time.monotonic,
    pause: Callable[[float], None] = time.sleep,
) -> None:
    """Require each service and HTTP/schema readiness on consecutive polls."""
    if not services or poll <= 0 or timeout <= poll:
        raise ValueError("A bounded readiness window is required")
    deadline = clock() + timeout
    confirmations = 0
    while True:
        states = [active(service) for service in services]
        confirmations = confirmations + 1 if all(states) and healthy() else 0
        if confirmations >= 2:
            return
        remaining = deadline - clock()
        if remaining <= 0:
            raise RuntimeError("Services did not reach stable HTTP/schema readiness")
        pause(min(poll, remaining))


@dataclass(frozen=True)
class ReleaseOperations:
    stop: Callable[[], None]
    install: Callable[[], None]
    reload: Callable[[], None]
    start: Callable[[], None]
    verify: Callable[[], None]
    restore: Callable[[], None]
    verify_restored: Callable[[], None]


def activate_release(operations: ReleaseOperations) -> None:
    try:
        operations.stop()
        operations.install()
        operations.reload()
        operations.start()
        operations.verify()
    except Exception:
        try:
            operations.stop()
            operations.restore()
            operations.reload()
            operations.start()
            operations.verify_restored()
        except Exception as recovery:
            raise RuntimeError(
                "Release activation failed and recovery is unverified"
            ) from recovery
        raise
