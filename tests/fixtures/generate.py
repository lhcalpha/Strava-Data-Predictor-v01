"""Regenerate the synthetic CSV fixtures: python tests/fixtures/generate.py

Every value is made up. Reference date for all files: 2026-11-05.
"""

from pathlib import Path

from tests.fixtures.builders import make_csv, run, typical_runs

HERE = Path(__file__).parent


def easy_runs(count: int, start: int = 1) -> list:
    return [run(start + i * 3, 6.0, 36.0, avg=140) for i in range(count)]


def mixed_quality_runs() -> list:
    usable = [
        run(1, 10.0, 46.0, avg=170, name="Tempo"),
        run(5, 8.0, 37.0, avg=168, name="Threshold"),
        run(9, 6.0, 27.6, avg=171, name="Hills"),
        run(12, 8.0, 48.0, avg=140),
        run(15, 12.0, 75.0, avg=145),
        run(18, 6.0, 36.0),
        run(22, 6.0, 36.0),
        run(26, 7.0, 42.0),
        run(30, 6.0, 36.0),
        run(35, 14.0, 88.0),
        run(40, 6.0, 36.0),
        run(45, 6.0, 36.0),
    ]
    excluded = [
        run(3, 30.0, 60.0, avg=130, name="Commute", type="Ride"),
        run(8, 40.0, 90.0, name="Long ride", type="Ride"),
        run(90, 6.0, 36.0, avg=150),
        run(100, 6.0, 36.0),
        run(120, 6.0, 36.0),
        run(20, None, 30.0, name="Treadmill no distance"),
        run(25, 5.0, 0.0, name="Zero time"),
        run(28, 10.0, 15.0, name="GPS glitch"),
    ]
    return usable + excluded


FIXTURES = {
    "typical_runner.csv": lambda: make_csv(typical_runs()),
    "strava_header.csv": lambda: make_csv(
        [
            run(2, 10.0, 46.0, avg=170, name="Tempo"),
            run(5, 5.0, 30.0, avg=150),
            run(9, 8.0, 37.0, avg=168, name="Threshold"),
            run(12, 12.0, 72.0, avg=146),
            run(16, 6.0, 27.6, avg=171, name="Track Intervals"),
        ]
    ),
    "no_hard_runs.csv": lambda: make_csv(easy_runs(12)),
    "interval_only.csv": lambda: make_csv(
        easy_runs(8)
        + [
            run(2, 6.0, 28.0, avg=172, name="6x800 Intervals"),
            run(9, 7.0, 33.0, avg=170, name="Hill Repeats"),
        ]
    ),
    "missing_columns.csv": lambda: make_csv(typical_runs(), drop_columns=("Moving Time",)),
    "empty.csv": lambda: "",
    "malformed.csv": lambda: make_csv([]) + "garbage,row\n",
    "too_few_runs.csv": lambda: make_csv(easy_runs(2)),
    "stale.csv": lambda: make_csv(easy_runs(8, start=20) + [run(21, 8.0, 37.0, avg=168)]),
    "imperial.csv": lambda: make_csv(typical_runs(), units="miles"),
    "xss.csv": lambda: make_csv(
        typical_runs() + [run(2, 5.0, 21.0, avg=175, name="<script>alert(1)</script>")]
    ),
    "mixed_quality.csv": lambda: make_csv(mixed_quality_runs()),
}


def main() -> None:
    for name, build in FIXTURES.items():
        (HERE / name).write_text(build(), encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
