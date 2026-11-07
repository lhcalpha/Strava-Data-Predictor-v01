"""Read a Strava activities CSV (FR-010 to FR-012, research R2, R3, R5).

The real export repeats column names (two Distance columns: the athlete's display unit first,
metres second), so columns are found by position rather than with csv.DictReader.
"""

import csv
import io
import re
import statistics
from datetime import date, datetime

from strava_predictor import config
from strava_predictor.domain.models import Activity, DataError, DataErrorCode

_AVG_HR = re.compile(config.AVG_HR_PATTERN, re.IGNORECASE)
_BOM = "﻿"


def parse_avg_hr(description: str | None) -> int | None:
    """The number directly after "Avg" in a description, if it is a valid heart rate."""
    match = _AVG_HR.search(description or "")
    if match is None:
        return None
    value = int(match.group(1))
    return value if config.HR_VALID_MIN <= value <= config.HR_VALID_MAX else None


def _number(text: str) -> float | None:
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return value if value > 0 else None


def _date(text: str) -> date:
    cleaned = text.strip()
    for pattern in config.DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    raise DataError(
        DataErrorCode.MALFORMED_CSV,
        f'The file could not be read: "{cleaned}" is not a date this app understands.',
    )


def _is_interval(name: str) -> bool:
    lowered = name.lower()
    return any(word in lowered for word in config.INTERVAL_KEYWORDS)


def _column_positions(header: list[str]) -> dict[str, list[int]]:
    positions: dict[str, list[int]] = {}
    for index, name in enumerate(header):
        positions.setdefault(name.strip(), []).append(index)
    return positions


def _display_unit_metres(pairs: list[tuple[float, float]]) -> float:
    """Metres per unit of the first Distance column, from rows where both columns have values."""
    if not pairs:
        return config.METRES_PER_KM
    ratio = statistics.median(metres / display for display, metres in pairs)
    miles_gap = abs(ratio - config.METRES_PER_MILE) / config.METRES_PER_MILE
    return (
        config.METRES_PER_MILE
        if miles_gap <= config.MILES_RATIO_TOLERANCE
        else (config.METRES_PER_KM)
    )


def _rows(text: str) -> list[list[str]]:
    try:
        return [row for row in csv.reader(io.StringIO(text, newline=""), strict=True) if row]
    except csv.Error as error:
        raise DataError(
            DataErrorCode.MALFORMED_CSV, "The file could not be read as a CSV file."
        ) from error


def parse_activities(csv_text: str) -> list[Activity]:
    """Parse every activity in the export. Distances are km; times are seconds."""
    text = csv_text.removeprefix(_BOM)
    if not text.strip():
        raise DataError(DataErrorCode.EMPTY_FILE, "The file is empty.")

    rows = _rows(text)
    header, body = rows[0], rows[1:]
    positions = _column_positions(header)
    missing = tuple(name for name in config.REQUIRED_COLUMNS if name not in positions)
    if missing:
        raise DataError(
            DataErrorCode.MISSING_COLUMNS,
            "The file is missing required columns: " + ", ".join(missing) + ".",
            missing,
        )

    first = {name: positions[name][0] for name in config.REQUIRED_COLUMNS}
    distance_columns = positions["Distance"]
    display_index = distance_columns[0]
    metres_index = distance_columns[1] if len(distance_columns) > 1 else None
    needed = max([*first.values(), *distance_columns])

    raw = []
    for row in body:
        if len(row) <= needed:
            raise DataError(
                DataErrorCode.MALFORMED_CSV,
                "The file could not be read: a row has fewer columns than the header.",
            )
        display = _number(row[display_index])
        metres = _number(row[metres_index]) if metres_index is not None else None
        raw.append((row, display, metres))

    pairs = [(display, metres) for _, display, metres in raw if display and metres]
    metres_per_unit = (
        _display_unit_metres(pairs) if metres_index is not None else (config.METRES_PER_KM)
    )

    activities = []
    for row, display, metres in raw:
        if metres is not None:
            distance_km = metres / config.METRES_PER_KM
        elif display is not None:
            distance_km = display * metres_per_unit / config.METRES_PER_KM
        else:
            distance_km = None
        name = row[first["Activity Name"]]
        description = row[first["Activity Description"]]
        activities.append(
            Activity(
                date=_date(row[first["Activity Date"]]),
                name=name,
                activity_type=row[first["Activity Type"]].strip(),
                description=description,
                distance_km=distance_km,
                moving_time_s=_number(row[first["Moving Time"]]),
                avg_hr=parse_avg_hr(description),
                is_interval=_is_interval(name),
            )
        )
    return activities
