from datetime import date

from fastapi.testclient import TestClient

from strava_predictor.web.app import create_app

REFERENCE_DATE = date(2026, 11, 5)

VALID_FIELDS = {
    "race_distance_km": "10",
    "weeks_to_race": "12",
    "goal_pace": "4:50",
    "days_per_week": "4",
    "max_hr": "201",
}


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make_client(session_clock=None) -> TestClient:
    kwargs = {"clock": lambda: REFERENCE_DATE}
    if session_clock is not None:
        kwargs["session_clock"] = session_clock
    return TestClient(create_app(**kwargs))


def post(client: TestClient, csv_text: str | bytes | None = None, **overrides):
    fields = {**VALID_FIELDS, **overrides}
    files = None
    if csv_text is not None:
        body = csv_text.encode("utf-8") if isinstance(csv_text, str) else csv_text
        files = {"csv_file": ("activities.csv", body, "text/csv")}
    else:
        files = {"csv_file": ("", b"", "application/octet-stream")}
    return client.post("/results", data=fields, files=files)
