"""Run the FastAPI model service and Express API in one production container."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time


def terminate(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 8
    for process in processes:
        if process.poll() is None:
            try:
                process.wait(max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                process.kill()


def main() -> int:
    environment = os.environ.copy()
    environment.setdefault("AI_SERVICE_URL", "http://127.0.0.1:8001")
    environment.setdefault("HOST", "0.0.0.0")
    environment.setdefault("NODE_ENV", "production")

    processes = [
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "ml.service:app", "--host", "127.0.0.1", "--port", "8001"],
            env=environment,
        ),
        subprocess.Popen(["node", "backend/server.js"], env=environment),
    ]

    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        if not stopping:
            stopping = True
            terminate(processes)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    try:
        while not stopping:
            for process in processes:
                code = process.poll()
                if code is not None:
                    terminate(processes)
                    return code or 1
            time.sleep(0.25)
    finally:
        terminate(processes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
