import re

from strava_predictor import config
from tests.integration.helpers import FakeClock, make_client, post

UPLOAD_AGAIN = "Please upload your CSV again"


def _cookie_header(response) -> str:
    return response.headers.get("set-cookie", "")


def test_first_upload_sets_a_safe_cookie(load_fixture):
    response = post(make_client(), load_fixture("typical_runner.csv"))
    header = _cookie_header(response).lower()
    assert header.startswith("session=")
    assert "httponly" in header
    assert "samesite=strict" in header
    assert "path=/" in header


def test_regenerate_without_upload(load_fixture):
    client = make_client()
    post(client, load_fixture("typical_runner.csv"))
    response = post(client, None, race_distance_km="21.1", weeks_to_race="16")
    assert response.status_code == 200
    assert 'id="results"' in response.text
    assert "21.1 km race in 16 weeks" in response.text
    assert response.text.count('class="week"') == 16


def test_form_says_a_file_is_loaded(load_fixture):
    client = make_client()
    post(client, load_fixture("typical_runner.csv"))
    assert "a file is already loaded" in client.get("/").text


def test_expired_session_asks_for_the_file_again(load_fixture):
    clock = FakeClock()
    client = make_client(session_clock=clock)
    post(client, load_fixture("typical_runner.csv"))
    clock.now += config.SESSION_TTL_S + 1
    response = post(client, None, weeks_to_race="20")
    assert response.status_code == 400
    assert UPLOAD_AGAIN in response.text
    assert re.search(r'name="weeks_to_race"[^>]*value="20"', response.text)


def test_unknown_cookie_asks_for_the_file_again():
    client = make_client()
    client.cookies.set("session", "made-up-token")
    response = post(client, None)
    assert response.status_code == 400
    assert UPLOAD_AGAIN in response.text


def test_invalid_field_keeps_the_session(load_fixture):
    client = make_client()
    post(client, load_fixture("typical_runner.csv"))
    bad = post(client, None, days_per_week="9")
    assert bad.status_code == 400
    assert 'id="days_per_week-error"' in bad.text
    assert "a file is already loaded" in bad.text
    good = post(client, None)
    assert good.status_code == 200


def test_new_file_replaces_stored_runs(load_fixture):
    client = make_client()
    post(client, load_fixture("typical_runner.csv"))
    post(client, load_fixture("no_hard_runs.csv"))
    response = post(client, None)
    assert "no hard runs" in response.text


def test_data_error_does_not_replace_stored_runs(load_fixture):
    client = make_client()
    post(client, load_fixture("typical_runner.csv"))
    post(client, load_fixture("missing_columns.csv"))
    response = post(client, None)
    assert response.status_code == 200
