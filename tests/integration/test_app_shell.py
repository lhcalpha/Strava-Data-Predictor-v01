import re

from fastapi.testclient import TestClient

from strava_predictor.web.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_form_page_has_every_field():
    response = _client().get("/")
    assert response.status_code == 200
    html = response.text
    for field in (
        "csv_file",
        "race_distance_km",
        "weeks_to_race",
        "goal_pace",
        "days_per_week",
        "max_hr",
    ):
        assert f'name="{field}"' in html
    assert re.search(r'name="max_hr"[^>]*value="201"', html)


def test_every_response_has_strict_csp():
    client = _client()
    for path in ("/", "/static/style.css"):
        response = client.get(path)
        assert response.headers["content-security-policy"] == "default-src 'self'"


def test_stylesheet_is_served():
    response = _client().get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_no_external_urls():
    html = _client().get("/").text
    assert "http://" not in html
    assert "https://" not in html
