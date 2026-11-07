from datetime import date

import pytest

from strava_predictor.domain.models import DataError, DataErrorCode
from strava_predictor.domain.parsing import parse_activities
from tests.fixtures.builders import make_csv, run


def test_real_layout_reads_metre_column(load_fixture):
    activities = parse_activities(load_fixture("strava_header.csv"))
    assert [a.distance_km for a in activities] == [10.0, 5.0, 8.0, 12.0, 6.0]
    assert activities[0].moving_time_s == 2760.0
    assert activities[0].name == "Tempo"
    assert activities[0].activity_type == "Run"
    assert activities[0].date == date(2026, 11, 3)


def test_first_distance_used_when_metres_blank():
    text = make_csv([run(1, 7.5, 40.0, metres_blank=True), run(2, 5.0, 30.0)])
    activities = parse_activities(text)
    assert activities[0].distance_km == pytest.approx(7.5)


def test_miles_detected_from_ratio_and_converted():
    text = make_csv(
        [run(1, 10.0, 50.0, metres_blank=True), run(2, 5.0, 30.0), run(3, 8.0, 44.0)],
        units="miles",
    )
    activities = parse_activities(text)
    assert activities[0].distance_km == pytest.approx(10.0, abs=0.01)
    assert activities[1].distance_km == pytest.approx(5.0)


def test_imperial_fixture_matches_metres(load_fixture):
    km = [a.distance_km for a in parse_activities(load_fixture("imperial.csv"))]
    metric = [a.distance_km for a in parse_activities(load_fixture("typical_runner.csv"))]
    assert km == pytest.approx(metric)


def test_single_distance_column_is_km():
    activities = parse_activities(make_csv([run(1, 6.0, 33.0)], header="simple"))
    assert activities[0].distance_km == 6.0


def test_missing_required_column_names_it(load_fixture):
    with pytest.raises(DataError) as error:
        parse_activities(load_fixture("missing_columns.csv"))
    assert error.value.code == DataErrorCode.MISSING_COLUMNS
    assert error.value.details == ("Moving Time",)
    assert "Moving Time" in error.value.message


@pytest.mark.parametrize("text", ["", "   \n\n", "﻿"])
def test_empty_file(text):
    with pytest.raises(DataError) as error:
        parse_activities(text)
    assert error.value.code == DataErrorCode.EMPTY_FILE


def test_short_row_is_malformed(load_fixture):
    with pytest.raises(DataError) as error:
        parse_activities(load_fixture("malformed.csv"))
    assert error.value.code == DataErrorCode.MALFORMED_CSV


def test_unreadable_date_is_malformed():
    text = make_csv([run(1, 5.0, 30.0)]).replace("Nov 4, 2026, 07:01:22 AM", "yesterday")
    with pytest.raises(DataError) as error:
        parse_activities(text)
    assert error.value.code == DataErrorCode.MALFORMED_CSV


def test_bad_quoting_is_malformed():
    header = "Activity Date,Activity Name,Activity Type,Activity Description,Distance,Moving Time"
    with pytest.raises(DataError) as error:
        parse_activities(header + '\n"Nov 4, 2026",x"y,Run,,5,1800\n"unterminated')
    assert error.value.code == DataErrorCode.MALFORMED_CSV


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Nov 4, 2026, 7:01:22 AM", date(2026, 11, 4)),
        ("Nov 04, 2026, 07:01:22 PM", date(2026, 11, 4)),
        ("2026-11-04 07:01:22", date(2026, 11, 4)),
        ("2026-11-04T19:01:22", date(2026, 11, 4)),
        ("2026-11-04", date(2026, 11, 4)),
    ],
)
def test_date_formats(text, expected):
    header = "Activity Date,Activity Name,Activity Type,Activity Description,Distance,Moving Time"
    activities = parse_activities(f'{header}\n"{text}",Run,Run,,5,1800\n')
    assert activities[0].date == expected


def test_blank_and_zero_values_become_none():
    header = "Activity Date,Activity Name,Activity Type,Activity Description,Distance,Moving Time"
    rows = '"2026-11-04",a,Run,,,1800\n"2026-11-04",b,Run,,5,\n"2026-11-04",c,Run,,0,0\n'
    a, b, c = parse_activities(f"{header}\n{rows}")
    assert a.distance_km is None and a.moving_time_s == 1800.0
    assert b.moving_time_s is None
    assert c.distance_km is None and c.moving_time_s is None


def test_thousands_separator_and_text_numbers():
    header = "Activity Date,Activity Name,Activity Type,Activity Description,Distance,Moving Time"
    rows = '"2026-11-04",a,Run,,"5.0","1,800"\n"2026-11-04",b,Run,,abc,xyz\n'
    a, b = parse_activities(f"{header}\n{rows}")
    assert a.moving_time_s == 1800.0
    assert b.distance_km is None and b.moving_time_s is None


@pytest.mark.parametrize(
    ("name", "expected"),
    [("Track Intervals", True), ("6x400 REPEATS", True), ("Morning Run", False)],
)
def test_interval_flag(name, expected):
    activities = parse_activities(make_csv([run(1, 5.0, 25.0, name=name)]))
    assert activities[0].is_interval is expected


def test_byte_order_mark_is_ignored(load_fixture):
    activities = parse_activities("﻿" + load_fixture("strava_header.csv"))
    assert len(activities) == 5
