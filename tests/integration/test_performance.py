"""SC-002: regenerating with new inputs takes under 2 seconds for 5,000 activities."""

import time

from tests.fixtures.builders import make_csv, run
from tests.integration.helpers import make_client, post

ACTIVITIES = 5000
LIMIT_S = 2.0


def _big_csv() -> str:
    runs = []
    for index in range(ACTIVITIES):
        kind = "Ride" if index % 5 == 0 else "Run"
        avg = 170 if index % 7 == 0 else 145
        runs.append(run(index % 1500, 6.0 + index % 10, 33.0 + index % 30, avg=avg, type=kind))
    return make_csv(runs)


def test_regenerate_5000_activities_under_two_seconds():
    client = make_client()
    first = post(client, _big_csv())
    assert first.status_code == 200
    started = time.perf_counter()
    response = post(client, None, race_distance_km="42.195", weeks_to_race="52", days_per_week="7")
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < LIMIT_S, f"regeneration took {elapsed:.2f} s"


def test_first_upload_of_5000_activities_under_two_seconds():
    client = make_client()
    text = _big_csv()
    started = time.perf_counter()
    response = post(client, text)
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < LIMIT_S, f"upload took {elapsed:.2f} s"
