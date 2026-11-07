"""Constitution V and R6/R9: uploads stay in memory, are never logged, and text is escaped."""

import logging
import re
import tempfile

import pytest

from strava_predictor import config
from tests.fixtures.builders import make_csv, run, typical_runs
from tests.integration.helpers import make_client, post

SECRET_NAME = "Secret Lake Loop"
SECRET_DESCRIPTION = "Avg 163 bpm near my house"


def _large_csv(target_bytes: int) -> str:
    runs = typical_runs() + [
        run(2, 6.0, 33.0, avg=163, name=SECRET_NAME, description=SECRET_DESCRIPTION)
    ]
    filler = [run(200 + i, 5.0, 30.0, avg=140) for i in range(400)]
    text = make_csv(runs + filler)
    header, _, body = text.partition("\n")
    rows = body.splitlines()
    filler_rows = rows[len(runs) :]
    lines = rows[: len(runs)]
    while sum(len(line) + 1 for line in lines) < target_bytes:
        lines.extend(filler_rows)
    return header + "\n" + "\n".join(lines) + "\n"


def test_oversized_upload_is_refused_and_values_kept():
    response = post(make_client(), b"x" * (config.MAX_UPLOAD_BYTES + 1), race_distance_km="21.1")
    assert response.status_code == 413
    assert "larger than 10 MB" in response.text
    assert re.search(r'name="race_distance_km"[^>]*value="21.1"', response.text)


def test_far_too_large_body_is_refused_unread():
    response = post(make_client(), b"x" * (config.MAX_UPLOAD_BYTES * 2))
    assert response.status_code == 413
    assert "larger than 10 MB" in response.text


def test_streamed_body_without_length_is_cut_off():
    chunk = b"x" * (1024 * 1024)

    def body():
        for _ in range(12):
            yield chunk

    response = make_client().post(
        "/results",
        content=body(),
        headers={"content-type": "multipart/form-data; boundary=zzz"},
    )
    assert response.status_code == 413


@pytest.fixture
def no_disk_writes(monkeypatch):
    """Fail if anything spools or creates a temporary file while a request is handled."""
    calls: list[str] = []

    def record(name):
        def fail(*args, **kwargs):
            calls.append(name)
            raise AssertionError(f"{name} was called while handling an upload")

        return fail

    monkeypatch.setattr(tempfile.SpooledTemporaryFile, "rollover", record("rollover"))
    for name in ("NamedTemporaryFile", "TemporaryFile", "mkstemp", "mkdtemp"):
        monkeypatch.setattr(tempfile, name, record(name))
    return calls


def test_upload_is_not_written_to_disk(no_disk_writes):
    client = make_client()
    text = _large_csv(3 * 1024 * 1024)
    assert len(text) > 3 * 1024 * 1024
    response = post(client, text)
    assert response.status_code == 200
    assert no_disk_writes == []


def test_upload_content_is_not_logged(caplog):
    text = _large_csv(1)
    with caplog.at_level(logging.DEBUG):
        response = post(make_client(), text)
    assert response.status_code == 200
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert SECRET_NAME not in logged
    assert "near my house" not in logged
    assert "163" not in logged


def test_activity_text_is_escaped(load_fixture):
    response = post(make_client(), load_fixture("xss.csv"))
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
