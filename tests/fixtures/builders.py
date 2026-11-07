"""Build synthetic Strava activity CSV text for tests.

STRAVA_HEADER copies the column names (only the names, no values) of a real Strava export, in
order, including the repeated names. All row values are made up.
"""

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta

REFERENCE_DATE = date(2026, 11, 5)

STRAVA_HEADER = [
    "Activity ID", "Activity Date", "Activity Name", "Activity Type", "Activity Description",
    "Elapsed Time", "Distance", "Max Heart Rate", "Relative Effort", "Commute",
    "Activity Private Note", "Activity Gear", "Filename", "Athlete Weight", "Bike Weight",
    "Elapsed Time", "Moving Time", "Distance", "Max Speed", "Average Speed", "Elevation Gain",
    "Elevation Loss", "Elevation Low", "Elevation High", "Max Grade", "Average Grade",
    "Average Positive Grade", "Average Negative Grade", "Max Cadence", "Average Cadence",
    "Max Heart Rate", "Average Heart Rate", "Max Watts", "Average Watts", "Calories",
    "Max Temperature", "Average Temperature", "Relative Effort", "Total Work", "Number of Runs",
    "Uphill Time", "Downhill Time", "Other Time", "Perceived Exertion", "Type", "Start Time",
    "Weighted Average Power", "Power Count", "Prefer Perceived Exertion",
    "Perceived Relative Effort", "Commute", "Total Weight Lifted", "From Upload",
    "Grade Adjusted Distance", "Weather Observation Time", "Weather Condition",
    "Weather Temperature", "Apparent Temperature", "Dewpoint", "Humidity", "Weather Pressure",
    "Wind Speed", "Wind Gust", "Wind Bearing", "Precipitation Intensity", "Sunrise Time",
    "Sunset Time", "Moon Phase", "Bike", "Gear", "Precipitation Probability",
    "Precipitation Type", "Cloud Cover", "Weather Visibility", "UV Index", "Weather Ozone",
    "Jump Count", "Total Grit", "Average Flow", "Flagged", "Average Elapsed Speed",
    "Dirt Distance", "Newly Explored Distance", "Newly Explored Dirt Distance", "Activity Count",
    "Total Steps", "Carbon Saved", "Pool Length", "Training Load", "Intensity",
    "Average Grade Adjusted Pace", "Timer Time", "Total Cycles", "Recovery", "With Pet",
    "Competition", "Long Run", "For a Cause", "With Kid", "Downhill Distance", "Total Sets",
    "Total Reps", "Media",
]  # fmt: skip

SIMPLE_HEADER = [
    "Activity Date",
    "Activity Name",
    "Activity Type",
    "Activity Description",
    "Distance",
    "Moving Time",
]

KM_PER_MILE = 1.609344


@dataclass(frozen=True)
class Run:
    days_ago: int
    km: float | None
    minutes: float | None
    avg: int | None = None
    name: str = "Morning Run"
    type: str = "Run"
    description: str | None = None
    metres_blank: bool = False


def run(days_ago, km, minutes, avg=None, name="Morning Run", type="Run", **extra) -> Run:  # noqa: A002
    return Run(days_ago, km, minutes, avg, name, type, **extra)


def _date_text(days_ago: int, reference: date) -> str:
    moment = datetime.combine(reference - timedelta(days=days_ago), datetime.min.time())
    moment = moment.replace(hour=7, minute=1, second=22)
    return moment.strftime("%b %d, %Y, %I:%M:%S %p").replace(" 0", " ", 1)


def _description(item: Run) -> str:
    if item.description is not None:
        return item.description
    return f"Avg {item.avg} bpm" if item.avg is not None else ""


def _number(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def make_csv(
    runs: list[Run],
    header: str = "strava",
    units: str = "km",
    reference: date = REFERENCE_DATE,
    drop_columns: tuple[str, ...] = (),
) -> str:
    """Return CSV text. header="strava" uses the real layout; "simple" uses one Distance column."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    names = STRAVA_HEADER if header == "strava" else SIMPLE_HEADER
    keep = [i for i, name in enumerate(names) if name not in drop_columns]
    writer.writerow([names[i] for i in keep])
    for number, item in enumerate(runs, start=1):
        seconds = None if item.minutes is None else item.minutes * 60
        if item.km is None:
            display = None
        elif units == "miles":
            display = item.km / KM_PER_MILE
        else:
            display = item.km
        values = {
            "Activity ID": str(1000 + number),
            "Activity Date": _date_text(item.days_ago, reference),
            "Activity Name": item.name,
            "Activity Type": item.type,
            "Activity Description": _description(item),
            "Moving Time": _number(seconds),
            "Elapsed Time": _number(seconds),
        }
        row = []
        distance_seen = 0
        for name in names:
            if name == "Distance":
                distance_seen += 1
                if header == "strava" and distance_seen == 2:
                    metres = None if item.km is None or item.metres_blank else item.km * 1000
                    row.append(_number(metres))
                else:
                    row.append(_number(display))
            else:
                row.append(values.get(name, ""))
        writer.writerow([row[i] for i in keep])
    return out.getvalue()


def typical_runs() -> list[Run]:
    """30 runs over 12 weeks: easy runs, 6 hard runs of 3 km or more, and weekly long runs."""
    runs: list[Run] = []
    for week in range(12):
        base = week * 7
        runs.append(run(base + 1, 8.0, 48.0, avg=145))
        runs.append(run(base + 4, 14.0 + (11 - week) % 3, 90.0, avg=148, name="Long Run"))
    hard = [
        run(3, 10.0, 46.0, avg=170, name="Tempo"),
        run(10, 5.0, 22.5, avg=172, name="5k effort"),
        run(17, 8.0, 37.0, avg=168, name="Threshold"),
        run(24, 6.0, 27.6, avg=171, name="Track Intervals"),
        run(31, 10.0, 47.0, avg=167, name="Tempo"),
        run(38, 4.0, 18.4, avg=175, name="Race pace"),
    ]
    return runs + hard
