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
    environment.setdefault("OMP_NUM_THREADS", "1")
    environment.setdefault("OPENBLAS_NUM_THREADS", "1")
    environment.setdefault("MKL_NUM_THREADS", "1")

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
        restart_at = 0.0
        failures = 0
        while not stopping:
            # An ML crash must not take down sign-in, tracking and officer work.
            api_code = processes[1].poll()
            if api_code is not None:
                print(f"API exited with code {api_code}", flush=True)
                return api_code or 1
            if processes[0].poll() is not None:
                if not restart_at:
                    failures += 1
                    restart_at = time.monotonic() + min(60, 5 * failures)
                    print(f"ML service exited with code {processes[0].returncode}; restarting while API stays available", flush=True)
                if time.monotonic() >= restart_at:
                    processes[0] = subprocess.Popen(
                        [sys.executable, "-m", "uvicorn", "ml.service:app", "--host", "127.0.0.1", "--port", "8001"],
                        env=environment,
                    )
                    restart_at = 0.0
            time.sleep(0.25)
    finally:
        terminate(processes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
