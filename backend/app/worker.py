"""Separate worker entry point; safe to restart, no execution in the web process."""
import argparse
import signal
import threading

from .brain import Worker
from .database import make_engine
from .provider import OllamaProvider
from .settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    args = parser.parse_args()
    settings = get_settings()
    engine = make_engine(settings)
    worker = Worker(engine, settings, OllamaProvider(settings))
    stop = threading.Event()

    def terminate(signum: int, frame: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        while not stop.is_set():
            worked = worker.once()
            if args.once:
                break
            if not worked:
                stop.wait(settings.worker_poll_seconds)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
