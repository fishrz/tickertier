"""One-command daily pipeline runner with fail-fast timing output."""
from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Sequence
from datetime import datetime


def _stamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_step(name: str, command: Sequence[str]) -> None:
    start = time.monotonic()
    print(f"[{_stamp()}] START {name}", flush=True)
    subprocess.run(command, check=True)
    elapsed = time.monotonic() - start
    print(f"[{_stamp()}] DONE  {name} ({elapsed:.1f}s)", flush=True)


def main() -> None:
    python = sys.executable
    steps = [
        ("fetch_prices --incremental", [python, "-m", "data.pipelines.fetch_prices", "--incremental"]),
        ("compute_metrics", [
            python,
            "-c",
            "from data.db import get_conn, init_schema; "
            "from data.pipelines.compute_metrics import compute_metrics; "
            "con=get_conn(); init_schema(con); "
            "print(f'wrote {compute_metrics(con)} metrics'); con.close()",
        ]),
        ("fetch_earnings", [python, "-m", "data.pipelines.fetch_earnings", "--skip-missing-key"]),
        ("compute_awards --daily", [python, "-m", "data.pipelines.compute_awards", "--daily"]),
        ("personas", [python, "-m", "data.personas"]),
    ]
    for name, command in steps:
        run_step(name, command)


if __name__ == "__main__":
    main()
