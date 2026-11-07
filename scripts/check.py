"""Run every quality gate in order and stop at the first failure.

Usage (from the project root): .venv\Scripts\python scripts\check.py
"""

import subprocess
import sys

GATES = [
    ["-m", "ruff", "check", "."],
    ["-m", "ruff", "format", "--check", "."],
    [
        "-m",
        "pytest",
        "--cov=strava_predictor",
        "--cov-branch",
        "--cov-fail-under=90",
    ],
    [
        "-m",
        "pytest",
        "tests/unit",
        "--cov=strava_predictor.domain",
        "--cov-branch",
        "--cov-fail-under=95",
    ],
]


def main() -> int:
    for gate in GATES:
        command = [sys.executable, *gate]
        print("$", " ".join(gate[1:]), flush=True)
        result = subprocess.run(command, check=False)
        if result.returncode != 0:
            print(f"FAILED: {' '.join(gate[1:])}", flush=True)
            return result.returncode
    print("All quality gates passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
